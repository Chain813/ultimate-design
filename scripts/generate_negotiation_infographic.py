# -*- coding: utf-8 -*-
"""scripts/generate_negotiation_infographic.py

Generates a high-resolution 1920x1080 infographic card summarizing the 
multi-agent planning negotiation process, saved to static/negotiation_infographic.png.
Now with white-mode layout, grid background, and dynamic text alignment.
"""

import os
import json
import re
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Rectangle

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def wrap_text(text, width=32):
    """Wraps Chinese text to a given character width."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)  # Strip any html tags
    lines = []
    current = ""
    for char in text:
        current += char
        # Estimate width: Chinese characters weigh 2, English 1
        current_len = sum(2 if ord(c) > 127 else 1 for c in current)
        if current_len >= width or char == '\n':
            lines.append(current.strip())
            current = ""
    if current:
        lines.append(current.strip())
    return "\n".join(lines)

def main():
    print("==================================================")
    print("🎨 开始生成博弈协商沙盘高分辨率白底图...")
    print("==================================================")

    # Configure Matplotlib fonts for Chinese support
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Segoe UI Black', 'DejaVu Sans', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    
    # Load cache
    cache_path = ROOT / "output" / "stage_bus_cache.json"
    if not cache_path.exists():
        print("错误: output/stage_bus_cache.json 不存在！请先运行 scripts/run_real_negotiation.py。")
        sys.exit(1)

    with open(cache_path, "r", encoding="utf-8") as f:
        cache_data = json.load(f)

    # Load dialogues and scores
    dialogues = cache_data.get("07_negotiation_dialogues", [])
    voting_scores = cache_data.get("07_voting_scores", {
        "👥 居民代表（老王）": 98.0,
        "💰 文旅运营商（赵总）": 98.0,
        "📐 规划师（李工）": 99.0
    })
    strategy_matrix = cache_data.get("07_strategy_matrix", "")

    # Define color palette (light mode theme)
    bg_color = "#F8FAFC"      # slate-50
    card_color = "#FFFFFF"    # white
    border_color = "#E2E8F0"  # slate-200
    text_main = "#0F172A"     # slate-900
    text_muted = "#475569"    # slate-600
    
    color_gold = "#D97706"    # amber-600
    color_emerald = "#059669" # emerald-600
    color_indigo = "#4F46E5"  # indigo-600

    # Initialize Figure (1920x1080 at 150 DPI)
    fig = plt.figure(figsize=(19.2, 10.8), dpi=150, facecolor=bg_color)
    
    # Draw grid background to match A3 sheets style
    ax_bg = fig.add_axes([0, 0, 1, 1], facecolor="none", zorder=0)
    ax_bg.axis('off')
    ax_bg.set_xlim(0, 1)
    ax_bg.set_ylim(0, 1)
    
    grid_spacing = 0.05
    for x in range(1, int(1.0 / grid_spacing)):
        ax_bg.plot([x * grid_spacing, x * grid_spacing], [0, 1], color="#E2E8F0", linewidth=0.5, zorder=0)
    for y in range(1, int(1.0 / grid_spacing)):
        ax_bg.plot([0, 1], [y * grid_spacing, y * grid_spacing], color="#E2E8F0", linewidth=0.5, zorder=0)

    # Draw double border frame around canvas
    ax_bg.plot([0.02, 0.98, 0.98, 0.02, 0.02], [0.02, 0.02, 0.98, 0.98, 0.02], color="#CBD5E1", linewidth=1.5, zorder=1)
    ax_bg.plot([0.022, 0.978, 0.978, 0.022, 0.022], [0.022, 0.022, 0.978, 0.978, 0.022], color="#CBD5E1", linewidth=0.5, zorder=1)

    # Header block card
    fig.text(0.04, 0.93, "数字孪生 · 古今共振 | 伪满皇宫周边地区更新设计", color=text_muted, fontsize=11, weight="medium")
    fig.text(0.04, 0.88, "多主体协同规划博弈协商成果图 (示意图)", color=text_main, fontsize=24, weight="bold")
    
    # Divider line under title
    fig.add_artist(plt.Line2D([0.04, 0.96], [0.86, 0.86], color="#94A3B8", linewidth=1.5))

    # GridSpec Layout
    gs = gridspec.GridSpec(1, 3, left=0.04, right=0.96, bottom=0.05, top=0.83, wspace=0.18)

    # ── Left Column: Stakeholder Profiles ──
    ax_left = fig.add_subplot(gs[0, 0])
    ax_left.set_facecolor(bg_color)
    ax_left.axis('off')
    
    ax_left.text(0.0, 0.98, "一、参与主体与核心利益诉求", color=text_main, fontsize=14, weight="bold")
    
    stakeholders = [
        {
            "title": "🏠 居民代表 (老王)",
            "color": color_gold,
            "desc": "在铁北生活了30年的老居民。高度关注日常采光、无障碍出行及社区口袋公园、菜市场配套。希望改造能大幅改善基础设施，同时避免噪声与过度商业化打扰日常安宁。",
            "y": 0.68
        },
        {
            "title": "💰 文旅运营商 (赵总)",
            "color": color_emerald,
            "desc": "代表开发与活化运营方。致力于发掘伪满皇宫周边文化IP潜力，倡导导入文创主力店、特色民宿与沉浸式街区商业。在不碰规划红线的前提下，关注开发容积率以确保项目可持续闭环。",
            "y": 0.38
        },
        {
            "title": "📐 专业规划师 (李工)",
            "color": color_indigo,
            "desc": "代表规划编制与法定合规控制方。遵循《长春市历史文化名城保护条例》，严控建筑高度与伪满皇宫风貌视廊。主张采用渐进式微更新策略，在满足居民民生诉求的同时，为运营方预留合理盈利空间。",
            "y": 0.08
        }
    ]

    for sh in stakeholders:
        # Draw card container
        card = FancyBboxPatch((0.0, sh["y"]), 0.95, 0.25, boxstyle="round,pad=0.02", 
                              fc=card_color, ec=border_color, lw=1.2, transform=ax_left.transData)
        ax_left.add_patch(card)
        
        # Color bar
        ax_left.plot([0.01, 0.01], [sh["y"]+0.03, sh["y"]+0.21], color=sh["color"], lw=4.5, solid_capstyle="round")
        
        # Text
        ax_left.text(0.04, sh["y"]+0.18, sh["title"], color=sh["color"], fontsize=12, weight="bold")
        ax_left.text(0.04, sh["y"]+0.03, wrap_text(sh["desc"], 38), color=text_muted, fontsize=9.5, linespacing=1.6)

    # ── Middle Column: Dialogue Timeline ──
    ax_mid = fig.add_subplot(gs[0, 1])
    ax_mid.set_facecolor(bg_color)
    ax_mid.axis('off')
    
    ax_mid.text(0.0, 0.98, "二、三轮多主体博弈协商历程", color=text_main, fontsize=14, weight="bold")
    
    # Group dialogues by round
    rounds_data = {}
    for d in dialogues:
        r = d.get("round_label", "第一轮")
        if r not in rounds_data:
            rounds_data[r] = []
        rounds_data[r].append(d)

    round_y = [0.68, 0.38, 0.08]
    round_labels = ["第一轮：方案陈述", "第二轮：利益交锋", "第三轮：妥协共识"]
    round_colors = [color_indigo, color_gold, color_emerald]

    for idx, r_name in enumerate(round_labels):
        y_pos = round_y[idx]
        
        # Round Header
        ax_mid.text(0.0, y_pos+0.25, f"● {r_name}", color=round_colors[idx], fontsize=11.5, weight="bold")
        
        # Round Container
        card = FancyBboxPatch((0.0, y_pos), 0.98, 0.23, boxstyle="round,pad=0.015", 
                              fc=card_color, ec=border_color, lw=1.0, transform=ax_mid.transData)
        ax_mid.add_patch(card)
        
        # Renders text from each player using dynamic vertical offset to avoid overlap
        r_dialogues = rounds_data.get(r_name, [])
        y_cursor = 0.19  # Starts near top of box
        
        for p_idx, player in enumerate(r_dialogues[:3]):
            name_clean = player["name"].split("（")[0]
            p_color = color_gold if "居民" in name_clean else (color_emerald if "文旅" in name_clean else color_indigo)
            
            raw_formal = player.get("formal", "")
            if len(raw_formal) > 65:
                raw_formal = raw_formal[:62] + "..."
            wrapped_formal = wrap_text(raw_formal, 44)
            
            # Print speaker and speech block
            ax_mid.text(0.03, y_pos + y_cursor, f"{name_clean}:", color=p_color, fontsize=8, weight="bold")
            ax_mid.text(0.18, y_pos + y_cursor, wrapped_formal, color=text_muted, fontsize=7.8, va="top", linespacing=1.3)
            
            # Calculate height decrement dynamically based on lines
            num_lines = len(wrapped_formal.split('\n'))
            y_cursor -= (num_lines * 0.025 + 0.015)

    # ── Right Column: Consensus Radar & Key Strategies ──
    gs_right = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[0, 2], hspace=0.35)
    
    # Subplot 1: Radar Chart
    ax_radar = fig.add_subplot(gs_right[0, 0], projection='polar')
    ax_radar.set_facecolor(card_color)
    
    # Configure Polar Axis colors
    ax_radar.tick_params(colors=text_muted, labelsize=9)
    ax_radar.grid(color=border_color, linewidth=0.8)
    ax_radar.spines['polar'].set_color(border_color)
    
    categories = ['居民代表 (老王)', '文旅运营商 (赵总)', '专业规划师 (李工)']
    N = len(categories)
    
    # Complete the circle
    angles = [n / float(N) * 2 * 3.1415926 for n in range(N)]
    angles += angles[:1]
    
    # Data
    initial_scores = [50, 50, 50, 50]
    
    laowang_final = voting_scores.get("👥 居民代表（老王）", voting_scores.get("👥 居民代表（老王）", 98.0))
    zhaozong_final = voting_scores.get("💰 文旅运营商（赵总）", 98.0)
    ligong_final = voting_scores.get("📐 规划师（李工）", 99.0)
    
    final_scores = [laowang_final, zhaozong_final, ligong_final, laowang_final]
    
    # Plot initial scores (grey dotted outline)
    ax_radar.plot(angles, initial_scores, color=text_muted, linewidth=1.5, linestyle="--", label="博弈前满意度 (50%)")
    # Plot final scores (indigo filled area)
    ax_radar.plot(angles, final_scores, color=color_indigo, linewidth=2.5, label="博弈达成满意度")
    ax_radar.fill(angles, final_scores, color=color_indigo, alpha=0.15)
    
    # Set custom labels
    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels(categories, fontsize=9.5, weight="bold", color=text_main)
    
    # Radial bounds
    ax_radar.set_ylim(0, 100)
    ax_radar.set_rgrids([20, 40, 60, 80, 100], angle=45, color=border_color, fontsize=8)
    
    ax_radar.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), facecolor=card_color, edgecolor=border_color, fontsize=8.5, labelcolor=text_main)
    ax_radar.set_title("博弈协商各方最终满意度雷达 / SATISFACTION RADAR", color=text_main, fontsize=12, pad=15, weight="bold")

    # Subplot 2: Key Strategies
    ax_strat = fig.add_subplot(gs_right[1, 0])
    ax_strat.set_facecolor(bg_color)
    ax_strat.axis('off')
    
    ax_strat.text(0.0, 0.98, "三、博弈协商成果空间更新共识", color=text_main, fontsize=13.5, weight="bold")
    
    # Parse key strategies from the strategy matrix (or fallbacks)
    key_strategies = []
    if strategy_matrix:
        rows = [r.strip() for r in strategy_matrix.split("\n") if "|" in r]
        if len(rows) >= 3:
            for r in rows[2:5]: 
                cols = [c.strip() for c in r.split("|")[1:-1]]
                if len(cols) >= 4:
                    key_strategies.append(f"🎯 **{cols[0]}**\n👉 {cols[1]} ({cols[3]})")
    
    if not key_strategies:
        key_strategies = [
            "🎯 **老水产地块厂房限制性保护活化**\n👉 引入低密文旅与青年公寓，建筑控高9m，保留场内历史地轨。(空间落位: 0号地块)",
            "🎯 **食品调料大市场‘微介入’风味改造**\n👉 升级为睦邻菜市场与风味院落，保留40%平价公益摊位。(空间落位: 1号地块)",
            "🎯 **社区医疗公服补齐与口袋公园增设**\n👉 强制配建2000㎡社区综合卫生站，填补GVI缺口增设口袋绿地。(空间落位: 2号地块)"
        ]

    y_pos = 0.75
    for strat in key_strategies[:3]:
        # Card container
        card = FancyBboxPatch((0.0, y_pos-0.08), 1.0, 0.22, boxstyle="round,pad=0.015", 
                              fc=card_color, ec=border_color, lw=1.0, transform=ax_strat.transData)
        ax_strat.add_patch(card)
        
        title_part, detail_part = strat.split("\n")
        title_clean = title_part.replace("**", "").replace("🎯", "").strip()
        detail_clean = detail_part.replace("**", "").replace("👉", "").strip()
        
        ax_strat.text(0.03, y_pos+0.06, f"🎯 {title_clean}", color=color_emerald, fontsize=10, weight="bold")
        ax_strat.text(0.03, y_pos-0.04, wrap_text(detail_clean, 48), color=text_muted, fontsize=8.5, linespacing=1.4)
        y_pos -= 0.32

    # Draw small stamp card on bottom right to match A3 sheet layout
    # Sits at x=[0.82, 0.96], y=[0.05, 0.15] on fig coords
    ax_stamp = fig.add_axes([0.84, 0.04, 0.12, 0.08], facecolor=card_color, zorder=2)
    ax_stamp.set_xticks([])
    ax_stamp.set_yticks([])
    for spine in ax_stamp.spines.values():
        spine.set_color(border_color)
        spine.set_linewidth(1.0)
        
    ax_stamp.text(0.05, 0.8, "图名 / Title", fontsize=7.5, color=text_muted, va="center")
    ax_stamp.text(0.05, 0.6, "博弈协商成果示意图", fontsize=8.5, color=text_main, va="center", weight="bold")
    
    ax_stamp.text(0.05, 0.35, "图号 / No.", fontsize=7.5, color=text_muted, va="center")
    ax_stamp.text(0.05, 0.15, "DR-075-SCHEMATIC", fontsize=8.5, color=text_main, va="center")

    # Save to file
    output_dir = ROOT / "static"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "negotiation_infographic.png"
    
    plt.savefig(output_path, facecolor=bg_color, edgecolor='none', bbox_inches='tight')
    plt.close()

    print(f"✅ 博弈协商高分辨率示意图已成功保存于: {output_path}")
    print("==================================================")

if __name__ == "__main__":
    main()
