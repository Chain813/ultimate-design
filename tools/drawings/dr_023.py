"""DR-059: 综合现状问题诊断图 — 四大问题汇总诊断与问题热点标注"""
from pathlib import Path

import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

NO_FRAME = True

def wrap_text(text, max_len=44):
    forbidden_start = set("，。、；：？！）】』」》〉〕”’）,.?!;:)】")
    forbidden_end = set("（【『「《〈〔“‘（([【")
    
    def char_width(c):
        return 2 if ord(c) > 127 else 1

    lines = []
    for part in text.split('\n'):
        if not part:
            lines.append("")
            continue
        current_line = ""
        current_w = 0
        i = 0
        while i < len(part):
            char = part[i]
            w = char_width(char)
            if current_w + w <= 44:
                current_line += char
                current_w += w
                i += 1
            else:
                if not current_line:
                    current_line = char
                    current_w = w
                    i += 1
                else:
                    if part[i] in forbidden_start:
                        current_line += part[i]
                        i += 1
                        while i < len(part) and part[i] in forbidden_start:
                            current_line += part[i]
                            i += 1
                    while current_line and current_line[-1] in forbidden_end:
                        i -= 1
                        current_line = current_line[:-1]
                if current_line:
                    lines.append(current_line)
                current_line = ""
                current_w = 0
        if current_line:
            lines.append(current_line)
    return '\n'.join(lines)
FOUR_ISSUES = [
    {
        "id": "01",
        "title": "功能混杂与低效用地",
        "color": "#EF4444",
        "icon": "▮",
        "desc": "研究区现状以低效批发仓储、零散工业为主，用地混合度高但产出能级低，与城市核心区位价值严重错配。",
        "hotspots": [
            ("农贸水产市场", 125.3335, 43.9074),
            ("食品调料大市场", 125.3418, 43.9067),
        ]
    },
    {
        "id": "02",
        "title": "交通割裂与可达性不足",
        "color": "#F59E0B",
        "icon": "▬",
        "desc": "京哈铁路与亚泰快速路形成双重物理割裂，内部路网整合度低，步行系统断点多达12处。",
        "hotspots": [
            ("铁路割裂带", 125.3380, 43.9080),
            ("亚泰快速路屏障", 125.3505, 43.8985),
        ]
    },
    {
        "id": "03",
        "title": "社区老化与配套缺失",
        "color": "#8B5CF6",
        "icon": "●",
        "desc": "片区老龄化率超30%，适老化设施500米服务半径覆盖不足，社区级绿地与公共空间严重匮乏。",
        "hotspots": [
            ("市一中北侧老旧社区", 125.3335, 43.9042),
            ("清禾集贸市场周边", 125.3470, 43.8999),
        ]
    },
    {
        "id": "04",
        "title": "环境品质与风貌失序",
        "color": "#0EA5E9",
        "icon": "◆",
        "desc": "全域平均绿视率仅8.7%，78.3%采样点低于15%宜居阈值；历史建筑与杂乱搭建混杂，风貌管控失位。",
        "hotspots": [
            ("中国石油周边硬质化", 125.3365, 43.8981),
            ("长春大街沿线", 125.3406, 43.8925),
        ]
    }
]


def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, *args, **kwargs):
    fig = ax.get_figure()

    # 1. Setup A3 Main Canvas
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)

    # Background grid
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)

    # 2. Header Card
    header_shadow = mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    header_bg = mpatches.Rectangle((2, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(header_shadow)
    ax.add_patch(header_bg)
    accent_bar = mpatches.Rectangle((2, 95.7), 136.8, 0.6, facecolor='#DC2626', edgecolor='none', zorder=3)
    ax.add_patch(accent_bar)

    ax.text(3.5, 93.6, "综合现状问题诊断图",
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    ax.text(3.5, 90.7, "汇总功能混杂、交通割裂、社区老化、环境失序四大核心问题，标注空间热点分布，形成更新策略的直接依据。",
            color='#334155', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)

    # 3. Map Container
    map_shadow = mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    map_bg = mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(map_shadow)
    ax.add_patch(map_bg)

    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    # 3b. Base Layers
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#E2F0FD", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=0.2, alpha=0.7, zorder=0.8)
    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 2.2, "#475569"), (2, 1.6, "#64748B"), (3, 1.1, "#94A3B8"), (4, 0.7, "#CBD5E1")]:
            sub = roads[roads['level'] == lvl]
            if not sub.empty:
                sub.plot(ax=ax_map, color=color, linewidth=lw, zorder=2.0)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#1E293B", linewidth=1.5, linestyle=(0, (5, 5)), zorder=2.5)
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5.0)

    # 3c. Plot Four Issue Hotspots
    for issue in FOUR_ISSUES:
        for name, lon, lat in issue["hotspots"]:
            px, py = get_xy(lon, lat)
            # Glow effect
            ax_map.plot(px, py, marker='o', markersize=28.0, color=issue["color"], alpha=0.15, zorder=5.5)
            ax_map.plot(px, py, marker='o', markersize=18.0, color=issue["color"], alpha=0.25, zorder=5.6)
            # Core marker
            ax_map.plot(px, py, marker='o', markersize=12.0, color='#FFFFFF', alpha=0.9, zorder=5.7)
            ax_map.plot(px, py, marker='s', markersize=7.0, color=issue["color"],
                        markeredgecolor='#FFFFFF', markeredgewidth=1.0, zorder=6.0)
            # Label
            txt = ax_map.text(px, py + 55, name, color=issue["color"], ha='center', va='bottom',
                              fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=10.0), zorder=6.5)
            txt.set_path_effects([path_effects.withStroke(linewidth=3.0, foreground='#FFFFFF')])

    # Windrose
    rose_path = ASSETS_DIR / "长春市风玫瑰.png"
    if rose_path.exists():
        try:
            ax_rose = fig.add_axes([87.0 / 141.42, 72.5 / 100.0, 12.0 / 141.42, 12.0 / 100.0], facecolor='none', zorder=4)
            ax_rose.set_axis_off()
            y_g, x_g = np.ogrid[-1:1:100j, -1:1:100j]
            r = np.sqrt(x_g**2 + y_g**2)
            alpha = np.clip(1.0 - r, 0, 1) * 0.50
            grad_img = np.ones((100, 100, 4))
            grad_img[..., 3] = alpha
            ax_rose.imshow(grad_img, zorder=0, extent=[0, 1, 0, 1], origin='lower')
            rose_img = Image.open(rose_path).convert("RGBA")
            rose_data = np.array(rose_img)
            rose_data[..., 0] = 0
            rose_data[..., 1] = 0
            rose_data[..., 2] = 0
            ax_rose.imshow(Image.fromarray(rose_data), zorder=1)
        except Exception:
            pass

    # 4. Four Issue Cards (Right side, X: 101.5 to 139.4)
    card_h = 18.5
    gap = 1.5
    y_start = 85.5

    for i, issue in enumerate(FOUR_ISSUES):
        y_top = y_start - i * (card_h + gap)
        # Card background
        card_shadow = mpatches.Rectangle((101.8, y_top - card_h + 0.3), 37.9, card_h, facecolor='#E2E8F0', edgecolor='none', zorder=1)
        card_bg = mpatches.Rectangle((101.5, y_top - card_h + 0.0), 37.9, card_h, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
        ax.add_patch(card_shadow)
        ax.add_patch(card_bg)
        # Left color bar
        color_bar = mpatches.Rectangle((101.5, y_top - card_h + 0.0), 0.8, card_h, facecolor=issue["color"], edgecolor='none', zorder=3)
        ax.add_patch(color_bar)

        # Issue number badge
        ax.text(104.0, y_top - 2.0, issue["id"], color='#FFFFFF', ha='center', va='center',
                fontproperties=fm.FontProperties(family='Arial', weight='bold', size=16), zorder=5,
                bbox=dict(boxstyle="round,pad=0.3", facecolor=issue["color"], edgecolor='none'))

        # Title
        ax.text(107.0, y_top - 2.0, issue["title"], color='#0F172A', ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=14), zorder=4)

        # Description
        wrapped = wrap_text(issue["desc"], max_len=42)
        y_desc = y_top - 5.5
        for line in wrapped.split('\n'):
            ax.text(104.0, y_desc, line, color='#475569', ha='left', va='center',
                    fontproperties=fm.FontProperties(family=font_prop['family'], size=12.0), zorder=4)
            y_desc -= 2.8

        # Hotspot labels
        for name, _lon, _lat in issue["hotspots"]:
            ax.text(104.0, y_desc, f"📍 {name}", color=issue["color"], ha='left', va='center',
                    fontproperties=fm.FontProperties(family=font_prop['family'], size=10.5), zorder=4)
            y_desc -= 2.5


legend_items = []
description_lines = []
