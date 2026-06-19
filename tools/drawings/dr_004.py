# -*- coding: utf-8 -*-
import os
from pathlib import Path

import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

# Use the DR-013-style full-page layout instead of the standard A3 title frame.
NO_FRAME = True


def wrap_text(text, max_len=30):
    lines = []
    current = []
    width = 0
    for char in text:
        char_w = 2 if ord(char) > 127 else 1
        if char == "\n":
            lines.append("".join(current))
            current = []
            width = 0
            continue
        if width + char_w > max_len:
            lines.append("".join(current))
            current = [char]
            width = char_w
        else:
            current.append(char)
            width += char_w
    if current:
        lines.append("".join(current))
    return "\n".join(lines)


def _font(font_prop, size, weight="normal"):
    return fm.FontProperties(family=font_prop["family"], size=size, weight=weight)


DRAWING_METADATA = {
    "现状区位图": {
        "title": "现状区位图",
        "subtitle": "展示项目在长春市宽城区伪满皇宫周边的城市区位、交通联系、更新地块与周边蓝绿空间关系。",
        "card_title": "区位说明 / LOCATION ANALYSIS",
        "rows": [
            [
                "1. 城市区位",
                "项目位于长春市宽城区伪满皇宫邻近区域，西接长春站交通枢纽，东临伊通河生态廊道，是历史文化展示与站城更新转换的重要界面。"
            ],
            [
                "2. 场地范围",
                "研究范围约150公顷，北至长白路、南接长春大街、西临亚泰大街、东至东九条及伊通河沿线，覆盖老城居住、工业遗存与公共服务片区。"
            ],
            [
                "3. 更新指向",
                "重点更新地块沿铁路、光复路 and 博物院周边分布，承担补绿地、织慢行、修复风貌和植入公共服务的综合更新任务。"
            ]
        ],
        "legend_items": [
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"],
            ["现状建筑", "building"],
            ["城市水系", "water"],
            ["现状铁路", "rail"],
            ["城市道路", "road"]
        ]
    },
    "日照与风环境分析图": {
        "title": "日照与风环境分析图",
        "subtitle": "基于CFD风流场与日照时数模拟，评估街区微气候舒适度，指导建筑布局与绿化防风设计。",
        "card_title": "气候分析 / MICROCLIMATE ANALYSIS",
        "rows": [
            [
                "1. 风速分布",
                "夏季主导风向为西南风，冬季为主导西南偏西风。街区内部高层住宅群产生局地狭管效应，铁路割裂带风速较高。"
            ],
            [
                "2. 日照时数",
                "老旧住宅区大寒日日照时数普遍低于2小时，部分里弄阴影遮挡严重。更新应局部降低高度以释放被遮挡的日照。"
            ],
            [
                "3. 改善策略",
                "在西南季风上风向设置多层次林带防风，结合口袋公园与慢行廊道构建通风廊道，缓解街区热岛效应。"
            ]
        ],
        "legend_items": [
            ["主导风向 (西南风)", "arrow_blue"],
            ["日照充足区域", "sun_yellow"],
            ["风速高值区", "highlight_red"],
            ["绿化防风带", "green_dash"],
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"]
        ]
    },
    "案例借鉴与对标分析图": {
        "title": "案例借鉴与对标分析图",
        "subtitle": "对标国内外历史街区更新与铁路缝合的典型案例，提取本街区可借鉴的模式与经验。",
        "card_title": "对标分析 / CASE BENCHMARKING",
        "rows": [
            [
                "1. 铁路缝合案例",
                "借鉴首尔京义线森林公园、纽约高线公园，利用废弃/地面铁路廊道改造为线性口袋公园，连接两侧城市社区。"
            ],
            [
                "2. 历史文化活化",
                "对标北京杨梅竹斜街微更新、成都宽窄巷子，以历史肌理为基础进行小规模渐进式修缮，避免大拆大建。"
            ],
            [
                "3. 社区融合模式",
                "借鉴东京下北泽铁路地下化后空地开发，植入社区商业、全龄活动设施与艺术工坊，促进新旧居民交流融合。"
            ]
        ],
        "legend_items": [
            ["铁路缝合借鉴点", "bench_rail"],
            ["历史活化示范区", "bench_culture"],
            ["社区融合节点", "bench_community"],
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"],
            ["现状铁路", "rail"]
        ]
    },
    "功能分区与策划定位图": {
        "title": "功能分区与策划定位图",
        "subtitle": "明确“一核、一廊、三区”的空间功能结构，引导产业、文化与社区生活协同定位。",
        "card_title": "策划定位 / FUNCTIONAL STRATEGY",
        "rows": [
            [
                "1. 文化创意核",
                "以伪满皇宫博物院及周边里弄为核心，策划文旅消费、历史博览与艺术展示功能，形成区域活力发动机。"
            ],
            [
                "2. 站城融合过渡区",
                "西侧靠近长春站，定位为科创办公、现代商服与青年公寓集聚区，承接人流辐射，激发产业转型。"
            ],
            [
                "3. 品质社区生活区",
                "中北部与东侧依托工业遗产及老旧住宅区，置换活态市集、全龄共享社区与生态公园，补充公共服务短板。"
            ]
        ],
        "legend_items": [
            ["文化创意核心区", "zone_orange"],
            ["站城融合过渡区", "zone_cyan"],
            ["品质社区生活区", "zone_green"],
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"],
            ["现状铁路", "rail"]
        ]
    },
    "开发强度与容积率分区策略图": {
        "title": "开发强度与容积率分区策略图",
        "subtitle": "实施差异化的强度管控，重点历史地段“保低限高”，站城融合核心区“适度增容”。",
        "card_title": "容积率控制 / FAR DEVELOPMENT CONTROL",
        "rows": [
            [
                "1. 高强度发展区",
                "靠近长春站的站城融合板块，基底容积率控制在2.0-2.5，适度提高开发强度，实现高效紧凑的土地利用。"
            ],
            [
                "2. 中强度控制区",
                "生活社区更新区与商业市集地块，容积率限制在1.2-1.5，保障通风采光，塑造舒适的人居尺度。"
            ],
            [
                "3. 低强度保护区",
                "伪满皇宫保护红线及缓冲带，容积率限制在0.5以下，中国石油公园地块容积率限制在0.2以内，严格限制体量。"
            ]
        ],
        "legend_items": [
            ["低强度 (FAR≤0.5)", "far_low"],
            ["中强度 (0.5<FAR≤1.5)", "far_mid"],
            ["高强度 (FAR>1.5)", "far_high"],
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"],
            ["现状铁路", "rail"]
        ]
    },
    "天际线与视觉通廊控制图": {
        "title": "天际线与视觉通廊控制图",
        "subtitle": "构建朝向伪满皇宫和中车工业遗存的多条视觉廊道，保障天际线的视线完整与风貌视廊。",
        "card_title": "视廊控制 / VISUAL CORRIDORS CONTROL",
        "rows": [
            [
                "1. 视廊轴线控制",
                "设定长春站-伪满皇宫、光复路-伪满皇宫、东十条-中车老厂房三条主视廊，视线通道内新建限高9-12米。"
            ],
            [
                "2. 空间天际线",
                "沿亚泰大街向东逐渐降低，呈现“西高东低、外高内低”的渐进式天际线，保护伪满皇宫主体建筑的视觉背景。"
            ],
            [
                "3. 视点品质控制",
                "在口袋公园与慢行桥节点设置8处观景视点，严控视线范围内新建建筑的立面体量与色彩，避免杂乱背景。"
            ]
        ],
        "legend_items": [
            ["主视觉通廊 (视廊)", "sight_arrow"],
            ["关键观景点 (View)", "sight_dot"],
            ["视线敏感背景区", "sight_bg"],
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"],
            ["现状铁路", "rail"]
        ]
    },
    "竖向规划与排水分析图": {
        "title": "竖向规划与排水分析图",
        "subtitle": "结合现状海绵城市高程排水体系，优化地表径流路径，确保降雨汇水高效排入伊通河。",
        "card_title": "竖向与排水 / ELEVATION & DRAINAGE",
        "rows": [
            [
                "1. 高程地势分析",
                "整体地势呈西高东低、北高南低态势，最大高差约12米。东侧靠近伊通河属于低洼易涝边缘。"
            ],
            [
                "2. 雨水径流控制",
                "通过场地道路横坡与绿地微地形改造，理顺地表径流方向。规划设置3条主排水分区，向东汇入伊通河。"
            ],
            [
                "3. 海绵城市设施",
                "在5个口袋公园及铁路防护绿带内布置下凹式绿地、雨水花园与植草沟，实现原位蓄滞并降低峰值流量。"
            ]
        ],
        "legend_items": [
            ["排水流向 (向东)", "flow_arrow"],
            ["积水易涝风险点", "flood_dot"],
            ["海绵储水节点", "sponge_node"],
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"],
            ["现状铁路", "rail"]
        ]
    },
    "智慧城市与数字基础设施规划图": {
        "title": "智慧城市与数字基础设施规划图",
        "subtitle": "依托物联网感知网络与数字孪生底座，部署智慧安防、智能交通终端与环境监测节点。",
        "card_title": "智慧规划 / SMART INFRASTRUCTURE",
        "rows": [
            [
                "1. 智慧物联网络",
                "在5大重点地块及慢行通廊中规划部署智慧综合杆，集成5G微基站、视频监控与空气质量监测功能。"
            ],
            [
                "2. 数字孪生服务",
                "建立社区数字孪生数据汇聚中心，对建筑能耗、管网安全、人车流量进行实时映射与智能调度。"
            ],
            [
                "3. 绿色智慧设施",
                "在能量花园及各口袋公园配置太阳能智能座椅、无人清扫车充电点与智慧导览屏，提升社区科技感。"
            ]
        ],
        "legend_items": [
            ["智慧物联感知节点", "smart_node"],
            ["5G信号覆盖区", "smart_wifi"],
            ["数字孪生联络通道", "smart_line"],
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"],
            ["现状铁路", "rail"]
        ]
    },
    "投资估算与经济测算图": {
        "title": "投资估算与经济测算图",
        "subtitle": "进行片区更新的投资估算与资金平衡预测，确保项目的财务可行性与社会效益。",
        "card_title": "经济测算 / INVESTMENT & BALANCING",
        "rows": [
            [
                "1. 总投资分配",
                "项目总估算投资约8.5亿元，其中老旧住区微更新与老水产市场活化占比55%，市政基础设施提升占比25%。"
            ],
            [
                "2. 资金平衡路径",
                "通过商业活态市集租金、新能源驿站收益以及历史文创街区特许经营，实现“自我输血”与资金长期闭环。"
            ],
            [
                "3. 开发效益评估",
                "更新后释放商业面积约4.5万平方米，预计提供2000+就业岗位，带动周边物业增值约15%-20%。"
            ]
        ],
        "legend_items": [
            ["重点投资建设地块", "inv_orange"],
            ["绿地海绵投资区域", "inv_green"],
            ["老旧住宅改造提升", "inv_yellow"],
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"],
            ["现状铁路", "rail"]
        ]
    },
    "公众参与与博弈协商成果图": {
        "title": "公众参与与博弈协商成果图",
        "subtitle": "收集居民、商户及产权单位的核心诉求，通过多次博弈与方案协调达成多方共赢方案。",
        "card_title": "博弈协商 / COMMUNITY COLLABORATION",
        "rows": [
            [
                "1. 居民利益诉求",
                "期望增加口袋公园与适老设施，治理老旧住宅屋顶漏水与管道老化问题。方案为此增设了全龄社区与口袋公园。"
            ],
            [
                "2. 沿街商户博弈",
                "担忧更新期间施工影响生意，要求保留传统摊位风味。方案采用渐进式分期施工并保留老市集文脉。"
            ],
            [
                "3. 多方博弈成果",
                "石油公司同意出让闲置土地改造为开放式能量花园公园，政府提供政策奖励；中车老厂房活化引入产权单位入股。"
            ]
        ],
        "legend_items": [
            ["公众诉求聚焦区域", "pop_focus"],
            ["博弈协商置换地块", "pop_swap"],
            ["保留历史风味街区", "pop_keep"],
            ["规划研究范围", "outline_red"],
            ["重点更新地块", "outline_orange"],
            ["现状铁路", "rail"]
        ]
    }
}


def draw_custom_overlays(ax_map, drawing_type, key_plots, get_xy, font_prop):
    fig = ax_map.get_figure()
    centroids = []
    if key_plots is not None and not key_plots.empty:
        for idx in range(len(key_plots)):
            geom = key_plots.iloc[idx].geometry
            centroids.append((geom.centroid.x, geom.centroid.y))
    else:
        for lon, lat in [
            (125.3335, 43.9074),
            (125.3417, 43.9067),
            (125.3335, 43.9042),
            (125.347, 43.8999),
            (125.3365, 43.8981)
        ]:
            centroids.append(get_xy(lon, lat))

    if drawing_type == "日照与风环境 analysis 图" or drawing_type == "日照与风环境分析图":
        wind_lines = [
            [(125.325, 43.895), (125.34, 43.905)],
            [(125.335, 43.895), (125.35, 43.905)],
            [(125.34, 43.895), (125.355, 43.905)],
            [(125.32, 43.9), (125.335, 43.91)],
            [(125.33, 43.9), (125.345, 43.91)],
            [(125.34, 43.9), (125.355, 43.91)]
        ]
        for start_pt, end_pt in wind_lines:
            sx, sy = get_xy(*start_pt)
            ex, ey = get_xy(*end_pt)
            ax_map.annotate(
                "",
                xy=(ex, ey),
                xytext=(sx, sy),
                arrowprops=dict(
                    arrowstyle="->",
                    color="#3B82F6",
                    lw=2.5,
                    alpha=0.5,
                    connectionstyle="arc3,rad=0.15"
                )
            )

        sun_points = [(125.3417, 43.9067), (125.3365, 43.8981), (125.3335, 43.9042)]
        for lon, lat in sun_points:
            px, py = get_xy(lon, lat)
            ax_map.plot(px, py + 100, marker="o", color="#F59E0B", markersize=14, alpha=0.85, zorder=8)
            ax_map.plot(px, py + 100, marker="o", color="#FFFBEB", markersize=8, zorder=9)

    elif drawing_type == "案例借鉴与对标分析图":
        if len(centroids) >= 5:
            pts = [centroids[0], centroids[2], centroids[4]]
            xs, ys = zip(*pts)
            ax_map.plot(xs, ys, color="#8B5CF6", lw=3, linestyle="--", alpha=0.7, zorder=8)
            for idx, label in [(0, "线性森林缝合点"), (1, "商业活化借鉴"), (3, "社区融合试点")]:
                if idx < len(centroids):
                    cx, cy = centroids[idx]
                    txt = ax_map.text(
                        cx,
                        cy - 80,
                        label,
                        color="#7C3AED",
                        ha="center",
                        va="top",
                        fontproperties=_font(font_prop, 9, "bold"),
                        zorder=10
                    )
                    txt.set_path_effects([path_effects.withStroke(linewidth=2.5, foreground="#FFFFFF")])

    elif drawing_type == "功能分区与策划定位图":
        cx1, cy1 = get_xy(125.3422, 43.9036)
        circle1 = mpatches.Circle(
            (cx1, cy1),
            280,
            facecolor="#EF4444",
            edgecolor="#DC2626",
            linewidth=1.5,
            linestyle="--",
            alpha=0.15,
            zorder=5
        )
        ax_map.add_patch(circle1)
        txt1 = ax_map.text(
            cx1,
            cy1,
            "历史文化博览区",
            color="#DC2626",
            ha="center",
            va="center",
            fontproperties=_font(font_prop, 12, "bold"),
            zorder=10
        )
        txt1.set_path_effects([path_effects.withStroke(linewidth=3, foreground="#FFFFFF")])

        cx2, cy2 = get_xy(125.33, 43.906)
        circle2 = mpatches.Circle(
            (cx2, cy2),
            220,
            facecolor="#06B6D4",
            edgecolor="#0891B2",
            linewidth=1.5,
            linestyle="--",
            alpha=0.15,
            zorder=5
        )
        ax_map.add_patch(circle2)
        txt2 = ax_map.text(
            cx2,
            cy2 - 40,
            "站城商业办公区",
            color="#0891B2",
            ha="center",
            va="center",
            fontproperties=_font(font_prop, 12, "bold"),
            zorder=10
        )
        txt2.set_path_effects([path_effects.withStroke(linewidth=3, foreground="#FFFFFF")])

        cx3, cy3 = get_xy(125.348, 43.897)
        circle3 = mpatches.Circle(
            (cx3, cy3),
            260,
            facecolor="#10B981",
            edgecolor="#059669",
            linewidth=1.5,
            linestyle="--",
            alpha=0.15,
            zorder=5
        )
        ax_map.add_patch(circle3)
        txt3 = ax_map.text(
            cx3,
            cy3 + 40,
            "生态社区生活区",
            color="#059669",
            ha="center",
            va="center",
            fontproperties=_font(font_prop, 12, "bold"),
            zorder=10
        )
        txt3.set_path_effects([path_effects.withStroke(linewidth=3, foreground="#FFFFFF")])

    elif drawing_type == "开发强度与容积率分区策略图":
        far_vals = ["FAR=1.3", "FAR=1.4", "FAR=1.3", "FAR=1.3", "FAR=0.2"]
        far_colors = ["#FDE68A", "#FCA5A5", "#FDE68A", "#FDE68A", "#A7F3D0"]
        for idx, (cx, cy) in enumerate(centroids):
            if idx < len(far_vals):
                ax_map.plot(
                    cx,
                    cy,
                    marker="s",
                    color=far_colors[idx],
                    markersize=26,
                    markeredgecolor="#475569",
                    markeredgewidth=1.2,
                    zorder=8
                )
                txt = ax_map.text(
                    cx,
                    cy,
                    far_vals[idx],
                    color="#0F172A",
                    ha="center",
                    va="center",
                    fontproperties=_font(font_prop, 8.0, "bold"),
                    zorder=10
                )
                txt.set_path_effects([path_effects.withStroke(linewidth=1.5, foreground="#FFFFFF")])

    elif drawing_type == "天际线与视觉通廊控制图":
        pcx, pcy = get_xy(125.3422, 43.9036)
        destinations = [
            ("长春站方向", 125.325, 43.908),
            ("胜利公园方向", 125.326, 43.896),
            ("伊通河生态区", 125.359, 43.901)
        ]
        for name, lon, lat in destinations:
            dcx, dcy = get_xy(lon, lat)
            ax_map.annotate(
                "",
                xy=(dcx, dcy),
                xytext=(pcx, pcy),
                arrowprops=dict(arrowstyle="->", color="#EF4444", lw=2, linestyle="--", alpha=0.8)
            )
            txt = ax_map.text(
                (pcx + dcx) / 2,
                (pcy + dcy) / 2 + 50,
                "主要视觉廊道",
                color="#EF4444",
                ha="center",
                va="center",
                fontproperties=_font(font_prop, 10, "bold"),
                zorder=10
            )
            txt.set_path_effects([path_effects.withStroke(linewidth=2.5, foreground="#FFFFFF")])

    elif drawing_type == "竖向规划与排水分析图":
        flow_pts = [
            (125.33, 43.906),
            (125.335, 43.903),
            (125.34, 43.899),
            (125.345, 43.905),
            (125.35, 43.9),
            (125.348, 43.896)
        ]
        for lon, lat in flow_pts:
            sx, sy = get_xy(lon, lat)
            ex, ey = get_xy(lon + 0.005, lat - 0.001)
            ax_map.annotate(
                "",
                xy=(ex, ey),
                xytext=(sx, sy),
                arrowprops=dict(arrowstyle="->", color="#2563EB", lw=2.2, alpha=0.75)
            )

        elevations = [
            ("+156.2m", 125.328, 43.908),
            ("+149.8m", 125.342, 43.903),
            ("+144.5m", 125.358, 43.901)
        ]
        for label, lon, lat in elevations:
            px, py = get_xy(lon, lat)
            txt = ax_map.text(
                px,
                py + 80,
                label,
                color="#1E40AF",
                ha="center",
                va="bottom",
                fontproperties=_font(font_prop, 10, "bold"),
                zorder=10
            )
            txt.set_path_effects([path_effects.withStroke(linewidth=2.5, foreground="#FFFFFF")])

    elif drawing_type == "智慧城市与数字基础设施规划图":
        for idx, (cx, cy) in enumerate(centroids):
            for r in [80, 160]:
                circle = mpatches.Circle(
                    (cx, cy),
                    r,
                    fill=False,
                    edgecolor="#06B6D4",
                    linewidth=0.8,
                    alpha=0.25,
                    linestyle="--",
                    zorder=5
                )
                ax_map.add_patch(circle)
            ax_map.plot(
                cx,
                cy,
                marker="o",
                color="#06B6D4",
                markersize=12,
                markeredgecolor="#FFFFFF",
                markeredgewidth=1.5,
                zorder=8
            )

        for i in range(len(centroids)):
            for j in range(i + 1, len(centroids)):
                dist = np.hypot(centroids[i][0] - centroids[j][0], centroids[i][1] - centroids[j][1])
                if dist < 1200:
                    ax_map.plot(
                        [centroids[i][0], centroids[j][0]],
                        [centroids[i][1], centroids[j][1]],
                        color="#0891B2",
                        lw=1.2,
                        linestyle=":",
                        alpha=0.6,
                        zorder=6
                    )

    elif drawing_type == "投资估算与经济测算图":
        inv_labels = ["1.8亿元", "3.2亿元", "1.5亿元", "1.2亿元", "0.8亿元"]
        for idx, (cx, cy) in enumerate(centroids):
            if idx < len(inv_labels):
                ax_map.plot(cx, cy, marker="o", color="#F97316", markersize=14, zorder=8)
                txt = ax_map.text(
                    cx,
                    cy + 90,
                    f"估算投资:\n{inv_labels[idx]}",
                    color="#C2410C",
                    ha="center",
                    va="bottom",
                    fontproperties=_font(font_prop, 9, "bold"),
                    zorder=10
                )
                txt.set_path_effects([path_effects.withStroke(linewidth=2.5, foreground="#FFFFFF")])

    elif drawing_type == "公众参与与博弈协商成果图":
        quotes = [
            ("老水产地块：\n'保留历史铁轨与红砖厂房！'", 125.3335, 43.9074, "left"),
            ("食品调料地块：\n'保留老市集文脉与风味摊位！'", 125.3417, 43.9067, "right"),
            ("一中北侧地块：\n'多建适老化与口袋公园设施！'", 125.3335, 43.9042, "left"),
            ("中国石油地块：\n'将加油站改造为开放绿地！'", 125.3365, 43.8981, "right")
        ]
        for q, lon, lat, align in quotes:
            px, py = get_xy(lon, lat)
            ha = "left" if align == "left" else "right"
            offset = 120 if align == "left" else -120
            ax_map.plot(px, py, marker="o", color="#EF4444", markersize=8, zorder=8)
            txt = ax_map.text(
                px + offset,
                py + 120,
                q,
                color="#991B1B",
                ha=ha,
                va="center",
                fontproperties=_font(font_prop, 9.5, "bold"),
                zorder=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#FCA5A5", lw=1.0, alpha=0.9)
            )
            ax_map.plot([px, px + offset], [py, py + 120], color="#FCA5A5", lw=1.2, zorder=7)

    # Try loading windrose if exists
    try:
        from PIL import Image as _PIL_Image
        from pathlib import Path as _Path
        _assets_dir = _Path(__file__).resolve().parent.parent.parent / "assets"
        _rose_path = _assets_dir / "长春市风玫瑰.png"
        if _rose_path.exists():
            ax_rose = fig.add_axes(
                [0.615188799321171, 0.725, 0.08485362749257531, 0.12],
                facecolor="none",
                zorder=4
            )
            ax_rose.set_axis_off()
            _y_g, _x_g = np.ogrid[-1:1:100j, -1:1:100j]
            _r = np.sqrt(_x_g**2 + _y_g**2)
            _alpha = np.clip(1.0 - _r, 0, 1) * 0.5
            _grad_img = np.ones((100, 100, 4))
            _grad_img[..., 3] = _alpha
            ax_rose.imshow(_grad_img, zorder=0, extent=(0, 1, 0, 1), origin="lower")
            _rose_img = _PIL_Image.open(_rose_path).convert("RGBA")
            _rose_data = np.array(_rose_img)
            _rose_data[..., 0] = 0
            _rose_data[..., 1] = 0
            _rose_data[..., 2] = 0
            _black_rose_img = _PIL_Image.fromarray(_rose_data)
            ax_rose.imshow(_black_rose_img, zorder=1)
    except Exception as e:
        print(f"Error loading wind rose in {__file__}: {e}")


def draw_map(
    ax,
    roads,
    buildings,
    water,
    rails,
    key_plots,
    landuse,
    boundary,
    cx,
    cy,
    view_w,
    view_h,
    get_xy,
    font_prop,
    *args,
    **kwargs
):
    fig = ax.get_figure()
    params = kwargs.get("params", {})
    drawing_type = params.get("drawing_type", "现状区位图")

    if drawing_type not in DRAWING_METADATA:
        matched = False
        for k in DRAWING_METADATA.keys():
            if k in drawing_type or drawing_type in k:
                drawing_type = k
                matched = True
                break
        if not matched:
            drawing_type = "现状区位图"

    meta = DRAWING_METADATA[drawing_type]

    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)
    ax.set_axis_off()

    # Match DR-013: light drawing grid, full-page composition, no standard title frame.
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color="#E2E8F0", linewidth=0.6, alpha=0.5, zorder=0)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color="#E2E8F0", linewidth=0.6, alpha=0.5, zorder=0)

    # Header, using DR-013 type scale.
    ax.add_patch(
        mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor="#E2E8F0", edgecolor="none", zorder=1)
    )
    ax.add_patch(
        mpatches.Rectangle(
            (2.0, 89.0),
            136.8,
            7.3,
            facecolor="#FFFFFF",
            edgecolor="#CBD5E1",
            linewidth=1.2,
            zorder=2
        )
    )
    ax.add_patch(
        mpatches.Rectangle((2.0, 95.7), 136.8, 0.6, facecolor="#D97706", edgecolor="none", zorder=3)
    )
    ax.text(
        3.5,
        93.6,
        meta["title"],
        color="#0F172A",
        ha="left",
        va="center",
        fontproperties=_font(font_prop, 26, "bold"),
        zorder=4
    )
    ax.text(
        3.5,
        90.7,
        meta["subtitle"],
        color="#334155",
        ha="left",
        va="center",
        fontproperties=_font(font_prop, 15.0),
        zorder=4
    )

    # Main map on the left.
    ax.add_patch(
        mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor="#E2E8F0", edgecolor="none", zorder=1)
    )
    ax.add_patch(
        mpatches.Rectangle(
            (2.0, 4.0),
            98.0,
            83.0,
            facecolor="#FFFFFF",
            edgecolor="#CBD5E1",
            linewidth=1.2,
            zorder=2
        )
    )
    ax_map = fig.add_axes(
        [3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0],
        facecolor="#F8FAFC",
        zorder=3
    )
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=0.18, zorder=2)
    if roads is not None and not roads.empty:
        for lvl, lw in [(1, 3.8), (2, 3.0), (3, 2.2), (4, 1.6)]:
            sub_gdf = roads[roads["level"] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(
                    ax=ax_map,
                    color="#94A3B8",
                    linewidth=lw,
                    capstyle="round",
                    joinstyle="round",
                    zorder=3
                )
        for lvl, lw in [(1, 2.6), (2, 2.0), (3, 1.2), (4, 0.8)]:
            sub_gdf = roads[roads["level"] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(
                    ax=ax_map,
                    color="#E2E8F0",
                    linewidth=lw,
                    capstyle="round",
                    joinstyle="round",
                    zorder=4
                )
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#475569", linewidth=1.8, linestyle=(0, (6, 6)), zorder=5)
    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax_map, facecolor="#F59E0B", edgecolor="#D97706", linewidth=1.6, alpha=0.42, zorder=6)
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=7)

    labels = [
        ("长春站", 125.3250, 43.9080),
        ("伪满皇宫博物院", 125.3422, 43.9036),
        ("光复路", 125.3475, 43.9017),
        ("伊通河沿岸公园", 125.3590, 43.9010),
        ("胜利公园", 125.3260, 43.8960),
    ]
    for name, lon, lat in labels:
        px, py = get_xy(lon, lat)
        ax_map.plot(
            px,
            py,
            marker="o",
            markersize=8,
            color="#FF9500",
            markeredgecolor="#FFFFFF",
            markeredgewidth=1.6,
            zorder=9
        )
        txt = ax_map.text(
            px,
            py + 70,
            name,
            color="#0F172A",
            ha="center",
            va="bottom",
            fontproperties=_font(font_prop, 12, "bold"),
            zorder=10
        )
        txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground="#FFFFFF")])

    draw_custom_overlays(ax_map, drawing_type, key_plots, get_xy, font_prop)

    hide_right_panels = os.environ.get("HIDE_RIGHT_PANELS") == "1"
    if not hide_right_panels:
        # Right legend card.
        ax.add_patch(
            mpatches.Rectangle(
                (101.8, 66.7),
                37.9,
                20.3,
                facecolor="#E2E8F0",
                edgecolor="none",
                zorder=1
            )
        )
        ax.add_patch(
            mpatches.Rectangle(
                (101.5, 67.0),
                37.9,
                20.3,
                facecolor="#FFFFFF",
                edgecolor="#CBD5E1",
                linewidth=1.2,
                zorder=2
            )
        )
        ax.add_patch(
            mpatches.Rectangle(
                (101.5, 85.8),
                37.9,
                1.5,
                facecolor="#D97706",
                edgecolor="none",
                zorder=3
            )
        )
        ax.text(
            103.5,
            82.8,
            "图例 / LEGEND",
            color="#D97706",
            ha="left",
            va="center",
            fontproperties=_font(font_prop, 13.5, "bold"),
            zorder=4
        )

        for i, (label, style) in enumerate(meta["legend_items"]):
            x = 103.5 + (i % 2) * 18.0
            y = 80.0 - (i // 2) * 3.3

            if style == "outline_red":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="none",
                        edgecolor="#FF3B30",
                        linewidth=1.8,
                        zorder=4
                    )
                )
            elif style == "outline_orange":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="none",
                        edgecolor="#F59E0B",
                        linewidth=1.8,
                        zorder=4
                    )
                )
            elif style == "outline_blue":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="none",
                        edgecolor="#2563EB",
                        linewidth=1.8,
                        zorder=4
                    )
                )
            elif style == "building":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#F8FAFC",
                        edgecolor="#CBD5E1",
                        linewidth=1.0,
                        zorder=4
                    )
                )
            elif style == "water":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#D0E6F7",
                        edgecolor="none",
                        zorder=4
                    )
                )
            elif style == "rail":
                ax.plot(
                    [x, x + 2.7],
                    [y, y],
                    color="#475569",
                    linewidth=1.8,
                    linestyle=(0, (5, 4)),
                    zorder=4
                )
            elif style == "road":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.55),
                        2.7,
                        1.1,
                        facecolor="#E2E8F0",
                        edgecolor="none",
                        zorder=4
                    )
                )
            elif style == "arrow_blue":
                ax.annotate(
                    "",
                    xy=(x + 2.7, y),
                    xytext=(x, y),
                    arrowprops=dict(arrowstyle="->", color="#3B82F6", lw=2, zorder=4)
                )
            elif style == "sun_yellow":
                ax.plot(x + 1.35, y, marker="o", markersize=6, color="#F59E0B", zorder=4)
            elif style == "highlight_red":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#EF4444",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )
            elif style == "green_dash":
                ax.plot(
                    [x, x + 2.7],
                    [y, y],
                    color="#10B981",
                    linewidth=2.0,
                    linestyle="--",
                    zorder=4
                )
            elif style == "bench_rail":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#8B5CF6",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )
            elif style == "bench_culture":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#F97316",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )
            elif style == "bench_community":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#10B981",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )
            elif style == "zone_orange":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#F97316",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )
            elif style == "zone_cyan":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#06B6D4",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )
            elif style == "zone_green":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#10B981",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )
            elif style == "far_low":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#A7F3D0",
                        edgecolor="#475569",
                        linewidth=1.0,
                        zorder=4
                    )
                )
            elif style == "far_mid":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#FDE68A",
                        edgecolor="#475569",
                        linewidth=1.0,
                        zorder=4
                    )
                )
            elif style == "far_high":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#FCA5A5",
                        edgecolor="#475569",
                        linewidth=1.0,
                        zorder=4
                    )
                )
            elif style == "sight_arrow":
                ax.plot(
                    [x, x + 2.7],
                    [y, y],
                    color="#EF4444",
                    linewidth=1.5,
                    linestyle="--",
                    zorder=4
                )
            elif style == "sight_dot":
                ax.plot(x + 1.35, y, marker="o", markersize=6, color="#EF4444", zorder=4)
            elif style == "sight_bg":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#FECACA",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )
            elif style == "flow_arrow":
                ax.annotate(
                    "",
                    xy=(x + 2.7, y),
                    xytext=(x, y),
                    arrowprops=dict(arrowstyle="->", color="#2563EB", lw=2, zorder=4)
                )
            elif style == "flood_dot":
                ax.plot(
                    x + 1.35,
                    y,
                    marker="x",
                    markersize=6,
                    color="#EF4444",
                    markeredgewidth=1.8,
                    zorder=4
                )
            elif style == "sponge_node":
                ax.plot(x + 1.35, y, marker="o", markersize=6, color="#2563EB", zorder=4)
            elif style == "smart_node":
                ax.plot(x + 1.35, y, marker="o", markersize=6, color="#06B6D4", zorder=4)
            elif style == "smart_wifi":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#CFFAFE",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )
            elif style == "smart_line":
                ax.plot(
                    [x, x + 2.7],
                    [y, y],
                    color="#0891B2",
                    linewidth=1.2,
                    linestyle=":",
                    zorder=4
                )
            elif style == "inv_orange":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#FFEDD5",
                        edgecolor="#F97316",
                        linewidth=1.0,
                        zorder=4
                    )
                )
            elif style == "inv_green":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#D1FAE5",
                        edgecolor="#10B981",
                        linewidth=1.0,
                        zorder=4
                    )
                )
            elif style == "inv_yellow":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#FEF3C7",
                        edgecolor="#F59E0B",
                        linewidth=1.0,
                        zorder=4
                    )
                )
            elif style == "pop_focus":
                ax.plot(
                    x + 1.35,
                    y,
                    marker="o",
                    markersize=6,
                    color="#EF4444",
                    fillstyle="none",
                    markeredgewidth=1.5,
                    zorder=4
                )
            elif style == "pop_swap":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="none",
                        edgecolor="#F59E0B",
                        linewidth=1.0,
                        linestyle="--",
                        zorder=4
                    )
                )
            elif style == "pop_keep":
                ax.add_patch(
                    mpatches.Rectangle(
                        (x, y - 0.8),
                        2.7,
                        1.7,
                        facecolor="#C084FC",
                        edgecolor="none",
                        alpha=0.6,
                        zorder=4
                    )
                )

            ax.text(
                x + 3.6,
                y,
                label,
                color="#334155",
                ha="left",
                va="center",
                fontproperties=_font(font_prop, 13.5),
                zorder=4
            )

        scale_len = 500 / (view_w / 96.0)
        x_start = 120.45 - scale_len / 2
        x_end = x_start + scale_len
        y_bar = 68.7
        ax.plot([x_start, x_end], [y_bar, y_bar], color="#0F172A", linewidth=1.5, zorder=4)
        for x in [x_start, x_start + scale_len / 2, x_end]:
            ax.plot([x, x], [y_bar - 0.8, y_bar + 0.8], color="#0F172A", linewidth=1.5, zorder=4)
        ax.text(
            x_start,
            70.5,
            "0",
            color="#334155",
            ha="center",
            va="center",
            fontproperties=_font(font_prop, 11),
            zorder=4
        )
        ax.text(
            x_start + scale_len / 2,
            70.5,
            "250m",
            color="#334155",
            ha="center",
            va="center",
            fontproperties=_font(font_prop, 11),
            zorder=4
        )
        ax.text(
            x_end,
            70.5,
            "500m",
            color="#334155",
            ha="center",
            va="center",
            fontproperties=_font(font_prop, 11),
            zorder=4
        )
        scale_ratio = view_w / 0.31968
        scale_rounded = int(round(scale_ratio / 500)) * 500
        ax.text(
            (x_start + x_end) / 2,
            67.4,
            f"比例尺 1:{scale_rounded}",
            color="#334155",
            ha="center",
            va="center",
            fontproperties=_font(font_prop, 11, "bold"),
            zorder=4
        )

        # Right explanation card.
        ax.add_patch(
            mpatches.Rectangle(
                (101.8, 3.7),
                37.9,
                61.3,
                facecolor="#E2E8F0",
                edgecolor="none",
                zorder=1
            )
        )
        ax.add_patch(
            mpatches.Rectangle(
                (101.5, 4.0),
                37.9,
                61.3,
                facecolor="#FFFFFF",
                edgecolor="#CBD5E1",
                linewidth=1.2,
                zorder=2
            )
        )
        ax.add_patch(
            mpatches.Rectangle(
                (101.5, 63.8),
                37.9,
                1.5,
                facecolor="#D97706",
                edgecolor="none",
                zorder=3
            )
        )
        ax.text(
            103.5,
            61.0,
            meta["card_title"],
            color="#D97706",
            ha="left",
            va="center",
            fontproperties=_font(font_prop, 13.5, "bold"),
            zorder=4
        )

        y = 56.0
        for title, body in meta["rows"]:
            ax.text(
                103.5,
                y,
                title,
                color="#0F172A",
                ha="left",
                va="top",
                fontproperties=_font(font_prop, 15.0, "bold"),
                zorder=4
            )
            y -= 2.5
            for line in wrap_text(body, 44).split("\n"):
                ax.text(
                    103.5,
                    y,
                    line,
                    color="#334155",
                    ha="left",
                    va="top",
                    fontproperties=_font(font_prop, 15.0),
                    zorder=4
                )
                y -= 2.85
            y -= 2.2
