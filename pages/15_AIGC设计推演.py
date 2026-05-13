"""AIGC 设计推演 —— 图生图渲染中心。

AI 润色提示词 → 空间约束锁定 → 深度图精确尺度 → SD 渲染。
"""

import json
import math
import streamlit as st
from pathlib import Path
from PIL import Image as PILImage, ImageDraw

from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.app_shell import render_top_nav
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="AIGC 设计推演", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="AIGC 设计推演",
    description="AI 润色提示词，ControlNet 锁定路网与建筑轮廓，深度图定义精确空间尺度。",
    eyebrow="AIGC Studio",
    tags=["AI 润色", "ControlNet", "深度图", "空间尺度"],
)

ROOT = Path(__file__).resolve().parent.parent

# 道路等级对应的现实宽度 (米)
ROAD_WIDTH_METERS = {
    1: 30,   # 一级道路 (主干道)
    2: 20,   # 二级道路 (次干道)
    3: 12,   # 三级道路 (支路)
    4: 6,    # 其他道路
}

# 建筑高度等级对应的深度值 (越近越亮)
BUILDING_DEPTH = {
    "low": 80,     # 低层 (<12m)
    "mid": 160,    # 中层 (12-24m)
    "high": 220,   # 高层 (>24m)
}


# ══════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════

@st.cache_data(ttl=3600)
def render_geojson_to_image(geojson_path: str, width: int = 1024, height: int = 768,
                            line_color: int = 255, line_width: int = 2,
                            lng_range: tuple = None, lat_range: tuple = None) -> "PILImage.Image":
    """将 GeoJSON 渲染为黑白线稿图，用于 ControlNet 输入。"""
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
    if lng_range:
        lng_min, lng_max = lng_range
    else:
        lng_min, lng_max = min(all_lngs), max(all_lngs)
    if lat_range:
        lat_min, lat_max = lat_range
    else:
        lat_min, lat_max = min(all_lats), max(all_lats)
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
    for feat in features:
        _draw_geometry(draw, feat["geometry"], to_pixel, line_color, line_width)
    return img


@st.cache_data(ttl=3600)
def render_depth_map(road_path: str, building_path: str,
                     width: int = 1024, height: int = 768,
                     lng_range: tuple = None, lat_range: tuple = None,
                     mode: str = "plan") -> "PILImage.Image":
    """渲染深度图。

    mode="plan": 平面类图纸 — 道路宽度按真实米数，建筑高度按楼层，编码空间尺度。
    mode="perspective": 透视类图纸 — 底部(近)亮，顶部(远)暗，编码远近关系。
    """
    # 收集所有坐标确定范围
    all_lngs, all_lats = [], []
    for p in [road_path, building_path]:
        if Path(p).exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            for feat in data.get("features", []):
                _collect_coords(feat["geometry"], all_lngs, all_lats)
    if not all_lngs:
        return PILImage.new("RGB", (width, height), (0, 0, 0))
    if lng_range:
        lng_min, lng_max = lng_range
    else:
        lng_min, lng_max = min(all_lngs), max(all_lngs)
    if lat_range:
        lat_min, lat_max = lat_range
    else:
        lat_min, lat_max = min(all_lats), max(all_lats)
    lng_pad = (lng_max - lng_min) * 0.02
    lat_pad = (lat_max - lat_min) * 0.02
    lng_min -= lng_pad; lng_max += lng_pad
    lat_min -= lat_pad; lat_max += lat_pad

    # 计算像素/米比例
    center_lat = (lat_min + lat_max) / 2
    meters_per_deg_lng = 111320 * math.cos(math.radians(center_lat))
    meters_per_deg_lat = 110540
    lng_range_m = (lng_max - lng_min) * meters_per_deg_lng
    lat_range_m = (lat_max - lat_min) * meters_per_deg_lat
    pixels_per_meter_x = width / lng_range_m
    pixels_per_meter_y = height / lat_range_m

    img = PILImage.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)

    def to_pixel(lng, lat):
        x = (lng - lng_min) / (lng_max - lng_min) * width
        y = (1 - (lat - lat_min) / (lat_max - lat_min)) * height
        return (x, y)

    # 透视模式：先画底部亮→顶部暗的渐变底色
    if mode == "perspective":
        for row in range(height):
            # 底部(近)=200，顶部(远)=30
            gray = int(200 - (row / height) * 170)
            draw.line([(0, row), (width, row)], fill=gray)

    # 1. 绘制道路 (按等级赋予不同灰度)
    if Path(road_path).exists():
        with open(road_path, "r", encoding="utf-8") as f:
            road_data = json.load(f)
        for feat in road_data.get("features", []):
            level = feat.get("properties", {}).get("level", 4)
            road_width_m = ROAD_WIDTH_METERS.get(level, 6)
            px_width = max(1, int(road_width_m * pixels_per_meter_x))
            if mode == "plan":
                # 平面模式：路越宽越亮(空间尺度)
                gray = {1: 200, 2: 150, 3: 100, 4: 60}.get(level, 60)
            else:
                # 透视模式：路越宽越亮(叠加在渐变上)
                gray = {1: 230, 2: 190, 3: 150, 4: 110}.get(level, 110)
            _draw_geometry(draw, feat["geometry"], to_pixel, gray, px_width)

    # 2. 绘制建筑轮廓 (按高度赋予深度值)
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
            if height_m <= 0:
                depth_val = BUILDING_DEPTH["low"]
            elif height_m <= 12:
                depth_val = BUILDING_DEPTH["low"]
            elif height_m <= 24:
                depth_val = BUILDING_DEPTH["mid"]
            else:
                depth_val = BUILDING_DEPTH["high"]
            if mode == "perspective":
                # 透视模式：建筑叠加在渐变上，更高的建筑更亮
                depth_val = min(255, depth_val + 40)
            _draw_geometry(draw, feat["geometry"], to_pixel, depth_val, 3)

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
    """递归绘制几何图形。"""
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
                draw.line(points + [points[0]], fill=color, width=width)
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                points = [to_pixel(c[0], c[1]) for c in ring if len(c) >= 2]
                if len(points) >= 2:
                    draw.line(points + [points[0]], fill=color, width=width)
    elif gtype == "GeometryCollection":
        for g in geometry.get("geometries", []):
            _draw_geometry(draw, g, to_pixel, color, width)


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
    st.markdown("---")
    st.markdown("### 🎛️ 渲染参数")
    denoising = st.slider("重绘强度", 0.1, 1.0, 0.55, 0.05, key="aigc_denoising")
    steps = st.slider("采样步数", 10, 50, 20, 5, key="aigc_steps")
    cfg_scale = st.slider("CFG Scale", 1.0, 15.0, 7.0, 0.5, key="aigc_cfg")
    sampler = st.selectbox("采样器", ["DPM++ 2M Karras", "Euler a", "DPM++ SDE Karras", "DDIM", "UniPC"], key="aigc_sampler")
    seed = st.number_input("种子 (-1=随机)", value=-1, min_value=-1, key="aigc_seed")

# ══════════════════════════════════════════
# 主区域
# ══════════════════════════════════════════

# ---- 1. 空间约束 ----
render_section_intro(
    "空间约束 (ControlNet)",
    "自动加载路网、建筑轮廓、研究边界，渲染时自动注入 ControlNet 锁定不变。",
    eyebrow="Spatial Lock",
)

SPATIAL_DATA = {
    "boundary": {"path": ROOT / "data/gis/Boundary_Scope.geojson", "label": "🔲 研究边界", "module": "canny", "model": "control_v11p_sd15_canny", "default_weight": 1.0},
    "roads": {"path": ROOT / "static/road_clipped.geojson", "label": "🛣️ 道路网络", "module": "canny", "model": "control_v11p_sd15_canny", "default_weight": 0.8},
    "buildings": {"path": ROOT / "static/buildings.geojson", "label": "🏢 建筑轮廓", "module": "canny", "model": "control_v11p_sd15_canny", "default_weight": 0.7},
    "plots": {"path": ROOT / "data/gis/Key_Plots_District.json", "label": "✴️ 重点地块", "module": "canny", "model": "control_v11p_sd15_canny", "default_weight": 1.0},
}
available_constraints = {k: v for k, v in SPATIAL_DATA.items() if v["path"].exists()}

col_checks = st.columns(len(available_constraints) if available_constraints else 1)
cn_enabled_keys = []
for i, (key, info) in enumerate(available_constraints.items()):
    with col_checks[i]:
        if st.checkbox(info["label"], value=(key in ("boundary", "buildings")), key=f"cn_{key}"):
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
    # 确定统一坐标范围
    preview_lng, preview_lat = None, None
    boundary_path = ROOT / "data/gis/Boundary_Scope.geojson"
    if boundary_path.exists():
        with open(boundary_path, "r", encoding="utf-8") as f:
            bdata = json.load(f)
        blng, blat = [], []
        for feat in bdata.get("features", []):
            _collect_coords(feat["geometry"], blng, blat)
        if blng:
            preview_lng = (min(blng), max(blng))
            preview_lat = (min(blat), max(blat))

    preview_cols = st.columns(min(3, len(cn_enabled_keys) + (1 if enable_depth else 0)))
    cn_images = {}
    for i, key in enumerate(cn_enabled_keys[:3]):
        info = available_constraints[key]
        with preview_cols[i % len(preview_cols)]:
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

# ---- 2. 底图上传 ----
render_section_intro("底图上传", "提供图生图的基础图像。", eyebrow="Upload")

col1, col2 = st.columns(2)
with col1:
    base_map_file = st.file_uploader("底图 / 参考图", type=["png", "jpg", "jpeg", "webp"], key="aigc_base_map")
with col2:
    mask_file = st.file_uploader("蒙版 (Mask)", type=["png", "jpg", "jpeg"], key="aigc_mask")

if base_map_file is not None:
    base_img = PILImage.open(base_map_file)
    st.image(base_img, caption=f"底图预览 ({base_img.size[0]}×{base_img.size[1]})", width=400)

st.markdown("---")

# ---- 3. 提示词 (必须 AI 润色) ----
render_section_intro("提示词", "先写场景描述，再由 AI 润色为专业提示词后才能渲染。", eyebrow="Prompt")

# 场景描述输入
scene_description = st.text_area(
    "场景描述 (中文即可)",
    value="城市更新后的街道透视图，保留历史建筑，增加绿化和公共空间，人行道宽敞，有行道树和座椅",
    height=100,
    key="aigc_scene_desc",
)

col_ai, col_model = st.columns([3, 1])
with col_ai:
    ds_model = st.text_input("AI 模型", value="deepseek-chat", key="aigc_ds_model", label_visibility="collapsed")
with col_model:
    pass

if st.button("🧠 AI 润色提示词", type="primary", key="aigc_polish", **stretch_width(st.button)):
    from src.engines.llm_engine import call_llm_engine
    with st.spinner("AI 润色中..."):
        polish_prompt = f"""你是一位专业的 AI 绘图提示词工程师，擅长为 Stable Diffusion 生成高质量提示词。
请根据以下场景描述，生成一段专业的英文提示词。

要求：
1. 以 masterpiece, best quality, ultra-detailed 开头
2. 包含建筑风格、材质、光影、色彩、植物、人物活动等细节
3. 描述空间关系和透视角度
4. 末尾添加画质增强词：8k, professional photography, architectural visualization
5. 负向提示词单独一行，以 [Negative]: 开头
6. 只输出提示词，不要解释

场景描述：{scene_description}"""

        result = call_llm_engine(
            prompt=polish_prompt,
            system_prompt="你是专业的建筑可视化提示词专家。只输出英文提示词，不要解释。",
            model=ds_model,
        )

    if result and isinstance(result, str) and len(result) > 20:
        # 解析正向和负向提示词
        if "[Negative]:" in result:
            parts = result.split("[Negative]:")
            st.session_state["aigc_prompt"] = parts[0].strip()
            st.session_state["aigc_neg"] = parts[1].strip()
        else:
            st.session_state["aigc_prompt"] = result.strip()
            st.session_state["aigc_neg"] = "low quality, blurry, distorted, deformed, ugly, watermark, text, oversaturated"
        st.session_state["aigc_prompt_polished"] = True
        st.rerun()
    else:
        st.warning("润色失败，请检查 DeepSeek API 配置。")

# 显示润色后的提示词
prompt_polished = st.session_state.get("aigc_prompt_polished", False)
current_prompt = st.session_state.get("aigc_prompt", "")
current_neg = st.session_state.get("aigc_neg", "")

if prompt_polished and current_prompt:
    st.success("✅ 提示词已润色，可以渲染")
    col_p, col_n = st.columns(2)
    with col_p:
        prompt = st.text_area("润色后的正向提示词", value=current_prompt, height=120, key="aigc_prompt_edit")
    with col_n:
        negative_prompt = st.text_area("润色后的负向提示词", value=current_neg, height=120, key="aigc_neg_edit")
else:
    st.warning("⚠️ 请先点击「AI 润色提示词」按钮，润色后才能渲染。")
    prompt = current_prompt
    negative_prompt = current_neg

st.markdown("---")

# ---- 4. 渲染 ----
can_render = prompt_polished and bool(current_prompt)

render_section_intro("渲染", "确认参数后点击渲染。", eyebrow="Render")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.metric("模式", render_mode.split(" ")[0])
col_s2.metric("Denoising", f"{denoising:.2f}")
col_s3.metric("ControlNet", f"{len(cn_enabled_keys) + (1 if enable_depth else 0)} 层")
col_s4.metric("提示词", "✅ 已润色" if prompt_polished else "❌ 未润色")

if st.button(
    "🚀 开始渲染",
    type="primary",
    key="aigc_render",
    disabled=not can_render,
    **stretch_width(st.button),
):
    from src.engines.stable_diffusion_engine import SDPipeline

    pipe = SDPipeline()

    if render_mode == "txt2img (纯文生图)":
        pipe.txt2img(prompt, negative_prompt, width=1024, height=768,
                     steps=steps, cfg_scale=cfg_scale, sampler_name=sampler, seed=seed)
    else:
        if base_map_file is not None:
            init_img = PILImage.open(base_map_file).convert("RGB")
        else:
            init_img = PILImage.new("RGB", (1024, 768), "#1e293b")
            st.warning("未上传底图，使用默认黑色画布。")

        if render_mode == "inpainting (局部重绘)":
            if mask_file is not None:
                mask_img = PILImage.open(mask_file).convert("L")
                pipe.inpaint(init_img, mask_img, prompt, negative_prompt,
                             denoising=denoising, steps=steps, cfg_scale=cfg_scale,
                             sampler_name=sampler, seed=seed)
            else:
                st.error("局部重绘模式需要上传蒙版。")
                st.stop()
        else:
            pipe.img2img(init_img, prompt, negative_prompt,
                         denoising=denoising, steps=steps, cfg_scale=cfg_scale,
                         sampler_name=sampler, seed=seed)

        # ControlNet 线稿约束
        for key in cn_enabled_keys:
            info = available_constraints[key]
            weight = cn_weights.get(key, info["default_weight"])
            if key in cn_images:
                cn_img = cn_images[key]
            else:
                cn_img = render_geojson_to_image(
                    str(info["path"]), width=init_img.size[0], height=init_img.size[1],
                    lng_range=preview_lng, lat_range=preview_lat,
                )
            pipe.add_controlnet(cn_img, module=info["module"], model=info["model"], weight=weight)

        # ControlNet 深度图约束
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
            pipe.add_controlnet(depth_img, module="depth", model="control_v11f1p_sd15_depth", weight=depth_weight)

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
            st.session_state["aigc_result_image"] = sd_result.images[0]
            st.session_state["aigc_result_seed"] = sd_result.seed
            st.session_state["aigc_result_time"] = sd_result.elapsed_seconds
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
        import io
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        st.download_button("📥 下载 PNG", buf.getvalue(), file_name=f"aigc_result_{result_seed}.png",
                           mime="image/png", **stretch_width(st.download_button))
