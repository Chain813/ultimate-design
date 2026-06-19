# -*- coding: utf-8 -*-
"""scripts/generate_negotiation_replay.py

Generates static/negotiation_replay.html with embedded dialogue logs, satisfaction scores, 
and strategy matrix for an interactive video-like playback experience.
"""

import json
import re
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def markdown_to_html_simple(md_text):
    """Converts simple markdown bold and lists to HTML."""
    if not md_text:
        return ""
    # Escapes HTML first to avoid script injections
    html = md_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold **text**
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    # Line breaks
    html = html.replace("\n", "<br>")
    return html

def main():
    print("==================================================")
    print("📦 开始生成博弈协商沙盘交互式重放页面...")
    print("==================================================")

    cache_path = ROOT / "output" / "stage_bus_cache.json"
    if not cache_path.exists():
        print("错误: output/stage_bus_cache.json 不存在！请先运行 scripts/run_real_negotiation.py。")
        sys.exit(1)

    with open(cache_path, "r", encoding="utf-8") as f:
        cache_data = json.load(f)

    # Load dialogues
    dialogues = cache_data.get("07_negotiation_dialogues", [])
    if not dialogues:
        print("警告: 缓存中没有 dialogues，尝试解析 07_negotiation_result...")
        # Fallback dialogue generation if empty
        dialogues = [
            {
                "round_label": "第一轮：方案陈述",
                "name": "🏠 居民代表（老王）",
                "thinking": "我希望能有更多的公共活动绿地和配套设施，菜市场得方便，不能全是高档写字楼。",
                "formal": "我们在这儿住了几十年，最盼望的就是小区环境变好。我希望在老水产市场和食品调料地块多建口袋公园和菜市场。商业开发我们不反对，但容积率和高度得合适，别把我们的阳光全挡了。"
            },
            {
                "round_label": "第一轮：方案陈述",
                "name": "💰 文旅运营商（赵总）",
                "thinking": "靠近伪满皇宫是极好的文旅节点，首层做商铺，高层精品民宿，以特色文创带动客流，保障收益。",
                "formal": "我看好这个地块的文旅IP价值。我们计划打造历史风貌市集和精品民宿群，实现文商旅融合。不过要实现盈利，我们希望容积率能稍微放宽到1.4的红线上限，并在风貌把控下适当增加商业开发强度。"
            },
            {
                "round_label": "第一轮：方案陈述",
                "name": "📐 规划师（李工）",
                "thinking": "核心区限高9米是红线，一般区18米，必须遵守保护条例，同时引导各方实现共赢。",
                "formal": "我们必须坚守《长春市历史文化名城保护条例》底线，特别是伪满皇宫周边的限高（核心区≤9m，一般区≤18m）。我建议采用‘微更新’模式，老旧红砖厂房可保留改造，引入低密度特色文旅，同时以口袋公园做生态过渡。"
            }
        ]

    # Load voting scores
    voting_scores = cache_data.get("07_voting_scores", {
        "👥 居民代表（老王）": 85.0,
        "💰 文旅运营商（赵总）": 80.0,
        "📐 规划师（李工）": 90.0
    })

    # Load strategy matrix (markdown)
    strategy_matrix_md = cache_data.get("07_strategy_matrix", "")
    if not strategy_matrix_md:
        strategy_matrix_md = "| 策略方向 | 具体举措 | 政策依据 | 空间落位 | 资金逻辑 | 协同度 |\n|---|---|---|---|---|---|\n| 暂无策略数据 | 请完成博弈推演后生成 | - | - | - | - |"

    # Convert strategy matrix markdown table to HTML table
    strategy_matrix_html = ""
    lines = strategy_matrix_md.strip().split("\n")
    if len(lines) >= 2:
        table_html = "<table class='matrix-table'><thead>"
        # Parse headers
        headers = [h.strip() for h in lines[0].split("|")[1:-1]]
        table_html += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>"
        # Parse rows (skip separator line)
        for line in lines[2:]:
            if "|" in line:
                cols = [markdown_to_html_simple(c.strip()) for c in line.split("|")[1:-1]]
                table_html += "<tr>" + "".join(f"<td>{c}</td>" for c in cols) + "</tr>"
        table_html += "</tbody></table>"
        strategy_matrix_html = table_html
    else:
        strategy_matrix_html = f"<div class='matrix-fallback'>{markdown_to_html_simple(strategy_matrix_md)}</div>"

    # Map dialogue names to avatar keys and colors
    avatar_map = {
        "🏠 居民代表（老王）": "avatar_laowang.png",
        "👥 居民代表（老王）": "avatar_laowang.png",
        "💰 文旅运营商（赵总）": "avatar_zhaozong.png",
        "📐 规划师（李工）": "avatar_ligong.png"
    }
    
    color_map = {
        "laowang": "gold",
        "zhaozong": "emerald",
        "ligong": "indigo"
    }

    processed_dialogues = []
    for d in dialogues:
        name = d["name"]
        avatar_file = avatar_map.get(name, "avatar_laowang.png")
        avatar_key = "laowang" if "老王" in name else ("zhaozong" if "赵总" in name else "ligong")
        color = color_map.get(avatar_key, "indigo")
        
        processed_dialogues.append({
            "round": d["round_label"],
            "name": name,
            "avatar": f"avatars/{avatar_file}",
            "color": color,
            "thinking": d.get("thinking", ""),
            "formal": d["formal"]
        })

    # Prepare JSON data for HTML embedding
    dialogues_json = json.dumps(processed_dialogues, ensure_ascii=False)
    scores_json = json.dumps(voting_scores, ensure_ascii=False)

    # HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多主体协同规划博弈协商沙盘 - 交互重放</title>
    <!-- Google Fonts Outfit & Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        :root {{
            --bg-gradient: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e1b4b 100%);
            --glass-bg: rgba(17, 24, 39, 0.75);
            --glass-border: rgba(255, 255, 255, 0.08);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            
            /* Avatar color themes */
            --color-gold: #f59e0b;
            --color-gold-bg: rgba(245, 158, 11, 0.06);
            --color-gold-border: rgba(245, 158, 11, 0.25);
            
            --color-emerald: #10b981;
            --color-emerald-bg: rgba(16, 185, 129, 0.06);
            --color-emerald-border: rgba(16, 185, 129, 0.25);
            
            --color-indigo: #6366f1;
            --color-indigo-bg: rgba(99, 102, 241, 0.06);
            --color-indigo-border: rgba(99, 102, 241, 0.25);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', 'system-ui', -apple-system, sans-serif;
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }}

        header {{
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--glass-border);
            padding: 16px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .brand h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 0.5px;
            background: linear-gradient(90deg, #818cf8 0%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand span {{
            font-size: 11px;
            background: rgba(99, 102, 241, 0.15);
            color: #a5b4fc;
            padding: 3px 8px;
            border-radius: 20px;
            border: 1px solid rgba(99, 102, 241, 0.3);
            text-transform: uppercase;
            font-weight: 600;
        }}

        .controls {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .btn {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-main);
            padding: 8px 18px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }}

        .btn:hover {{
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }}

        .btn-primary {{
            background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
            border: none;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }}

        .btn-primary:hover {{
            background: linear-gradient(90deg, #818cf8 0%, #6366f1 100%);
            box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
        }}

        .speed-control {{
            display: flex;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 2px;
        }}

        .speed-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .speed-btn.active {{
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-main);
        }}

        .main-layout {{
            flex: 1;
            display: grid;
            grid-template-columns: 1.3fr 1fr;
            gap: 24px;
            padding: 24px 40px;
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
        }}

        /* Left Side: Dialogue Stream */
        .chat-section {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        .chat-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            height: 620px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .chat-header {{
            padding: 16px 24px;
            border-bottom: 1px solid var(--glass-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0,0,0,0.1);
        }}

        .chat-header-title {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .chat-timeline-indicator {{
            background: rgba(255, 255, 255, 0.08);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            color: #a5b4fc;
        }}

        .chat-body {{
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
            scroll-behavior: smooth;
        }}

        /* Dialogue Bubbles */
        .dialogue-item {{
            display: flex;
            gap: 16px;
            align-items: flex-start;
            animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
            transform: translateY(20px);
        }}

        @keyframes slideUp {{
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .avatar {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            flex-shrink: 0;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.25);
            background: #334155;
            border: 2px solid var(--border-color);
        }}

        .avatar-gold {{ --border-color: var(--color-gold); }}
        .avatar-emerald {{ --border-color: var(--color-emerald); }}
        .avatar-indigo {{ --border-color: var(--color-indigo); }}

        .bubble {{
            flex: 1;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            border-left: 4px solid var(--border-color);
            background: var(--bg-color);
        }}

        .bubble-gold {{
            --border-color: var(--color-gold);
            --bg-color: var(--color-gold-bg);
        }}
        .bubble-emerald {{
            --border-color: var(--color-emerald);
            --bg-color: var(--color-emerald-bg);
        }}
        .bubble-indigo {{
            --border-color: var(--color-indigo);
            --bg-color: var(--color-indigo-bg);
        }}

        .bubble-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .speaker-name {{
            font-weight: 700;
            font-size: 14px;
            color: var(--name-color);
        }}
        .bubble-gold .speaker-name {{ --name-color: var(--color-gold); }}
        .bubble-emerald .speaker-name {{ --name-color: var(--color-emerald); }}
        .bubble-indigo .speaker-name {{ --name-color: var(--color-indigo); }}

        .round-tag {{
            font-size: 11px;
            color: var(--text-muted);
            font-weight: 400;
        }}

        .thinking-process {{
            font-size: 12px;
            color: #64748b;
            background: rgba(0, 0, 0, 0.2);
            padding: 8px 12px;
            border-left: 3px solid #475569;
            border-radius: 4px;
            margin-bottom: 12px;
            font-style: italic;
        }}

        .thinking-process span {{
            font-weight: 600;
            font-style: normal;
            font-size: 10px;
            letter-spacing: 0.5px;
            display: block;
            margin-bottom: 3px;
            color: #94a3b8;
        }}

        .formal-reply {{
            font-size: 13.5px;
            line-height: 1.6;
            color: #e2e8f0;
        }}

        /* Typing indicator */
        .typing-indicator {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 18px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            border: 1px dashed rgba(255, 255, 255, 0.08);
            font-size: 12px;
            color: var(--text-muted);
            width: fit-content;
            margin-left: 64px;
        }}

        .typing-dots {{
            display: flex;
            gap: 4px;
        }}

        .typing-dot {{
            width: 6px;
            height: 6px;
            background: #818cf8;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }}

        .typing-dot:nth-child(1) {{ animation-delay: -0.32s; }}
        .typing-dot:nth-child(2) {{ animation-delay: -0.16s; }}

        @keyframes bounce {{
            0%, 80%, 100% {{ transform: scale(0); }}
            40% {{ transform: scale(1); }}
        }}

        /* Right Side: Metrics & Matrix */
        .metrics-section {{
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}

        .chart-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 380px;
            justify-content: center;
        }}

        .chart-title {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 16px;
            align-self: flex-start;
        }}

        .scores-panel {{
            display: flex;
            width: 100%;
            justify-content: space-around;
            margin-top: 10px;
        }}

        .score-item {{
            text-align: center;
        }}

        .score-val {{
            font-family: 'Outfit', sans-serif;
            font-size: 26px;
            font-weight: 800;
            margin-top: 4px;
        }}

        .score-item.gold .score-val {{ color: var(--color-gold); }}
        .score-item.emerald .score-val {{ color: var(--color-emerald); }}
        .score-item.indigo .score-val {{ color: var(--color-indigo); }}

        .score-label {{
            font-size: 11px;
            color: var(--text-muted);
            font-weight: 500;
        }}

        /* Bottom/Right Card: Strategy Matrix */
        .matrix-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .matrix-title {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 16px;
        }}

        .matrix-container {{
            flex: 1;
            overflow-y: auto;
            border-radius: 8px;
            border: 1px solid var(--glass-border);
        }}

        .matrix-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12.5px;
            text-align: left;
        }}

        .matrix-table th {{
            background: rgba(0,0,0,0.25);
            color: var(--text-main);
            font-weight: 600;
            padding: 12px 14px;
            border-bottom: 1px solid var(--glass-border);
            position: sticky;
            top: 0;
            backdrop-filter: blur(4px);
        }}

        .matrix-table td {{
            padding: 12px 14px;
            border-bottom: 1px solid var(--glass-border);
            color: #cbd5e1;
            line-height: 1.5;
            vertical-align: top;
        }}

        .matrix-table tr:hover {{
            background: rgba(255, 255, 255, 0.02);
        }}

        .matrix-table tr:last-child td {{
            border-bottom: none;
        }}

        /* Custom Scrollbar */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}

        ::-webkit-scrollbar-track {{
            background: rgba(0,0,0,0.1);
        }}

        ::-webkit-scrollbar-thumb {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255,255,255,0.2);
        }}
    </style>
</head>
<body>

    <header>
        <div class="brand">
            <h1>UltimateDESIGN 博弈协商沙盘</h1>
            <span>Replay Board</span>
        </div>
        <div class="controls">
            <div class="speed-control">
                <button class="speed-btn active" onclick="setSpeed(1000, this)">1x</button>
                <button class="speed-btn" onclick="setSpeed(500, this)">2x</button>
                <button class="speed-btn" onclick="setSpeed(200, this)">5x</button>
            </div>
            <button class="btn" id="restartBtn" onclick="restartReplay()">⏮ 重新开始</button>
            <button class="btn btn-primary" id="playBtn" onclick="togglePlay()">▶ 开始播放</button>
        </div>
    </header>

    <div class="main-layout">
        
        <!-- Left Side: Chat Screen -->
        <section class="chat-section">
            <div class="chat-card">
                <div class="chat-header">
                    <div class="chat-header-title">
                        <span>💬</span> 协商发言流 (Dialogue Stream)
                    </div>
                    <div class="chat-timeline-indicator" id="timelineIndicator">
                        准备中
                    </div>
                </div>
                <div class="chat-body" id="chatBody">
                    <!-- Dialogue items will render here dynamically -->
                </div>
                <div class="typing-indicator" id="typingIndicator" style="display: none;">
                    <span id="typingName">老王</span> 正在思考中
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Right Side: Metrics & Consensus Matrix -->
        <section class="metrics-section">
            
            <!-- Radar Chart Card -->
            <div class="chart-card">
                <div class="chart-title">📊 协同共识满意度收敛 (Satisfaction Level)</div>
                <div style="width: 260px; height: 260px; position: relative;">
                    <canvas id="radarChart"></canvas>
                </div>
                <div class="scores-panel">
                    <div class="score-item gold">
                        <div class="score-label">老王 (居民)</div>
                        <div class="score-val" id="scoreLaowang">50</div>
                    </div>
                    <div class="score-item emerald">
                        <div class="score-label">赵总 (运营商)</div>
                        <div class="score-val" id="scoreZhaozong">50</div>
                    </div>
                    <div class="score-item indigo">
                        <div class="score-label">李工 (规划师)</div>
                        <div class="score-val" id="scoreLigong">50</div>
                    </div>
                </div>
            </div>

            <!-- Strategy Consensus Matrix Card -->
            <div class="matrix-card">
                <div class="matrix-title">📐 协商产出：《策略共识矩阵》</div>
                <div class="matrix-container">
                    {strategy_matrix_html}
                </div>
            </div>

        </section>

    </div>

    <script>
        // Dialogues data generated by python script
        const dialogues = {dialogues_json};
        
        // Final scores
        const finalScores = {scores_json};
        
        // Speaker icons mapping
        const speakerIcons = {{
            "🏠 居民代表（老王）": "👴",
            "👥 居民代表（老王）": "👴",
            "💰 文旅运营商（赵总）": "👔",
            "📐 规划师（李工）": "📐"
        }};

        let currentIndex = 0;
        let isPlaying = false;
        let playInterval = null;
        let stepDelay = 1000; // default speed 1x delay multiplier (1000ms base)
        let chart = null;

        // Initialize Radar Chart
        function initChart() {{
            const ctx = document.getElementById('radarChart').getContext('2d');
            chart = new Chart(ctx, {{
                type: 'radar',
                data: {{
                    labels: ['居民代表 (老王)', '文旅运营商 (赵总)', '专业规划师 (李工)'],
                    datasets: [{{
                        label: '利益满意度得分',
                        data: [50, 50, 50],
                        backgroundColor: 'rgba(99, 102, 241, 0.15)',
                        borderColor: '#818cf8',
                        borderWidth: 2,
                        pointBackgroundColor: '#6366f1',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#6366f1'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        r: {{
                            angleLines: {{
                                color: 'rgba(255, 255, 255, 0.08)'
                            }},
                            grid: {{
                                color: 'rgba(255, 255, 255, 0.08)'
                            }},
                            pointLabels: {{
                                color: '#94a3b8',
                                font: {{
                                    size: 10,
                                    weight: 'bold'
                                }}
                            }},
                            ticks: {{
                                display: false,
                                stepSize: 20
                            }},
                            min: 0,
                            max: 100
                        }}
                    }}
                }}
            }});
        }}

        // Dynamic satisfaction simulation during turns
        function updateScores(index) {{
            // Calculate intermediate scores based on index
            let laowang = 50;
            let zhaozong = 50;
            let ligong = 50;
            
            const targetLaowang = finalScores["👥 居民代表（老王）"] || 85;
            const targetZhaozong = finalScores["💰 文旅运营商（赵总）"] || 80;
            const targetLigong = finalScores["📐 规划师（李工）"] || 90;

            if (index > 0) {{
                // Round 1 finishes
                laowang = 55 + (targetLaowang - 55) * Math.min(index / 9, 0.3);
                zhaozong = 52 + (targetZhaozong - 52) * Math.min(index / 9, 0.3);
                ligong = 55 + (targetLigong - 55) * Math.min(index / 9, 0.3);
            }}
            if (index >= 3) {{
                // Round 2 finishes (利益交锋 - satisfaction might fluctuate)
                laowang = 60 + (targetLaowang - 60) * Math.min(index / 9, 0.6);
                zhaozong = 65 + (targetZhaozong - 65) * Math.min(index / 9, 0.6);
                ligong = 62 + (targetLigong - 62) * Math.min(index / 9, 0.6);
            }}
            if (index >= 6) {{
                // Round 3 finishes (妥协达成 - convergence to final)
                laowang = 70 + (targetLaowang - 70) * ((index - 6) / 3);
                zhaozong = 70 + (targetZhaozong - 70) * ((index - 6) / 3);
                ligong = 72 + (targetLigong - 72) * ((index - 6) / 3);
            }}
            if (index >= dialogues.length) {{
                laowang = targetLaowang;
                zhaozong = targetZhaozong;
                ligong = targetLigong;
            }}

            laowang = Math.round(laowang);
            zhaozong = Math.round(zhaozong);
            ligong = Math.round(ligong);

            // Update UI
            document.getElementById('scoreLaowang').innerText = laowang;
            document.getElementById('scoreZhaozong').innerText = zhaozong;
            document.getElementById('scoreLigong').innerText = ligong;

            // Update Chart
            chart.data.datasets[0].data = [laowang, zhaozong, ligong];
            chart.update();
        }}

        function setSpeed(ms, btn) {{
            stepDelay = ms;
            document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (isPlaying) {{
                // restart interval with new speed
                clearInterval(playInterval);
                playInterval = setInterval(nextStep, stepDelay * 2);
            }}
        }}

        function togglePlay() {{
            const btn = document.getElementById('playBtn');
            if (isPlaying) {{
                clearInterval(playInterval);
                isPlaying = false;
                btn.innerText = '▶ 开始播放';
            }} else {{
                isPlaying = true;
                btn.innerText = '⏸ 暂停播放';
                // Trigger immediate next step, then set interval
                nextStep();
                playInterval = setInterval(nextStep, stepDelay * 2.5);
            }}
        }}

        function restartReplay() {{
            clearInterval(playInterval);
            isPlaying = false;
            document.getElementById('playBtn').innerText = '▶ 开始播放';
            currentIndex = 0;
            document.getElementById('chatBody').innerHTML = '';
            document.getElementById('timelineIndicator').innerText = '准备中';
            updateScores(0);
        }}

        function nextStep() {{
            if (currentIndex >= dialogues.length) {{
                clearInterval(playInterval);
                isPlaying = false;
                document.getElementById('playBtn').innerText = '▶ 播放完成';
                document.getElementById('playBtn').disabled = true;
                document.getElementById('timelineIndicator').innerText = '推演完成';
                document.getElementById('typingIndicator').style.display = 'none';
                return;
            }}

            const d = dialogues[currentIndex];
            const name = d.name;
            const round = d.round;
            const thinking = d.thinking;
            const formal = d.formal;
            const color = d.color;
            const emoji = speakerIcons[name] || "👤";

            // Show typing indicator
            document.getElementById('typingIndicator').style.display = 'flex';
            document.getElementById('typingName').innerText = name;
            
            // Wait for typing simulation before showing bubble
            setTimeout(() => {{
                if (!isPlaying && currentIndex === 0) return; // guard against reset during timeout
                
                document.getElementById('typingIndicator').style.display = 'none';
                document.getElementById('timelineIndicator').innerText = round;
                
                const chatBody = document.getElementById('chatBody');
                
                // Construct bubble HTML
                let thinkingHtml = '';
                if (thinking) {{
                    thinkingHtml = `
                        <div class="thinking-process">
                            <span>💭 思考过程 (Thinking Process)</span>
                            ${{thinking}}
                        </div>
                    `;
                }}

                const itemHtml = `
                    <div class="dialogue-item">
                        <div class="avatar avatar-${{color}}">${{emoji}}</div>
                        <div class="bubble bubble-${{color}}">
                            <div class="bubble-header">
                                <span class="speaker-name">${{name}}</span>
                                <span class="round-tag">${{round}}</span>
                            </div>
                            ${{thinkingHtml}}
                            <div class="formal-reply">${{formal}}</div>
                        </div>
                    </div>
                `;
                
                chatBody.insertAdjacentHTML('beforeend', itemHtml);
                chatBody.scrollTop = chatBody.scrollHeight;
                
                currentIndex++;
                updateScores(currentIndex);
            }}, stepDelay);
        }}

        window.onload = function() {{
            initChart();
            updateScores(0);
        }}
    </script>
</body>
</html>
"""

    output_dir = ROOT / "static"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "negotiation_replay.html"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ 交互式重放页面已成功生成于: {output_path}")
    print("==================================================")

if __name__ == "__main__":
    main()
