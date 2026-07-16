"""GIS白模渲染器 —— 从建筑轮廓+层数生成统一3D白模，保证AIGC出图建筑一致性

核心管线:
  Building_Footprints.geojson (2D polygon + Floor字段)
    → 挤出为3D体块 (Floor × 3.5m 层高)
    → 从多角度渲染白模 (鸟瞰 / 地块人视)
    → 输出 depth map + edge map → ControlNet 输入
    → SD img2img (低denoising保持形态, 高style注入材质)

Usage:
    from src.engines.white_model_renderer import WhiteModelRenderer
    renderer = WhiteModelRenderer()
    renderer.render_birdseye("output/birdseye_white.png")
    renderer.render_plot_view("老水产批发市场", "output/plot1_white.png")
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

logger = logging.getLogger("ultimateDESIGN")

# ══════════════════════════════════════════════════════════
# 建筑几何定义
# ══════════════════════════════════════════════════════════

FLOOR_HEIGHT = 3.5  # 标准层高 (m)
BUILDING_COLOR_LIGHT = (240, 240, 245)   # 白模亮面
BUILDING_COLOR_DARK = (200, 200, 210)     # 白模暗面
BUILDING_COLOR_ROOF = (255, 255, 255)     # 屋顶色
GROUND_COLOR = (180, 180, 185)            # 地面
ROAD_COLOR = (160, 160, 165)              # 道路
WATER_COLOR = (140, 180, 210)             # 水系
PLOT_BOUNDARY_COLOR = (255, 80, 80)       # 重点地块红线

# ══════════════════════════════════════════════════════════
# 视角定义
# ══════════════════════════════════════════════════════════

@dataclass
class CameraView:
    """相机视角定义"""
    name: str
    # 相机位置 (经度, 纬度, 高度m)
    eye_lng: float
    eye_lat: float
    eye_alt: float
    # 注视点 (经度, 纬度)
    target_lng: float
    target_lat: float
    # 视场角 (度)
    fov: float = 45.0
    # 图像分辨率
    width: int = 1024
    height: int = 768


# 预定义视角
PRESET_VIEWS: dict[str, CameraView] = {
    "birdseye_sw": CameraView(
        name="鸟瞰_西南",
        eye_lng=125.340, eye_lat=43.900, eye_alt=800,
        target_lng=125.352, target_lat=43.912,
        fov=35.0, width=1280, height=960,
    ),
    "birdseye_se": CameraView(
        name="鸟瞰_东南",
        eye_lng=125.364, eye_lat=43.900, eye_alt=800,
        target_lng=125.352, target_lat=43.912,
        fov=35.0, width=1280, height=960,
    ),
    "birdseye_nw": CameraView(
        name="鸟瞰_西北",
        eye_lng=125.340, eye_lat=43.924, eye_alt=600,
        target_lng=125.352, target_lat=43.912,
        fov=40.0, width=1280, height=960,
    ),
}


# ══════════════════════════════════════════════════════════
# 一致的建筑风格提示词 (所有出图共用)
# ══════════════════════════════════════════════════════════

CONSISTENT_STYLE_PROMPT = """architectural visualization, urban renewal historic district,
consistent building style across all views:
- neo-classical mansard roofs with dark grey slate tiles,
- cream limestone facade with subtle horizontal banding,
- uniform window rhythm (tall rectangular windows, dark bronze frames, recessed 15cm),
- ground floor: transparent glass storefront with dark steel mullions,
- building heights strictly as modeled (no added floors),
- historic preservation district character, early 20th century industrial heritage adapted,
- tree-lined streets with ginkgo trees, wide pedestrian sidewalks,
- warm late afternoon sunlight, golden hour, soft shadows,
- 8k resolution, architectural photography, highly detailed, coherent across views"""

CONSISTENT_NEGATIVE_PROMPT = """different building heights, mismatched window styles,
modern glass curtain wall, skyscrapers, suburban sprawl, cartoon, watermark, text,
blurry, distorted geometry, buildings floating, inconsistent roof forms,
extra floors added, missing buildings, displaced buildings"""

# ══════════════════════════════════════════════════════════
# 建筑几何加载 & 挤出
# ══════════════════════════════════════════════════════════

@dataclass
class Building3D:
    """单栋建筑的3D表示"""
    building_id: str
    footprint: list[tuple[float, float]]  # 底面多边形 (lng, lat)
    floors: int
    height_m: float                        # floors × FLOOR_HEIGHT
    is_historical: bool = False
    prop_style: str = "normal"
    centroid: tuple[float, float] = (0, 0)


@dataclass
class PlotBoundary:
    """重点地块"""
    name: str
    boundary: list[tuple[float, float]]
    centroid: tuple[float, float]


class WhiteModelRenderer:
    """从GIS建筑数据生成统一白模的渲染器"""

    def __init__(self, data_dir: Path | None = None):
        from src.config import DATA_DIR
        self.data_dir = data_dir or DATA_DIR
        self.buildings: list[Building3D] = []
        self.plots: list[PlotBoundary] = []
        self.bounds: tuple[float, float, float, float] = (0, 0, 0, 0)
        self._loaded = False

    # ── 数据加载 ──

    def load_data(self, max_buildings: int = 20000):
        """加载建筑轮廓和重点地块数据

        Args:
            max_buildings: 最大加载建筑数 (110k全量会慢, 采样保证性能)
        """
        if self._loaded:
            return

        # 加载建筑
        building_path = self.data_dir / "gis" / "Building_Footprints.geojson"
        if building_path.exists():
            with open(building_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            features = data["features"]
            # 对大量建筑进行采样 (均匀采样保持空间分布)
            total = len(features)
            if total > max_buildings:
                step = total // max_buildings
                sampled = features[::step]
                logger.info(f"Sampled {len(sampled)} buildings from {total}")
            else:
                sampled = features

            for feat in sampled:
                props = feat["properties"]
                geom = feat["geometry"]
                coords = self._extract_polygon(geom)
                if not coords or len(coords) < 3:
                    continue

                floors = props.get("Floor", 1)
                if floors is None or floors < 1:
                    floors = 1

                bld = Building3D(
                    building_id=props.get("building_id", ""),
                    footprint=coords,
                    floors=int(floors),
                    height_m=int(floors) * FLOOR_HEIGHT,
                    is_historical=props.get("is_historical", False),
                    prop_style=props.get("prop_style", "normal"),
                    centroid=self._centroid(coords),
                )
                self.buildings.append(bld)

        # 加载重点地块
        plots_path = self.data_dir / "gis" / "Key_Plots_District.json"
        if plots_path.exists():
            with open(plots_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for feat in data["features"]:
                name = feat["properties"].get("name", feat["properties"].get("Name", ""))
                coords = self._extract_polygon(feat["geometry"])
                if name and coords:
                    self.plots.append(PlotBoundary(
                        name=name,
                        boundary=coords,
                        centroid=self._centroid(coords),
                    ))

        # 计算边界
        if self.buildings:
            all_lngs = [c[0] for b in self.buildings for c in b.footprint]
            all_lats = [c[1] for b in self.buildings for c in b.footprint]
            self.bounds = (min(all_lngs), min(all_lats), max(all_lngs), max(all_lats))

        self._loaded = True
        logger.info(f"Loaded {len(self.buildings)} buildings, {len(self.plots)} plots")

    @staticmethod
    def _extract_polygon(geom: dict) -> list[tuple[float, float]]:
        """从 GeoJSON geometry 提取外环坐标"""
        try:
            if geom["type"] == "Polygon":
                rings = geom.get("coordinates", [])
                if rings and len(rings) > 0 and len(rings[0]) > 0:
                    return [(p[0], p[1]) for p in rings[0] if len(p) >= 2]
            elif geom["type"] == "MultiPolygon":
                best = []
                for ring in geom.get("coordinates", []):
                    if ring and len(ring) > 0 and len(ring[0]) > 0:
                        coords = [(p[0], p[1]) for p in ring[0] if len(p) >= 2]
                        if len(coords) > len(best):
                            best = coords
                return best
        except (IndexError, TypeError):
            pass
        return []

    @staticmethod
    def _centroid(coords: list[tuple[float, float]]) -> tuple[float, float]:
        x = sum(c[0] for c in coords) / len(coords)
        y = sum(c[1] for c in coords) / len(coords)
        return (x, y)

    # ── 坐标转换 (2.5D 等距投影) ──

    def _make_transform(self, view: CameraView):
        """创建 2.5D 等距投影变换"""
        cx, cy = view.target_lng, view.target_lat
        cos_lat = math.cos(math.radians(cy))
        scale_x = 111320.0 * cos_lat  # m/deg longitude
        scale_y = 111320.0            # m/deg latitude

        # 等距投影角度
        angle_deg = 30  # 标准等距视角
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        return {
            "cx": cx, "cy": cy,
            "scale_x": scale_x, "scale_y": scale_y,
            "cos_a": cos_a, "sin_a": sin_a,
            "z_scale": 0.3,   # 高度缩放因子 (m→pixel, 增大使建筑高度更明显)
            "global_scale": 2.0,  # 全局缩放 (增大使建筑体块更大)
        }

    def _project_2d(self, lng: float, lat: float, T: dict) -> tuple[float, float]:
        """2.5D 等距投影: (lng, lat) → (sx, sy)"""
        wx = (lng - T["cx"]) * T["scale_x"] * T["global_scale"]
        wy = (lat - T["cy"]) * T["scale_y"] * T["global_scale"]
        sx = (wx - wy) * T["cos_a"]
        sy = (wx + wy) * T["sin_a"]
        return (sx, sy)

    def _project_3d(self, lng: float, lat: float, alt: float, T: dict) -> tuple[float, float]:
        """2.5D 等距投影: (lng, lat, alt) → (sx, sy)"""
        sx, sy = self._project_2d(lng, lat, T)
        sy -= alt * T["z_scale"]  # 高度向上偏移 (屏幕y轴向下)
        return (sx, sy)

    # ═══════════════════════════════════════════════
    # 核心渲染 (2.5D 等距)
    # ═══════════════════════════════════════════════

    def render_view(self, view: CameraView, output_path: str,
                    highlight_plots: list[str] | None = None,
                    outline_only: bool = False) -> str:
        """从指定视角渲染 2.5D 等距白模

        使用 painter's algorithm: 远→近顺序绘制, 保证遮挡正确
        """
        self.load_data()
        T = self._make_transform(view)

        # 计算画布大小和偏移
        w, h = view.width, view.height
        ox, oy = w // 2, h // 2  # 画面中心

        img = Image.new("RGB", (w, h), (220, 225, 230))  # 淡蓝灰底
        draw = ImageDraw.Draw(img)

        # ── 1. 收集所有建筑投影并排序 (painter's algorithm: 远→近) ──
        projected = []
        for bld in self.buildings:
            # 投影底面中心
            bx, by = self._project_2d(bld.centroid[0], bld.centroid[1], T)
            # 投影底面所有点
            base_pts = []
            for lng, lat in bld.footprint:
                sx, sy = self._project_2d(lng, lat, T)
                base_pts.append((sx, sy))
            # 投影顶面
            roof_pts = []
            for lng, lat in bld.footprint:
                sx, sy = self._project_3d(lng, lat, bld.height_m, T)
                roof_pts.append((sx, sy))

            # 裁剪: 跳过完全在画布外的建筑
            in_view = any(
                -w < sx < w*2 and -h < sy < h*2
                for sx, sy in base_pts
            )
            if not in_view:
                continue

            # 深度键: 用于远→近排序 (等距投影中, x+y 越大越近)
            depth_key = bx + by
            projected.append((depth_key, bld, base_pts, roof_pts))

        # 远→近排序
        projected.sort(key=lambda x: x[0])

        # ── 2. 渲染建筑 ──
        for depth_key, bld, base_pts, roof_pts in projected:
            self._draw_building_25d(
                draw, bld, base_pts, roof_pts,
                ox, oy, w, h, outline_only,
            )

        # ── 3. 渲染地块边界 ──
        if highlight_plots:
            for plot in self.plots:
                if plot.name in highlight_plots:
                    plot_pts = []
                    for lng, lat in plot.boundary:
                        sx, sy = self._project_2d(lng, lat, T)
                        plot_pts.append((ox + sx, oy + sy))
                    if len(plot_pts) >= 3:
                        draw.polygon(plot_pts, outline=(220, 30, 30), width=5)

        # ── 4. 保存 ──
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        logger.info(f"White model rendered: {output_path} ({len(projected)} buildings)")
        return output_path

    def _draw_building_25d(self, draw: ImageDraw.ImageDraw, bld: Building3D,
                           base_pts: list[tuple[float, float]],
                           roof_pts: list[tuple[float, float]],
                           ox: float, oy: float, w: int, h: int,
                           outline_only: bool):
        """绘制单栋建筑的 2.5D 体块

        绘制顺序: 底面 → 暗面(左) → 亮面(右) → 顶面
        """
        # 偏移到画布中心
        base = [(ox + x, oy + y) for x, y in base_pts]
        roof = [(ox + x, oy + y) for x, y in roof_pts]

        if len(base) < 3 or len(roof) < 3:
            return

        # 楼高配色
        floor_count = bld.floors
        if bld.is_historical:
            base_color = (250, 245, 235)
            dark_color = (220, 210, 195)
            light_color = (255, 250, 242)
            roof_color = (240, 230, 215)
        elif floor_count <= 2:
            base_color = (230, 228, 225)
            dark_color = (200, 198, 195)
            light_color = (245, 244, 242)
            roof_color = (250, 248, 245)
        elif floor_count <= 5:
            base_color = (225, 222, 218)
            dark_color = (190, 186, 180)
            light_color = (240, 238, 235)
            roof_color = (248, 245, 240)
        else:
            base_color = (218, 214, 208)
            dark_color = (180, 175, 168)
            light_color = (235, 232, 228)
            roof_color = (245, 242, 235)

        if outline_only:
            # 仅轮廓
            draw.polygon(base, outline=(80, 80, 90))
            draw.polygon(roof, outline=(60, 60, 70))
            # 连接底面和顶面的对应顶点作为侧边
            for bpt, rpt in zip(base, roof):
                draw.line([bpt, rpt], fill=(90, 90, 100), width=1)
            return

        # ── 体块渲染 ──
        # 1. 底面 (阴影)
        shadow_offset = [(x + 3, y + 3) for x, y in base]
        draw.polygon(shadow_offset, fill=(160, 158, 155))

        # 2. 暗面 (左下侧) — 取底面最左下的点到对应顶面点
        if len(base) >= 4:
            sorted_by_x = sorted(base, key=lambda p: p[0])
            left_pts = sorted_by_x[:len(sorted_by_x)//2]
            # 暗面: base左半 + roof左半 (反转顺序)
            left_base = sorted(left_pts, key=lambda p: p[1])
            left_roof = sorted(roof[:len(roof)//2], key=lambda p: p[1], reverse=True)
            wall = left_base + left_roof
            if len(wall) >= 3:
                draw.polygon(wall, fill=dark_color, outline=dark_color)

        # 3. 亮面 (右上侧)
        sorted_by_x_r = sorted(base, key=lambda p: -p[0])
        right_pts = sorted_by_x_r[:len(sorted_by_x_r)//2]
        right_base = sorted(right_pts, key=lambda p: p[1])
        right_roof = sorted(roof[-len(roof)//2:], key=lambda p: p[1], reverse=True)
        wall_r = right_base + right_roof
        if len(wall_r) >= 3:
            draw.polygon(wall_r, fill=light_color, outline=light_color)

        # 4. 顶面
        draw.polygon(roof, fill=roof_color, outline=(170, 168, 165))

    # ── 深度图渲染 ──

    def render_depth_map(self, view: CameraView, output_path: str) -> str:
        """渲染 2.5D 深度图 (用于 ControlNet Depth)

        深度编码: 近处=白(255), 远处=黑(0)
        """
        self.load_data()
        T = self._make_transform(view)
        w, h = view.width, view.height
        ox, oy = w // 2, h // 2

        img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(img)

        # 收集建筑的屏幕位置和深度
        entries = []
        for bld in self.buildings:
            bx, by = self._project_2d(bld.centroid[0], bld.centroid[1], T)
            roof_pts = []
            for lng, lat in bld.footprint:
                sx, sy = self._project_3d(lng, lat, bld.height_m, T)
                roof_pts.append((ox + sx, oy + sy))
            if roof_pts and any(0 <= x < w and 0 <= y < h for x, y in roof_pts):
                entries.append((bx + by, roof_pts))

        if not entries:
            img.save(output_path, "PNG")
            return output_path

        # 归一化深度
        depths = [e[0] for e in entries]
        d_min, d_max = min(depths), max(depths)
        d_range = d_max - d_min if d_max > d_min else 1

        for depth, roof_pts in entries:
            depth_val = int(255 * (depth - d_min) / d_range)
            depth_val = max(40, min(255, depth_val))

            if len(roof_pts) >= 3:
                # 用膨胀多边形确保小建筑可见
                cx_p = sum(p[0] for p in roof_pts) / len(roof_pts)
                cy_p = sum(p[1] for p in roof_pts) / len(roof_pts)
                # 将屋顶各点向外扩展 2px
                inflated = []
                for px, py in roof_pts:
                    dx = px - cx_p
                    dy = py - cy_p
                    mag = max(math.sqrt(dx*dx + dy*dy), 0.1)
                    inflated.append((px + 2*dx/mag, py + 2*dy/mag))
                draw.polygon(inflated, fill=depth_val)
                # 同时绘制圆形以确保覆盖
                radius = max(3, int(math.sqrt(len(roof_pts))))
                draw.ellipse(
                    [cx_p - radius, cy_p - radius, cx_p + radius, cy_p + radius],
                    fill=depth_val,
                )

        # 高斯模糊使深度连续
        img = img.filter(ImageFilter.GaussianBlur(radius=5))

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        return output_path

    def _get_boundary_polygon(self) -> list[tuple[float, float]]:
        """获取研究范围边界多边形"""
        boundary_path = self.data_dir / "gis" / "Boundary_Scope.geojson"
        if boundary_path.exists():
            with open(boundary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data["features"]:
                return self._extract_polygon(data["features"][0]["geometry"])

        # 回退: 用建筑的外包络
        if self.bounds != (0, 0, 0, 0):
            min_lng, min_lat, max_lng, max_lat = self.bounds
            pad = 0.002
            return [
                (min_lng - pad, min_lat - pad),
                (max_lng + pad, min_lat - pad),
                (max_lng + pad, max_lat + pad),
                (min_lng - pad, max_lat + pad),
            ]
        return []

    # ═══════════════════════════════════════════════
    # 快捷渲染方法
    # ═══════════════════════════════════════════════

    def render_birdseye(self, output_path: str, direction: str = "sw") -> str:
        """渲染鸟瞰白模"""
        view_key = f"birdseye_{direction}"
        view = PRESET_VIEWS.get(view_key, PRESET_VIEWS["birdseye_sw"])
        return self.render_view(view, output_path,
                                highlight_plots=[p.name for p in self.plots])

    def render_plot_view(self, plot_name: str, output_path: str,
                         zoom_scale: float = 3.0) -> str:
        """渲染特定地块的放大 2.5D 白模

        放大到地块级别, 展示地块内建筑的形态关系
        """
        self.load_data()

        # 找到目标地块
        target_plot = None
        for plot in self.plots:
            if plot.name == plot_name:
                target_plot = plot
                break

        if target_plot is None:
            raise ValueError(f"Plot not found: {plot_name}")

        # 以地块为中心, 放大视图
        cx, cy = target_plot.centroid
        view = CameraView(
            name=f"地块_{plot_name}",
            eye_lng=0, eye_lat=0, eye_alt=0,  # 2.5D不需要eye参数
            target_lng=cx, target_lat=cy,
            fov=30.0, width=1024, height=768,
        )
        # 临时增大全局缩放来放大地块
        return self.render_view(view, output_path,
                                highlight_plots=[plot_name])

    def render_all_birdseye(self, output_dir: str) -> list[str]:
        """渲染所有预定义鸟瞰角度"""
        paths = []
        for direction in ["sw", "se", "nw"]:
            path = str(Path(output_dir) / f"birdseye_{direction}.png")
            self.render_birdseye(path, direction)
            paths.append(path)
        return paths

    def render_all_plots(self, output_dir: str) -> list[str]:
        """渲染所有重点地块的白模"""
        self.load_data()
        paths = []
        for plot in self.plots:
            safe_name = plot.name.replace("/", "_").replace(" ", "_")
            path = str(Path(output_dir) / f"plot_{safe_name}.png")
            self.render_plot_view(plot.name, path)
            paths.append(path)
        return paths

    def render_edge_map(self, view: CameraView, output_path: str) -> str:
        """渲染边缘图 (用于 ControlNet Canny 模式)

        白底黑线, 直接从 2.5D 投影绘制建筑轮廓
        """
        self.load_data()
        T = self._make_transform(view)
        w, h = view.width, view.height
        ox, oy = w // 2, h // 2

        img = Image.new("L", (w, h), 255)  # 白底
        draw = ImageDraw.Draw(img)

        for bld in self.buildings:
            # 只画顶面轮廓和底面外轮廓
            roof_pts = []
            base_pts = []
            for lng, lat in bld.footprint:
                sx, sy = self._project_3d(lng, lat, bld.height_m, T)
                roof_pts.append((ox + sx, oy + sy))
                sx2, sy2 = self._project_2d(lng, lat, T)
                base_pts.append((ox + sx2, oy + sy2))

            if len(roof_pts) >= 3:
                # 顶面轮廓 (较粗)
                draw.polygon(roof_pts, outline=30, width=2)
                # 底面轮廓 (较细)
                draw.polygon(base_pts, outline=60, width=1)
                # 连接顶面和底面的可见边
                if len(roof_pts) == len(base_pts):
                    for rpt, bpt in zip(roof_pts, base_pts):
                        draw.line([rpt, bpt], fill=45, width=1)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        logger.info(f"Edge map rendered: {output_path}")
        return output_path


# ══════════════════════════════════════════════════════════
# AIGC 生成管线集成
# ══════════════════════════════════════════════════════════

def build_consistent_aigc_prompt(style: str = "historic_renewal") -> tuple[str, str]:
    """构建统一的 AIGC 提示词 (保证所有出图风格一致)

    Returns:
        (positive_prompt, negative_prompt)
    """
    # 基于一致的风格基础, 根据场景微调
    style_additions = {
        "historic_renewal": (
            "historic district urban renewal, adaptive reuse of industrial heritage, "
            "mixed-use neighborhood, ground floor retail with residential above, "
            "pedestrian-friendly streetscape, green infrastructure, pocket parks, "
            "early 20th century warehouse conversion to creative offices, "
            "warm brick and limestone material palette, dark slate roofing, "
            "consistent across all views, architectural coherence enforced",
            ""
        ),
        "birdseye": (
            "aerial bird's eye view, isometric perspective, urban masterplan, "
            "city block scale, roof gardens visible, street network clearly defined, "
            "riverfront on east side, railway corridor on north, "
            "unified architectural language across all blocks",
            "distorted perspective, floating buildings, inconsistent building heights, "
            "missing river, extra roads"
        ),
        "street_view": (
            "street level perspective, eye level view, human scale, "
            "active street frontage, outdoor seating, street trees, "
            "consistent facade rhythm, uniform window proportions, "
            "cohesive material palette across all visible buildings",
            "empty streets, different building styles on same block, "
            "modern glass towers, suburban character"
        ),
    }

    pos = CONSISTENT_STYLE_PROMPT
    neg = CONSISTENT_NEGATIVE_PROMPT

    add = style_additions.get(style, style_additions["historic_renewal"])
    pos = pos + ", " + add[0] if add[0] else pos
    neg = neg + ", " + add[1] if add[1] else neg

    return pos, neg


def create_controlnet_payload(
    white_model_path: str,
    depth_map_path: str,
    edge_map_path: str,
    style: str = "historic_renewal",
) -> dict:
    """构建完整的 AIGC 请求 payload (本地 SD WebUI API 格式)

    供 SDPipeline 或 云端 API 使用
    """
    pos_prompt, neg_prompt = build_consistent_aigc_prompt(style)

    return {
        "prompt": pos_prompt,
        "negative_prompt": neg_prompt,
        "init_image": white_model_path,       # img2img 输入
        "denoising_strength": 0.45,            # 保留形态, 注入材质
        "width": 1024,
        "height": 768,
        "controlnet_units": [
            {
                "input_image": depth_map_path,
                "module": "depth",
                "model": "control_v11f1p_sd15_depth",
                "weight": 0.7,
                "guidance_start": 0.0,
                "guidance_end": 1.0,
            },
            {
                "input_image": edge_map_path,
                "module": "canny",
                "model": "control_v11p_sd15_canny",
                "weight": 0.5,
                "guidance_start": 0.0,
                "guidance_end": 0.8,
            },
        ],
    }
