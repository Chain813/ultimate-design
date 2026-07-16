"""AIGC 设计推演 —— 图生图渲染中心。

AI 润色提示词 → 空间约束锁定 → 深度图精确尺度 → SD 渲染。
集成 DesignContext 设计纲要，支持批量渲染与结果管理。
"""

import io
import json
import math
import time
from pathlib import Path

import streamlit as st
from PIL import Image as PILImage
from PIL import ImageDraw

from src.ui.app_shell import render_top_nav
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.streamlit_compat import stretch_width
from src.workflow.stage_keys import SK

st.set_page_config(page_title="AIGC 设计推演", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="AIGC 设计推演",
    description="AI 润色提示词，ControlNet 锁定路网与建筑轮廓，深度图定义精确空间尺度。支持设计纲要自动注入。",
    eyebrow="AIGC Studio",
    tags=["AI 润色", "ControlNet", "深度图", "设计纲要"],
)

ROOT = Path(__file__).resolve().parent.parent


# ══════════════════════════════════════════
# 设计策略 → AIGC 渲染风格映射
# ══════════════════════════════════════════

STRATEGY_STYLES = {
    "历史保护修缮": {
        "keywords": ["heritage preservation", "historical restoration", "traditional architecture",
                     "Chinese traditional roof", "gray brick walls", "red wooden doors",
                     "ancient palace nearby", "cultural heritage zone"],
        "materials": "gray brick, carved wooden beams, traditional tiles, stone foundations, red lacquer",
        "lighting": "warm golden hour light, soft shadows, nostalgic atmosphere",
        "colors": "warm earth tones, gray, dark red, ochre, amber",
        "vegetation": "old scholar trees, traditional garden plants, wisteria, bamboo",
        "atmosphere": "quiet, dignified, historical resonance, preserved cultural memory",
        "negative_extra": "modern glass, steel structure, neon lights, demolition, construction debris",
        "denoising_boost": -0.1,  # 降低重绘强度，保留更多原始特征
        "cn_weight_boost": 0.2,   # 提高 ControlNet 权重，严格遵循空间约束
    },
    "微更新修补": {
        "keywords": ["micro-renewal", "community renovation", "street-level improvement",
                     "pocket park", "community garden", "elderly-friendly design",
                     "children's playground", "neighborhood vitality"],
        "materials": "exposed brick, wooden benches, permeable pavement, green walls, mosaic tiles",
        "lighting": "natural daylight, warm community glow, evening lanterns",
        "colors": "warm greens, soft yellows, terracotta, natural wood tones",
        "vegetation": "community gardens, fruit trees, flowering shrubs, vertical greenery",
        "atmosphere": "cozy, lived-in, community gathering, intergenerational activities",
        "negative_extra": "high-rise, luxury, commercial mega-structure, cold industrial",
        "denoising_boost": 0.0,
        "cn_weight_boost": 0.0,
    },
    "功能置换活化": {
        "keywords": ["adaptive reuse", "industrial heritage conversion", "creative industry park",
                     "loft office", "art gallery in old factory", "youth innovation hub",
                     "industrial-chic design", "exposed steel beams"],
        "materials": "corten steel, exposed concrete, glass curtain wall, reclaimed wood, industrial pipes",
        "lighting": "dramatic industrial lighting, large skylights, evening ambient glow",
        "colors": "industrial gray, rust orange, accent blue, raw concrete, matte black",
        "vegetation": "rooftop gardens, industrial courtyard planting, wild grass meadows",
        "atmosphere": "creative energy, industrial revival, youth culture, innovation",
        "negative_extra": "traditional residential, suburban house, farmland, rural",
        "denoising_boost": 0.1,   # 提高重绘强度，允许更多创意变化
        "cn_weight_boost": -0.1,  # 降低 ControlNet 权重，允许更大创意空间
    },
    "TOD 站城一体": {
        "keywords": ["transit-oriented development", "station-area renewal", "high-density mixed-use",
                     "underground metro entrance", "pedestrian skywalk", "urban core vitality",
                     "vertical city", "compact urban form"],
        "materials": "glass curtain wall, aluminum panels, polished stone, steel structure, LED lighting",
        "lighting": "modern urban lighting, metro station glow, evening commercial neon, dawn skyline",
        "colors": "silver, glass blue, white, accent red, modern gray",
        "vegetation": "linear parks along transit corridors, rooftop greenery, street trees in planters",
        "atmosphere": "bustling, efficient, modern metropolitan, 24-hour活力",
        "negative_extra": "rural landscape, low-density sprawl, farmland, isolated buildings",
        "denoising_boost": 0.15,
        "cn_weight_boost": 0.0,
    },
    "生态绿廊修复": {
        "keywords": ["ecological corridor", "riparian restoration", "sponge city", "biodiversity habitat",
                     "wetland park", "green infrastructure", "waterfront promenade",
                     "native plant restoration", "bird-friendly design"],
        "materials": "natural stone, timber boardwalk, permeable paving, gabion walls, living walls",
        "lighting": "natural daylight filtering through canopy, dappled light, misty morning riverside",
        "colors": "lush greens, water blue, natural wood brown, wildflower colors, earth tones",
        "vegetation": "native trees, riparian plants, wildflower meadows, wetland reeds, willow trees",
        "atmosphere": "peaceful, natural, ecological recovery, human-nature harmony",
        "negative_extra": "concrete channel, industrial waterfront, pollution, hardscape only",
        "denoising_boost": 0.05,
        "cn_weight_boost": 0.1,
    },
    "历史街区文创": {
        "keywords": ["cultural creative district", "heritage-themed commercial street",
                     "traditional craft workshops", "cultural tourism destination",
                     "night economy", "intangible heritage display"],
        "materials": "traditional brick with modern glass inserts, wooden lattice screens, stone paving",
        "lighting": "festive lanterns, warm shopfront glow, evening cultural atmosphere",
        "colors": "traditional red and gold accents, warm white walls, natural wood, ink black",
        "vegetation": "bonsai displays, traditional courtyard plants, seasonal flower arrangements",
        "atmosphere": "cultural celebration, artisanal craftsmanship, living heritage, tourism vitality",
        "negative_extra": "purely residential, industrial, cold modernist, no cultural elements",
        "denoising_boost": 0.05,
        "cn_weight_boost": 0.05,
    },
}


def _detect_strategy_from_context(ctx) -> list[str]:
    """从 DesignContext 自动检测适用的设计策略类型。"""
    detected = []
    # 合并所有文本进行关键词匹配
    all_text = " ".join([
        str(ctx.strategy_matrix or ""),
        str(ctx.design_concept or ""),
        str(ctx.design_brief or ""),
        str(ctx.spatial_structure or ""),
        str(ctx.building_form or ""),
        str(ctx.landscape_style or ""),
    ]).lower()

    keyword_map = {
        "历史保护修缮": ["保护", "修缮", "历史", "文物", "遗产", "紫线", "风貌", "heritage", "preservation", "restoration"],
        "微更新修补": ["微更新", "社区", "修补", "口袋公园", "邻里", "适老化", "micro-renewal", "community"],
        "功能置换活化": ["功能置换", "工业遗存", "活化", "文创", "产业园", "adaptive reuse", "industrial", "creative"],
        "TOD 站城一体": ["TOD", "站城", "轨道交通", "地铁", "高强度", "transit", "station", "metro"],
        "生态绿廊修复": ["生态", "绿廊", "海绵", "滨水", "伊通河", "廊道", "ecological", "corridor", "riparian"],
        "历史街区文创": ["文创", "旅游", "非遗", "商业街", "夜经济", "cultural", "tourism", "craft"],
    }

    for style_name, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw in all_text)
        if score >= 2:
            detected.append(style_name)

    # 如果没有检测到任何策略，默认使用微更新
    if not detected:
        detected.append("微更新修补")

    return detected


def _build_style_prompt(styles: list[str]) -> str:
    """根据选中的策略风格生成提示词补充文本。"""
    if not styles:
        return ""
    parts = []
    for style_name in styles:
        style = STRATEGY_STYLES.get(style_name, {})
        if style:
            parts.append(f"[{style_name}]")
            parts.append(f"Style keywords: {', '.join(style.get('keywords', [])[:5])}")
            parts.append(f"Materials: {style.get('materials', '')}")
            parts.append(f"Lighting: {style.get('lighting', '')}")
            parts.append(f"Colors: {style.get('colors', '')}")
            parts.append(f"Atmosphere: {style.get('atmosphere', '')}")
    return "\n".join(parts)


def _get_style_params(styles: list[str]) -> dict:
    """聚合多个策略的渲染参数（取平均或最大值）。"""
    if not styles:
        return {"denoising_boost": 0, "cn_weight_boost": 0, "negative_extra": ""}
    denoising_boosts = []
    cn_weight_boosts = []
    negative_extras = []
    for style_name in styles:
        style = STRATEGY_STYLES.get(style_name, {})
        denoising_boosts.append(style.get("denoising_boost", 0))
        cn_weight_boosts.append(style.get("cn_weight_boost", 0))
        negative_extras.append(style.get("negative_extra", ""))
    return {
        "denoising_boost": sum(denoising_boosts) / len(denoising_boosts),
        "cn_weight_boost": sum(cn_weight_boosts) / len(cn_weight_boosts),
        "negative_extra": ", ".join(filter(None, negative_extras)),
    }

# 道路等级对应的现实宽度 (米)
ROAD_WIDTH_METERS = {1: 30, 2: 20, 3: 12, 4: 6}

# 建筑高度等级对应的深度值
BUILDING_DEPTH = {"low": 80, "mid": 160, "high": 220}

# 分辨率预设（含低配模式）
RESOLUTION_PRESETS = {
    "⚡ 低配 512×384": (512, 384),
    "⚡ 低配 512×512": (512, 512),
    "标准 1024×768 (4:3)": (1024, 768),
    "标准 1280×720 (16:9)": (1280, 720),
    "标准 768×1024 (3:4 竖版)": (768, 1024),
    "标准 1024×1024 (1:1)": (1024, 1024),
    "高清 1536×864 (16:9)": (1536, 864),
}

# ControlNet 预处理器选项
CONTROLNET_MODULES = {
    "canny (边缘检测)": "canny",
    "lineart_realistic (写实线稿)": "lineart_realistic",
    "lineart_anime (动漫线稿)": "lineart_anime",
    "scribble_xdog (涂鸦)": "scribble_xdog",
    "depth (深度)": "depth",
    "seg (语义分割)": "seg",
}

# SD 模型缓存
@st.cache_data(ttl=300)
def _fetch_sd_models():
    """从 SD WebUI 获取可用模型列表。"""
    try:
        import requests
        resp = requests.get("http://127.0.0.1:7860/sdapi/v1/sd-models", timeout=3)
        if resp.status_code == 200:
            models = resp.json()
            return [m.get("model_name", m.get("title", "unknown")) for m in models]
    except Exception:
        pass
    return []


# ══════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def render_geojson_to_image(geojson_path: str, width: int = 1024, height: int = 768,
                            line_color: int = 255, line_width: int = 2,
                            lng_range: tuple | None = None, lat_range: tuple | None = None,
                            enhance: bool = True) -> "PILImage.Image":
    """将 GeoJSON 渲染为高质量黑白线稿图，用于 ControlNet 输入。

    enhance=True 时启用增强：多层线条叠加、高斯模糊抗锯齿、对比度增强。
    """
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    features = data.get("features", [])
    if not features:
        return PILImage.new("RGB", (width, height), (0, 0, 0))
    all_lngs, all_lats = [], []
    for feat in features:
        _collect_coords(feat["geometry"], all_lngs, all_lats)
    if not all_lngs:
        return PILImage.new("RGB", (width, height), (0, 0, 0))
    lng_min, lng_max = lng_range if lng_range else (min(all_lngs), max(all_lngs))
    lat_min, lat_max = lat_range if lat_range else (min(all_lats), max(all_lats))
    lng_pad = (lng_max - lng_min) * 0.02
    lat_pad = (lat_max - lat_min) * 0.02
    lng_min -= lng_pad; lng_max += lng_pad
    lat_min -= lat_pad; lat_max += lat_pad
    img = PILImage.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    def to_pixel(lng, lat):
        x = (lng - lng_min) / (lng_max - lng_min) * width
        y = (1 - (lat - lat_min) / (lat_max - lat_min)) * height
        return (x, y)
    # 多层渲染：粗线条 + 细线条，提升 ControlNet 感知
    for feat in features:
        _draw_geometry(draw, feat["geometry"], to_pixel, line_color, max(3, line_width + 1))
    for feat in features:
        _draw_geometry(draw, feat["geometry"], to_pixel, max(180, line_color - 40), line_width)
    if enhance:
        from PIL import ImageFilter
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        # 增强对比度
        from PIL import ImageEnhance
        img = ImageEnhance.Contrast(img).enhance(1.3)
    return img


@st.cache_data(ttl=3600, max_entries=20)
def render_depth_map(road_path: str, building_path: str,
                     width: int = 1024, height: int = 768,
                     lng_range: tuple | None = None, lat_range: tuple | None = None,
                     mode: str = "plan") -> "PILImage.Image":
    """渲染深度图。"""
    all_lngs, all_lats = [], []
    for p in [road_path, building_path]:
        if Path(p).exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            for feat in data.get("features", []):
                _collect_coords(feat["geometry"], all_lngs, all_lats)
    if not all_lngs:
        return PILImage.new("RGB", (width, height), (0, 0, 0))
    lng_min, lng_max = lng_range if lng_range else (min(all_lngs), max(all_lngs))
    lat_min, lat_max = lat_range if lat_range else (min(all_lats), max(all_lats))
    lng_pad = (lng_max - lng_min) * 0.02
    lat_pad = (lat_max - lat_min) * 0.02
    lng_min -= lng_pad; lng_max += lng_pad
    lat_min -= lat_pad; lat_max += lat_pad

    center_lat = (lat_min + lat_max) / 2
    meters_per_deg_lng = 111320 * math.cos(math.radians(center_lat))
    meters_per_deg_lat = 110540
    lng_range_m = (lng_max - lng_min) * meters_per_deg_lng
    lat_range_m = (lat_max - lat_min) * meters_per_deg_lat
    pixels_per_meter_x = width / lng_range_m

    img = PILImage.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)

    def to_pixel(lng, lat):
        x = (lng - lng_min) / (lng_max - lng_min) * width
        y = (1 - (lat - lat_min) / (lat_max - lat_min)) * height
        return (x, y)

    if mode == "perspective":
        for row in range(height):
            gray = int(200 - (row / height) * 170)
            draw.line([(0, row), (width, row)], fill=gray)

    if Path(road_path).exists():
        with open(road_path, "r", encoding="utf-8") as f:
            road_data = json.load(f)
        for feat in road_data.get("features", []):
            level = feat.get("properties", {}).get("level", 4)
            road_width_m = ROAD_WIDTH_METERS.get(level, 6)
            px_width = max(1, int(road_width_m * pixels_per_meter_x))
            if mode == "plan":
                gray = {1: 200, 2: 150, 3: 100, 4: 60}.get(level, 60)
            else:
                gray = {1: 230, 2: 190, 3: 150, 4: 110}.get(level, 110)
            _draw_geometry(draw, feat["geometry"], to_pixel, gray, px_width)

    if Path(building_path).exists():
        with open(building_path, "r", encoding="utf-8") as f:
            bldg_data = json.load(f)
        for feat in bldg_data.get("features", []):
            props = feat.get("properties", {})
            floor = props.get("Floor") or props.get("floor") or props.get("levels") or 0
            try:
                floor = int(float(floor))
            except (ValueError, TypeError):
                floor = 0
            height_m = floor * 3.5
            if height_m <= 12:
                depth_val = BUILDING_DEPTH["low"]
            elif height_m <= 24:
                depth_val = BUILDING_DEPTH["mid"]
            else:
                depth_val = BUILDING_DEPTH["high"]
            if mode == "perspective":
                depth_val = min(255, depth_val + 40)
            _draw_geometry(draw, feat["geometry"], to_pixel, depth_val, 3)

    return img


@st.cache_data(ttl=3600, max_entries=20)
def render_landuse_overlay(landuse_path: str, width: int = 1024, height: int = 768,
                           lng_range: tuple | None = None, lat_range: tuple | None = None) -> "PILImage.Image":
    """渲染用地类型色块叠加图，用于 ControlNet 语义约束。"""
    if not Path(landuse_path).exists():
        return PILImage.new("RGB", (width, height), (0, 0, 0))
    with open(landuse_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    features = data.get("features", [])
    if not features:
        return PILImage.new("RGB", (width, height), (0, 0, 0))
    all_lngs, all_lats = [], []
    for feat in features:
        _collect_coords(feat["geometry"], all_lngs, all_lats)
    if not all_lngs:
        return PILImage.new("RGB", (width, height), (0, 0, 0))
    lng_min, lng_max = lng_range if lng_range else (min(all_lngs), max(all_lngs))
    lat_min, lat_max = lat_range if lat_range else (min(all_lats), max(all_lats))
    lng_pad = (lng_max - lng_min) * 0.02
    lat_pad = (lat_max - lat_min) * 0.02
    lng_min -= lng_pad; lng_max += lng_pad
    lat_min -= lat_pad; lat_max += lat_pad
    img = PILImage.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    def to_pixel(lng, lat):
        x = (lng - lng_min) / (lng_max - lng_min) * width
        y = (1 - (lat - lat_min) / (lat_max - lat_min)) * height
        return (x, y)
    # 用地类型→颜色映射 (灰度值用于 ControlNet)
    landuse_colors = {
        "居住": (80, 80, 80),
        "商业": (160, 120, 60),
        "工业": (100, 100, 100),
        "绿地": (40, 120, 40),
        "道路": (180, 180, 180),
        "公共设施": (60, 60, 160),
        "水域": (40, 40, 120),
    }
    for feat in features:
        props = feat.get("properties", {})
        land_type = props.get("land_type", props.get("LandUse", ""))
        color = landuse_colors.get(land_type, (60, 60, 60))
        _draw_geometry_filled(draw, feat["geometry"], to_pixel, color)
    return img


def _collect_coords(geometry, lngs, lats):
    """递归收集坐标。"""
    coords = geometry.get("coordinates", [])
    gtype = geometry.get("type", "")
    if gtype == "Point":
        if len(coords) >= 2:
            lngs.append(coords[0]); lats.append(coords[1])
    elif gtype in ("LineString", "MultiPoint"):
        for c in coords:
            if len(c) >= 2:
                lngs.append(c[0]); lats.append(c[1])
    elif gtype in ("Polygon", "MultiLineString"):
        for ring in coords:
            for c in ring:
                if len(c) >= 2:
                    lngs.append(c[0]); lats.append(c[1])
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                for c in ring:
                    if len(c) >= 2:
                        lngs.append(c[0]); lats.append(c[1])
    elif gtype == "GeometryCollection":
        for g in geometry.get("geometries", []):
            _collect_coords(g, lngs, lats)


def _draw_geometry(draw, geometry, to_pixel, color, width):
    """递归绘制几何图形（线条）。"""
    coords = geometry.get("coordinates", [])
    gtype = geometry.get("type", "")
    if gtype == "LineString":
        points = [to_pixel(c[0], c[1]) for c in coords if len(c) >= 2]
        if len(points) >= 2:
            draw.line(points, fill=color, width=width)
    elif gtype == "MultiLineString":
        for line in coords:
            points = [to_pixel(c[0], c[1]) for c in line if len(c) >= 2]
            if len(points) >= 2:
                draw.line(points, fill=color, width=width)
    elif gtype == "Polygon":
        for ring in coords:
            points = [to_pixel(c[0], c[1]) for c in ring if len(c) >= 2]
            if len(points) >= 2:
                draw.line([*points, points[0]], fill=color, width=width)
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                points = [to_pixel(c[0], c[1]) for c in ring if len(c) >= 2]
                if len(points) >= 2:
                    draw.line([*points, points[0]], fill=color, width=width)
    elif gtype == "GeometryCollection":
        for g in geometry.get("geometries", []):
            _draw_geometry(draw, g, to_pixel, color, width)


def _draw_geometry_filled(draw, geometry, to_pixel, color):
    """递归绘制几何图形（填充）。"""
    coords = geometry.get("coordinates", [])
    gtype = geometry.get("type", "")
    if gtype == "Polygon":
        for ring in coords:
            points = [to_pixel(c[0], c[1]) for c in ring if len(c) >= 2]
            if len(points) >= 3:
                draw.polygon(points, fill=color)
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                points = [to_pixel(c[0], c[1]) for c in ring if len(c) >= 2]
                if len(points) >= 3:
                    draw.polygon(points, fill=color)
    elif gtype == "GeometryCollection":
        for g in geometry.get("geometries", []):
            _draw_geometry_filled(draw, g, to_pixel, color)


def _get_boundary_range():
    """从 Boundary_Scope.geojson 计算统一坐标范围。"""
    boundary_path = ROOT / "data/gis/Boundary_Scope.geojson"
    if boundary_path.exists():
        with open(boundary_path, "r", encoding="utf-8") as f:
            bdata = json.load(f)
        blng, blat = [], []
        for feat in bdata.get("features", []):
            _collect_coords(feat["geometry"], blng, blat)
        if blng:
            return (min(blng), max(blng)), (min(blat), max(blat))
    return None, None


def _build_design_context_prompt():
    """从 DesignContext 构建场景描述的补充上下文。"""
    try:
        from src.workflow.design_context import build_design_context
        ctx = build_design_context()
        parts = []
        if ctx.design_brief:
            parts.append(f"设计纲要：{ctx.design_brief[:800]}")
        elif ctx.spatial_structure:
            parts.append(f"空间结构：{ctx.spatial_structure[:400]}")
        if ctx.design_concept:
            parts.append(f"设计概念：{ctx.design_concept[:300]}")
        if ctx.strategy_matrix:
            parts.append(f"设计策略：{ctx.strategy_matrix[:300]}")
        if ctx.top_plot:
            parts.append(f"重点地块：{ctx.top_plot}")
        if ctx.building_form:
            parts.append(f"建筑形态：{ctx.building_form[:200]}")
        if ctx.landscape_style:
            parts.append(f"风貌要求：{ctx.landscape_style[:200]}")
        return "\n".join(parts) if parts else ""
    except Exception:
        return ""


def _build_auto_scene_description():
    """根据 DesignContext 自动生成高质量场景描述。"""
    try:
        from src.workflow.design_context import build_design_context
        ctx = build_design_context()
        parts = ["城市更新后的街区场景："]
        if ctx.spatial_structure:
            # 提取空间结构中的关键描述
            ss = ctx.spatial_structure[:300]
            parts.append(f"空间结构：{ss}")
        if ctx.building_form:
            parts.append(f"建筑风貌：{ctx.building_form[:200]}")
        if ctx.landscape_style:
            parts.append(f"景观特征：{ctx.landscape_style[:200]}")
        if ctx.public_space:
            parts.append(f"公共空间：{ctx.public_space[:200]}")
        if ctx.top_plot:
            parts.append(f"重点展示区域：{ctx.top_plot}")
        # 通用质量要求
        parts.append("画面要求：高质量建筑效果图，保留历史建筑特征，增加绿化和公共空间，人行道宽敞，有行道树和座椅，天空晴朗，光线自然。")
        return "\n".join(parts)
    except Exception:
        return ""


# ══════════════════════════════════════════
# 侧边栏：SD 参数配置
# ══════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ SD 渲染参数")
    render_mode = st.selectbox(
        "渲染模式",
        ["img2img (图生图)", "txt2img (纯文生图)", "inpainting (局部重绘)"],
        key="aigc_mode",
    )

    # 模型选择
    st.markdown("### 🧠 SD 模型")
    sd_models = _fetch_sd_models()
    if sd_models:
        sd_model = st.selectbox("选择模型", sd_models, key="aigc_sd_model")
    else:
        sd_model = st.text_input("模型名称 (SD WebUI 未连接)", value="", key="aigc_sd_model_manual")
        st.caption("启动 SD WebUI 后可自动获取模型列表")

    st.markdown("---")

    # 硬件模式
    hw_mode = st.radio("硬件模式", ["⚡ 低配模式", "🎮 标准模式", "🚀 高清模式"], index=1, key="aigc_hw_mode")
    if hw_mode.startswith("⚡"):
        default_res, default_steps, default_cfg = "⚡ 低配 512×384", 12, 5.0
    elif hw_mode.startswith("🚀"):
        default_res, default_steps, default_cfg = "高清 1536×864 (16:9)", 30, 8.0
    else:
        default_res, default_steps, default_cfg = "标准 1024×768 (4:3)", 20, 7.0

    st.markdown("### 🎛️ 渲染参数")
    res_label = st.selectbox("输出分辨率", list(RESOLUTION_PRESETS.keys()),
                             index=list(RESOLUTION_PRESETS.keys()).index(default_res) if default_res in RESOLUTION_PRESETS else 2,
                             key="aigc_resolution")
    output_w, output_h = RESOLUTION_PRESETS[res_label]
    denoising = st.slider("重绘强度", 0.1, 1.0, 0.55, 0.05, key="aigc_denoising")
    steps = st.slider("采样步数", 5, 50, default_steps, 1, key="aigc_steps")
    cfg_scale = st.slider("CFG Scale", 1.0, 15.0, default_cfg, 0.5, key="aigc_cfg")
    sampler = st.selectbox("采样器", ["DPM++ 2M Karras", "Euler a", "DPM++ SDE Karras", "DDIM", "UniPC"], key="aigc_sampler")
    seed = st.number_input("种子 (-1=随机)", value=-1, min_value=-1, key="aigc_seed")

    # ControlNet 预处理器选择
    st.markdown("---")
    st.markdown("### 🔧 ControlNet 预处理器")
    cn_module_label = st.selectbox("空间约束预处理器", list(CONTROLNET_MODULES.keys()), key="aigc_cn_module")
    cn_module = CONTROLNET_MODULES[cn_module_label]
    cn_depth_module = st.selectbox("深度图预处理器", ["depth (深度)", "lineart_realistic (写实线稿)"], key="aigc_cn_depth_module")
    cn_depth_module_val = CONTROLNET_MODULES.get(cn_depth_module.split(" ")[0], "depth")

# 统一坐标范围（始终计算，确保所有约束图对齐）
preview_lng, preview_lat = _get_boundary_range()

# ══════════════════════════════════════════
# 主区域
# ══════════════════════════════════════════

# ---- 1. 空间约束 ----
render_section_intro(
    "空间约束 (ControlNet)",
    "自动加载路网、建筑轮廓、研究边界、用地类型，渲染时自动注入 ControlNet 锁定不变。",
    eyebrow="Spatial Lock",
)

SPATIAL_DATA = {
    "boundary": {"path": ROOT / "data/gis/Boundary_Scope.geojson", "label": "🔲 研究边界", "default_weight": 1.0},
    "roads": {"path": ROOT / "static/road_clipped.geojson", "label": "🛣️ 道路网络", "default_weight": 0.9},
    "buildings": {"path": ROOT / "static/buildings.geojson", "label": "🏢 建筑轮廓", "default_weight": 0.8},
    "plots": {"path": ROOT / "data/gis/Key_Plots_District.json", "label": "✴️ 重点地块", "default_weight": 1.0},
    "landuse": {"path": ROOT / "data/gis/landuse_clipped.geojson", "label": "🗺️ 用地类型", "default_weight": 0.6},
}
# ControlNet 模型映射：根据预处理器自动选择对应模型
CN_MODEL_MAP = {
    "canny": "control_v11p_sd15_canny",
    "lineart_realistic": "control_v11p_sd15_lineart",
    "lineart_anime": "control_v11p_sd15s2_lineart_anime",
    "scribble_xdog": "control_v11p_sd15_scribble",
    "depth": "control_v11f1p_sd15_depth",
    "seg": "control_v11p_sd15_seg",
}
available_constraints = {k: v for k, v in SPATIAL_DATA.items() if v["path"].exists()}

col_checks = st.columns(min(5, len(available_constraints)) if available_constraints else 1)
cn_enabled_keys = []
for i, (key, info) in enumerate(available_constraints.items()):
    with col_checks[i % len(col_checks)]:
        default_on = key in ("boundary", "buildings")
        if st.checkbox(info["label"], value=default_on, key=f"cn_{key}"):
            cn_enabled_keys.append(key)

if cn_enabled_keys:
    weight_cols = st.columns(len(cn_enabled_keys))
    cn_weights = {}
    for i, key in enumerate(cn_enabled_keys):
        info = available_constraints[key]
        with weight_cols[i]:
            cn_weights[key] = st.slider(info["label"].split(" ")[-1], 0.0, 2.0, info["default_weight"], 0.1, key=f"cn_w_{key}")

# 深度图
st.markdown("---")
render_section_intro(
    "深度图 (Depth)",
    "根据图纸类型自动适配：平面类用空间尺度约束，透视类用远近深度关系。",
    eyebrow="Depth Map",
)

col_depth1, col_depth2, col_depth3 = st.columns(3)
with col_depth1:
    enable_depth = st.checkbox("启用深度图约束", value=True, key="aigc_depth_on")
    depth_weight = st.slider("深度图权重", 0.0, 2.0, 0.8, 0.1, key="aigc_depth_weight", disabled=not enable_depth)
with col_depth2:
    depth_mode = st.radio(
        "图纸类型",
        ["平面类 (总平面/分析图)", "透视类 (街道/鸟瞰)"],
        key="aigc_depth_mode",
        disabled=not enable_depth,
    )
with col_depth3:
    if depth_mode.startswith("平面"):
        st.markdown("**空间尺度约束**")
        st.caption("道路宽度按等级换算为米数")
        st.caption("建筑高度按楼层数换算")
        for level, meters in ROAD_WIDTH_METERS.items():
            label = {1: "主干道", 2: "次干道", 3: "支路", 4: "其他"}[level]
            st.caption(f"  L{level} {label}: {meters}m")
    else:
        st.markdown("**远近深度关系**")
        st.caption("前景 (近) = 亮，背景 (远) = 暗")
        st.caption("基于道路等级和建筑高度生成")

# 预览
with st.expander("预览约束图与深度图", expanded=False):
    show_previews = st.checkbox("🔍 显示实时渲染的控制特征图与深度图", value=False, key="aigc_show_previews")
    if show_previews:
        total_cols = len(cn_enabled_keys) + (1 if enable_depth else 0)
        preview_cols = st.columns(min(3, max(1, total_cols)))
        cn_images = {}
        for i, key in enumerate(cn_enabled_keys[:3]):
            info = available_constraints[key]
            with preview_cols[i % len(preview_cols)]:
                if key == "landuse":
                    img = render_landuse_overlay(str(info["path"]), width=512, height=384,
                                                 lng_range=preview_lng, lat_range=preview_lat)
                else:
                    img = render_geojson_to_image(str(info["path"]), width=512, height=384,
                                                  lng_range=preview_lng, lat_range=preview_lat)
                cn_images[key] = img
                st.image(img, caption=info["label"], width=256)

        if enable_depth:
            road_path = str(ROOT / "static/road_clipped.geojson")
            bldg_path = str(ROOT / "static/buildings.geojson")
            d_mode = "plan" if depth_mode.startswith("平面") else "perspective"
            with preview_cols[(len(cn_enabled_keys)) % len(preview_cols)]:
                depth_img = render_depth_map(road_path, bldg_path, width=512, height=384,
                                             lng_range=preview_lng, lat_range=preview_lat, mode=d_mode)
                st.image(depth_img, caption=f"深度图 ({'空间尺度' if d_mode == 'plan' else '远近关系'})", width=256)
                st.caption("亮=近/高，暗=远/低")

st.markdown("---")

# ---- 1.5 设计策略风格 ----
render_section_intro(
    "设计策略风格",
    "根据前期设计决策自动匹配渲染风格，也可手动选择。风格影响提示词、色彩、材质和光影。",
    eyebrow="Style Strategy",
)

# 自动检测策略
try:
    from src.workflow.design_context import build_design_context as _bdc
    _ctx = _bdc()
    auto_styles = _detect_strategy_from_context(_ctx)
except Exception:
    auto_styles = ["微更新修补"]

# 风格选择（支持多选）
style_options = list(STRATEGY_STYLES.keys())
default_selection = [s for s in auto_styles if s in style_options] or ["微更新修补"]

selected_styles = st.multiselect(
    "选择渲染风格（可多选组合）",
    style_options,
    default=default_selection,
    key="aigc_styles",
    help="选择的设计策略将自动影响提示词中的建筑风格、材质、色彩和氛围描述",
)

# 显示选中风格的详细信息
if selected_styles:
    cols = st.columns(min(3, len(selected_styles)))
    for i, style_name in enumerate(selected_styles):
        style = STRATEGY_STYLES[style_name]
        with cols[i % len(cols)], st.container(border=True):
            st.markdown(f"**{style_name}**")
            st.caption(f"🎨 色彩: {style['colors']}")
            st.caption(f"🧱 材质: {style['materials'][:60]}...")
            st.caption(f"💡 光影: {style['lighting'][:60]}...")

st.markdown("---")

# ---- 2. 底图上传 ----
render_section_intro("底图上传", "提供图生图的基础图像。", eyebrow="Upload")

mode_short = render_mode.split(" ")[0]
col1, col2 = st.columns(2)
with col1:
    base_map_file = st.file_uploader("底图 / 参考图", type=["png", "jpg", "jpeg", "webp"], key="aigc_base_map")
with col2:
    if mode_short == "inpainting":
        mask_file = st.file_uploader("蒙版 (Mask)", type=["png", "jpg", "jpeg"], key="aigc_mask")
    else:
        mask_file = None
        st.caption("蒙版仅在局部重绘模式下需要")

if base_map_file is not None:
    base_img = PILImage.open(base_map_file)
    st.image(base_img, caption=f"底图预览 ({base_img.size[0]}×{base_img.size[1]})", width=400)

st.markdown("---")

# ---- 3. 提示词 ----
render_section_intro("提示词", "写场景描述后可直接渲染，也可先 AI 润色获得更专业的提示词。", eyebrow="Prompt")

# 从 DesignContext 自动生成场景描述
auto_desc = _build_auto_scene_description()
design_ctx_text = _build_design_context_prompt()
default_scene = auto_desc if auto_desc else "城市更新后的街道透视图，保留历史建筑，增加绿化和公共空间，人行道宽敞，有行道树和座椅"

scene_description = st.text_area(
    "场景描述 (中文即可)",
    value=st.session_state.get("aigc_scene_desc", default_scene),
    height=150,
    key="aigc_scene_desc",
)

# 显示设计上下文摘要
if design_ctx_text:
    with st.expander("📋 当前设计上下文（来自 DesignContext）", expanded=False):
        st.caption(design_ctx_text[:1000])

col_ai, col_model = st.columns([3, 1])
with col_ai:
    ds_model = st.text_input("AI 模型", value="deepseek-v4-flash", key="aigc_ds_model", label_visibility="collapsed")

if st.button("🧠 AI 润色提示词", type="secondary", key="aigc_polish", **stretch_width(st.button)):
    from src.engines.llm_engine import call_llm_engine
    with st.spinner("AI 润色中..."):
        # 注入设计上下文 + 策略风格到润色 prompt
        ctx_block = f"\n\n设计背景：\n{design_ctx_text[:600]}" if design_ctx_text else ""
        style_block = f"\n\n渲染风格要求：\n{_build_style_prompt(selected_styles)}" if selected_styles else ""
        style_params = _get_style_params(selected_styles)
        negative_extra = style_params.get("negative_extra", "")

        polish_prompt = f"""你是一位专业的建筑可视化提示词工程师，擅长为 Stable Diffusion 生成高质量提示词。
请根据以下场景描述和渲染风格要求，生成一段专业的英文提示词。

要求：
1. 以 masterpiece, best quality, ultra-detailed, urban design, architectural visualization 开头
2. 严格遵循渲染风格中的建筑风格、材质、色彩和氛围描述
3. 包含具体的建筑风格（如：新中式、现代简约、历史保护修缮）、材质（如：青砖、玻璃幕墙、石材）
4. 描述空间关系和透视角度（如：鸟瞰、街景透视、轴测）
5. 包含环境细节：绿化率、行道树种类、公共空间活动、天空状态
6. 末尾添加画质增强词：8k, professional photography, cinematic lighting, volumetric fog
7. 负向提示词单独一行，以 [Negative]: 开头，必须包含：low quality, blurry, distorted, deformed, ugly, watermark, text, oversaturated, cartoon, anime, sketch
8. 负向提示词中还要排除与当前风格矛盾的元素
9. 只输出提示词，不要解释

场景描述：{scene_description}{ctx_block}{style_block}"""

        result = call_llm_engine(
            prompt=polish_prompt,
            system_prompt="你是专业的建筑可视化提示词专家，精通城市规划和建筑设计领域的英文提示词工程。只输出英文提示词，不要解释。",
            model=ds_model,
        )

    if result and isinstance(result, str) and len(result) > 20:
        if "[Negative]:" in result:
            parts = result.split("[Negative]:")
            st.session_state["aigc_prompt"] = parts[0].strip()
            st.session_state["aigc_neg"] = parts[1].strip()
        else:
            st.session_state["aigc_prompt"] = result.strip()
            st.session_state["aigc_neg"] = "low quality, blurry, distorted, deformed, ugly, watermark, text, oversaturated, cartoon, anime, sketch, lowres, bad anatomy"
        st.session_state["aigc_prompt_polished"] = True
        st.rerun()
    else:
        st.warning("润色失败，请检查 DeepSeek API 配置。可直接使用场景描述渲染。")

# 显示提示词（润色后可编辑，未润色也可直接使用）
prompt_polished = st.session_state.get("aigc_prompt_polished", False)
current_prompt = st.session_state.get("aigc_prompt", "")
current_neg = st.session_state.get("aigc_neg", "low quality, blurry, distorted, deformed, ugly, watermark, text, oversaturated")

if prompt_polished and current_prompt:
    st.success("✅ 提示词已润色")
    col_p, col_n = st.columns(2)
    with col_p:
        prompt = st.text_area("正向提示词 (可编辑)", value=current_prompt, height=120, key="aigc_prompt_edit")
    with col_n:
        negative_prompt = st.text_area("负向提示词 (可编辑)", value=current_neg, height=120, key="aigc_neg_edit")
else:
    # 未润色时也可直接渲染（使用场景描述作为 prompt）
    st.info("💡 可直接点击渲染（使用场景描述），或先点击「AI 润色」获得更专业的英文提示词。")
    prompt = scene_description
    negative_prompt = current_neg

st.markdown("---")

# ---- 4. 渲染 ----
# 移除强制润色门控：有场景描述即可渲染
can_render = bool(prompt)

render_section_intro("渲染", "确认参数后点击渲染。", eyebrow="Render")

# 应用策略风格参数
style_params = _get_style_params(selected_styles)
effective_denoising = max(0.1, min(1.0, denoising + style_params.get("denoising_boost", 0)))
cn_weight_adj = style_params.get("cn_weight_boost", 0)
style_neg_extra = style_params.get("negative_extra", "")
if style_neg_extra and style_neg_extra not in negative_prompt:
    negative_prompt = f"{negative_prompt}, {style_neg_extra}"

col_s1, col_s2, col_s3, col_s4, col_s5, col_s6 = st.columns(6)
col_s1.metric("模式", mode_short)
col_s2.metric("分辨率", f"{output_w}×{output_h}")
col_s3.metric("Denoising", f"{effective_denoising:.2f}")
col_s4.metric("ControlNet", f"{len(cn_enabled_keys) + (1 if enable_depth else 0)} 层")
col_s5.metric("风格", "/".join([s[:2] for s in selected_styles]) if selected_styles else "默认")
col_s6.metric("提示词", "✅ 已润色" if prompt_polished else "📝 场景描述")

if st.button(
    "🚀 开始渲染",
    type="primary",
    key="aigc_render",
    disabled=not can_render,
    **stretch_width(st.button),
):
    from src.engines.stable_diffusion_engine import SDPipeline

    pipe = SDPipeline()

    # 切换 SD 模型（如果用户选择了不同模型）
    if sd_model:
        try:
            import requests
            requests.post("http://127.0.0.1:7860/sdapi/v1/options",
                          json={"sd_model_checkpoint": sd_model}, timeout=10)
        except Exception:
            pass  # 模型切换失败不阻断渲染

    if mode_short == "txt2img":
        pipe.txt2img(prompt, negative_prompt, width=output_w, height=output_h,
                     steps=steps, cfg_scale=cfg_scale, sampler_name=sampler, seed=seed)
    else:
        if base_map_file is not None:
            init_img = PILImage.open(base_map_file).convert("RGB")
        else:
            init_img = PILImage.new("RGB", (output_w, output_h), "#1e293b")
            st.warning("未上传底图，使用默认黑色画布。")

        if mode_short == "inpainting":
            if mask_file is not None:
                mask_img = PILImage.open(mask_file).convert("L")
                pipe.inpaint(init_img, mask_img, prompt, negative_prompt,
                             denoising=effective_denoising, steps=steps, cfg_scale=cfg_scale,
                             sampler_name=sampler, seed=seed)
            else:
                st.error("局部重绘模式需要上传蒙版。")
                st.stop()
        else:
            pipe.img2img(init_img, prompt, negative_prompt,
                         denoising=effective_denoising, steps=steps, cfg_scale=cfg_scale,
                         sampler_name=sampler, seed=seed)

        # ControlNet 约束（使用用户选择的预处理器和对应模型，应用风格调整）
        cn_model = CN_MODEL_MAP.get(cn_module, "control_v11p_sd15_canny")
        for key in cn_enabled_keys:
            info = available_constraints[key]
            base_weight = cn_weights.get(key, info["default_weight"])
            weight = max(0.1, min(2.0, base_weight + cn_weight_adj))
            if key in cn_images:
                cn_img = cn_images[key]
            else:
                if key == "landuse":
                    cn_img = render_landuse_overlay(
                        str(info["path"]), width=init_img.size[0], height=init_img.size[1],
                        lng_range=preview_lng, lat_range=preview_lat,
                    )
                else:
                    cn_img = render_geojson_to_image(
                        str(info["path"]), width=init_img.size[0], height=init_img.size[1],
                        lng_range=preview_lng, lat_range=preview_lat,
                    )
            pipe.add_controlnet(cn_img, module=cn_module, model=cn_model, weight=weight)

        # 深度图约束
        if enable_depth:
            road_path = str(ROOT / "static/road_clipped.geojson")
            bldg_path = str(ROOT / "static/buildings.geojson")
            d_mode = "plan" if depth_mode.startswith("平面") else "perspective"
            depth_img = render_depth_map(
                road_path, bldg_path,
                width=init_img.size[0], height=init_img.size[1],
                lng_range=preview_lng, lat_range=preview_lat,
                mode=d_mode,
            )
            depth_cn_model = CN_MODEL_MAP.get(cn_depth_module_val, "control_v11f1p_sd15_depth")
            pipe.add_controlnet(depth_img, module=cn_depth_module_val, model=depth_cn_model, weight=depth_weight)

    # 执行渲染
    progress_bar = st.progress(0, text="准备渲染...")
    def update_progress(**kwargs):
        step_idx = kwargs.get("step_index", 0)
        total = kwargs.get("total_steps", 1)
        progress_bar.progress((step_idx + 0.5) / total, text=f"渲染步骤 {step_idx + 1}/{total}...")

    try:
        with st.spinner("SD 渲染中，请耐心等待..."):
            sd_result = pipe.run(on_progress=update_progress)
        progress_bar.progress(1.0, text="渲染完成!")
        if sd_result.images:
            result_img = sd_result.images[0]
            st.session_state["aigc_result_image"] = result_img
            st.session_state["aigc_result_seed"] = sd_result.seed
            st.session_state["aigc_result_time"] = sd_result.elapsed_seconds

            # 保存到 stage_bus
            from src.workflow.stage_data_bus import save_stage_output
            save_stage_output("15", SK.AIGC_PROMPT, prompt)
            save_stage_output("15", SK.AIGC_SEED, sd_result.seed)

            # 保存到历史记录
            if "aigc_history" not in st.session_state:
                st.session_state["aigc_history"] = []
            st.session_state["aigc_history"].append({
                "image": result_img,
                "seed": sd_result.seed,
                "time": sd_result.elapsed_seconds,
                "prompt": prompt[:100],
                "mode": mode_short,
                "timestamp": time.strftime("%H:%M:%S"),
            })
            # 限制历史记录数
            if len(st.session_state["aigc_history"]) > 10:
                st.session_state["aigc_history"] = st.session_state["aigc_history"][-10:]
        else:
            st.error("渲染未返回图像。")
    except Exception as e:
        st.error(f"SD 渲染失败: {e}")

# ---- 渲染结果 ----
if "aigc_result_image" in st.session_state:
    st.markdown("---")
    render_section_intro("渲染结果", "查看渲染结果，支持下载。", eyebrow="Result")
    result_img = st.session_state["aigc_result_image"]
    result_seed = st.session_state.get("aigc_result_seed", "N/A")
    result_time = st.session_state.get("aigc_result_time", 0)
    col_img, col_info = st.columns([3, 1])
    with col_img:
        st.image(result_img, caption="渲染结果", use_container_width=True)
    with col_info:
        st.metric("Seed", result_seed)
        st.metric("耗时", f"{result_time:.1f}s")
        st.metric("尺寸", f"{result_img.size[0]}×{result_img.size[1]}")
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        st.download_button("📥 下载 PNG", buf.getvalue(), file_name=f"aigc_result_{result_seed}.png",
                           mime="image/png", **stretch_width(st.download_button))

# ---- 历史记录 ----
history = st.session_state.get("aigc_history", [])
if history:
    st.markdown("---")
    with st.expander(f"📚 渲染历史 ({len(history)} 张)", expanded=False):
        for i, item in enumerate(reversed(history)):
            col_thumb, col_meta = st.columns([1, 2])
            with col_thumb:
                st.image(item["image"], width=200)
            with col_meta:
                st.caption(f"**{item['timestamp']}** | Seed: {item['seed']} | {item['time']:.1f}s | {item['mode']}")
                st.caption(f"Prompt: {item['prompt']}...")
