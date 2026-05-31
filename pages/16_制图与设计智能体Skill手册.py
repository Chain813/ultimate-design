# -*- coding: utf-8 -*-
"""阶段 16：制图与设计智能体 Skill 手册 —— 本地化智能体技能规范与实时交互沙盘。"""

import time
import os
import sys
import subprocess
import json
from pathlib import Path
from PIL import Image
import streamlit as st
import plotly.graph_objects as go

from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.streamlit_compat import stretch_width
from src.engines.llm_engine import call_llm_engine

# 1. Config streamlit page
st.set_page_config(page_title="16 AI智能体Skill手册", layout="wide", initial_sidebar_state="expanded")
render_top_nav()
render_engine_status_alert()

# 2. Render Page Banner
graphic_svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 200" width="100%" height="100%" style="max-width: 600px; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.04));">
  <defs>
    <linearGradient id="g_base" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#f5f5f7"/>
    </linearGradient>
  </defs>
  <!-- Main boxes representing skills -->
  <rect x="50" y="40" width="160" height="120" rx="10" fill="url(#g_base)" stroke="#0071e3" stroke-width="1.2"/>
  <text x="130" y="78" fill="#0071e3" font-size="14" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">制图技能 (Drawing)</text>
  <text x="130" y="108" fill="#86868b" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">Matplotlib & Pillow</text>
  <text x="130" y="128" fill="#86868b" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">A3 标准图纸排版</text>

  <rect x="260" y="40" width="160" height="120" rx="10" fill="url(#g_base)" stroke="#34c759" stroke-width="1.2"/>
  <text x="340" y="78" fill="#34c759" font-size="14" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">智能体博弈 (Agent)</text>
  <text x="340" y="108" fill="#86868b" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">Multi-Agent Forum</text>
  <text x="340" y="128" fill="#86868b" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">满意度效用评估</text>

  <rect x="470" y="40" width="160" height="120" rx="10" fill="url(#g_base)" stroke="#ff9500" stroke-width="1.2"/>
  <text x="550" y="78" fill="#ff9500" font-size="14" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">合规校验 (Zoning)</text>
  <text x="550" y="108" fill="#86868b" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">Zoning Policy Check</text>
  <text x="550" y="128" fill="#86868b" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">规划指标与建议</text>

  <!-- Connective lines -->
  <line x1="210" y1="100" x2="260" y2="100" stroke="#d1d1d6" stroke-width="1.5" stroke-dasharray="4,3"/>
  <line x1="420" y1="100" x2="470" y2="100" stroke="#d1d1d6" stroke-width="1.5" stroke-dasharray="4,3"/>
</svg>
"""

render_page_banner(
    title="AI制图与设计技能手册",
    description="集成城乡规划标准图册制图规范（Matplotlib + Pillow 绘图底盘）、开源社区 AI 辅助更新算法指南，并在文档下方提供实时编译工作坊与三方听证会博弈沙盘。",
    graphic_html=graphic_svg
)

# 3. Sidebar selection
skills_dir = Path("docs/skills")
skill_files = {
    "城乡规划标准图册代码制图技能": "code_drawing_skill.md",
    "通用 Python 代码技术制图与排版拼装设计手册": "generic_code_drawing_skill.md",
    "开源社区城市设计与城市更新 AI 智能体规范手册": "open_source_urban_planning_agent_specs.md",
    "城市更新与城市设计数字化平台 AI 辅助设计指南": "urban_design_ai_agent_skill.md"
}

st.sidebar.markdown("### 📚 技能库导航")
selected_skill_name = st.sidebar.radio("选择 Skill 手册", list(skill_files.keys()))
selected_file = skills_dir / skill_files[selected_skill_name]

# 4. Render markdown content
st.markdown("---")
if selected_file.exists():
    with open(selected_file, "r", encoding="utf-8") as f:
        content = f.read()
    st.markdown(content, unsafe_allow_html=True)
else:
    st.error(f"无法找到技能文档: {selected_file}")

# 5. Interactive Workshop Section
st.markdown("---")
st.header("🛠️ 智能体 Skill 交互体验工作坊 (Interactive Workshop)")

if "drawing" in skill_files[selected_skill_name]:
    # A3 Drawing Compile workshop
    st.subheader("🖼️ A3 规划图纸在线编译与出图预览")
    st.markdown("基于 **Pillow 版式拼装与动态标尺计算规范**，在此直接触发后台制图底盘，实时渲染 GIS 空间要素层，完成标准图签封图。")
    
    drawings_list = {
        "DR-004: 现状区位图": ("现状区位图", "DR-004_现状区位图.png", "DR-004"),
        "DR-020: 道路交通现状图": ("交通分析图", "DR-020_道路交通现状图.png", "DR-020"),
        "DR-051: 道路交通系统规划图": ("道路交通系统规划图", "DR-051_道路交通系统规划图.png", "DR-051"),
        "DR-056: 绿地景观系统图": ("绿地景观系统图", "DR-056_绿地景观系统图.png", "DR-056"),
    }
    
    selected_draw = st.selectbox("选择要编译的空间图纸", list(drawings_list.keys()))
    drawing_type, filename, code = drawings_list[selected_draw]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info(f"""
        **图纸代号**: `{code}`
        
        **图纸类型**: `{drawing_type}`
        
        **输出比例**: A3 物理比例尺自适应
        
        **制图配置项**: 
        - 道路 Cap & Join 平滑样式 (圆角)
        - 规划图叠加 (红/橙虚线高亮)
        - 右侧图例框下方设计说明
        - 左下角法定控制指标显示
        """)
        compile_btn = st.button("🚀 开始编译并预览", **stretch_width(st.button))
        
    with col2:
        if compile_btn:
            with st.spinner("绘图底盘运行中：读取 GeoJSON、构建 Matplotlib Ax 并进行 Pillow 矢量拼接..."):
                cmd = [sys.executable, "tools/generate_atlas_sheets.py", code]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
                
                if res.returncode == 0:
                    st.success(f"✓ 图纸 {code} 编译成功！")
                    with st.expander("📝 编译控制台输出日志"):
                        st.code(res.stdout)
                else:
                    st.error(f"❌ 编译失败，错误代码: {res.returncode}")
                    with st.expander("📝 编译异常日志"):
                        st.code(res.stderr)
            
            # Show image
            img_path = Path("static/atlas") / filename
            if img_path.exists():
                try:
                    img = Image.open(img_path)
                    st.image(img, caption=f"{selected_draw} A3标准导出版式预览", **stretch_width(st.image))
                except Exception as e:
                    st.error(f"渲染生成图片异常: {e}")
            else:
                st.warning(f"未找到生成的图片文件: {img_path}")
        else:
            # Check for existing image preview
            img_path = Path("static/atlas") / filename
            if img_path.exists():
                try:
                    img = Image.open(img_path)
                    st.image(img, caption=f"{selected_draw} 历史图集生成缓存预览", **stretch_width(st.image))
                except Exception:
                    pass
            else:
                st.info("点击“开始编译并预览”按钮，运行底层制图脚本。")
else:
    # Participatory planning simulation workshop
    st.subheader("⚖️ 多主体共识博弈协商仿真沙盘")
    st.markdown("基于 **多智能体博弈决策模型**，模拟在听证会上各个利益相关方（居民、开发商、规划局）对重大冲突指标展开的多轮论证，并实时监控决策共识雷达。")
    
    scenarios = {
        "冲突场景 A：伪满皇宫风貌区限高放宽": "伪满皇宫周边高度控制分区，开发商要求限高从9米放宽至24米，以实现项目资金平衡；居民强烈抗拒高楼，要求视廊保护与日照；规划师严守紫线和历史街区风貌限制。",
        "冲突场景 B：伊通河沿岸大面积绿地（现状2.9%）增设": "街区绿地率实测仅2.9%（严重偏低）。规划师与居民代表联手要求开发商腾退工业院落配建5公顷口袋绿化；开发商抗议成本过高、折算项目净收益骤降。",
        "冲突场景 C：长春站TOD枢纽高强度开发": "火车站南侧地块更新，开发商要求将容积率提高至2.5，配建高层写字楼；居民投诉高强度开发将带来严重的交通拥堵、工作日噪声和日照遮挡。"
    }
    
    selected_scen = st.selectbox("选择要论证的城市更新冲突场景", list(scenarios.keys()))
    st.warning(f"**场景核心冲突**：{scenarios[selected_scen]}")
    
    run_simulation_btn = st.button("💬 启动智能体协商博弈", **stretch_width(st.button))
    
    if run_simulation_btn:
        st.write("---")
        st.markdown("### 🗣️ 协商会现场发言记录 (Multi-Agent Debate)")
        
        # Call LLM or fallback
        prompt = f"""你正在为一个基于冲突场景【{selected_scen}：{scenarios[selected_scen]}】的城市更新协商会议生成模拟对话。
请你扮演三个角色：
1. “居民代表” (绿底, 核心诉求是生活绿化、采光、日常便利，抗拒噪音和高强度商业)
2. “开发运营商” (蓝底, 核心诉求是开发强度容积率、商业活力、投资回报，抗拒过度限高和无偿配建)
3. “注册规划师” (红底/灰底, 核心诉求是上位规划合规、历史遗产紫线保护、公共交通TOD与生态织补)

请为这三个角色各生成一段150字左右的专业观点陈述（包含对容积率、高度、绿化率等具体指标在现场交锋中的主张），并给出他们基于本次协商提案的满意度分数（0到100的整数）。发言应该非常体现出各自鲜明的立场与利益博弈，语言严谨，不得包含前言或后记解释。

请严格以 JSON 格式输出，仅输出纯 JSON 字符串：
{{
  "dialogue": [
    {{"role": "居民代表", "text": "...", "satisfaction": 65}},
    {{"role": "开发运营商", "text": "...", "satisfaction": 72}},
    {{"role": "注册规划师", "text": "...", "satisfaction": 78}}
  ],
  "reasoning": "三方满意度评分背后的利益让步依据说明。"
}}
"""
        with st.spinner("AI 智能体正在读取法定规划限制、运行记忆流反思并输出发言..."):
            try:
                res_text = call_llm_engine(prompt=prompt, system_prompt="你是城乡规划专家系统。只输出纯 JSON 字符串，不要格式化标记，不要解释。", model="deepseek-v4-flash")
                if "```json" in res_text:
                    res_text = res_text.split("```json")[1].split("```")[0]
                elif "```" in res_text:
                    res_text = res_text.split("```")[1].split("```")[0]
                data = json.loads(res_text.strip())
            except Exception:
                # Fallback to local high-fidelity presets
                if "限高" in selected_scen:
                    data = {
                        "dialogue": [
                            {"role": "居民代表", "text": "我们坚决反对放宽限高。伪满皇宫是我们宽城区的历史标志，如果盖起24米的高楼，不仅阳光被彻底挡住，整个历史风貌的视线走廊全被截断了！我们希望严守9米的核心区限高，多建老幼游憩绿地。", "satisfaction": 45},
                            {"role": "开发运营商", "text": "我们理解居民对采光的要求，但在核心区保留9米限高下，容积率仅为0.8，这导致前期拆迁补偿和工业遗存加固的几亿资金完全无法平衡。放宽到24米是为了引入青年文创民宿，我们将退让红线增加地下车库供社区共用。", "satisfaction": 80},
                            {"role": "注册规划师", "text": "作为规划协调方，紫线控制是法定红线，不能随意突破。我们建议采取折中方案：临伪满皇宫一侧30米内执行9米绝对限高，过渡区地块阶梯状退台至18米（约5层），容积率限制在1.2，通过开发商配建老幼中心交换部分面积奖励。", "satisfaction": 65}
                        ],
                        "reasoning": "开发商获得了一定容积率让步，但高度仍受限；居民保护了最近的日照但退让了远期视廊；规划局在严守法律前提下完成了更新破局。"
                    }
                elif "绿地" in selected_scen:
                    data = {
                        "dialogue": [
                            {"role": "居民代表", "text": "现状绿地率只有2.9%，全是水泥地，夏天热得像火炉，老人小孩连个散步的地方都没有！必须把闲置的机车厂院落全部改成口袋公园，种树铺草，还我们绿视率和生态健康！", "satisfaction": 90},
                            {"role": "开发运营商", "text": "机车厂废弃车间原计划改造成商业街区，租金是主要收入来源。无偿配建5公顷绿地并负责后期维护，会使我们的静态投资回收期延长至15年，我们要求政府在土地出让金或税收上给予生态修补专项补贴。", "satisfaction": 50},
                            {"role": "注册规划师", "text": "根据《城市居住区规划设计标准》，该片区绿地赤字极为严重。我们支持增设绿地以盘活生态资产。规划建议采用‘绿地指标占补平衡’：开发商无偿移口袋公园，规划局允许其在商铺楼顶做垂直绿化并折算50%绿地指标，同时减免5%契税。", "satisfaction": 85}
                        ],
                        "reasoning": "居民获得了高额生态补偿，满意度极高；开发商虽然损失了部分商铺面积，但通过楼顶绿化折算和税收减免回收了资金；规划师成功推行了生态织补目标。"
                    }
                else:
                    data = {
                        "dialogue": [
                            {"role": "居民代表", "text": "火车站南侧本来就拥堵，如果建起2.5容积率的高楼大厦，交通肯定瘫痪！而且高楼风和铁路噪音叠加，简直没法居住。我们要求限制容积率在1.4以内，严控高层开发。", "satisfaction": 55},
                            {"role": "开发运营商", "text": "火车站TOD地块是黄金地段，必须通过高强度开发实现溢出效应。2.5的容积率能够容纳更多数字创新产业，创造几千个就业岗位，我们将无偿配建二层人行连廊直通火车站，彻底解决地面人车混行拥堵。", "satisfaction": 85},
                            {"role": "注册规划师", "text": "TOD开发符合城市高质量收缩与更新导向。我们建议把容积率控制在2.0。开发商必须把配建的二层连廊向全社会免费开放，且建筑裙房必须引入平价社区菜市，以对冲高强度开发对居民生活造成的负面冲击。", "satisfaction": 75}
                        ],
                        "reasoning": "TOD高强度开发基本实现，开发商满意度较高；居民虽然承担了开发密度，但获得了二层连廊便利与菜市配套；规划局成功将商业溢出效应反哺给了社会基础设施。"
                    }
                    
        # Render dialogs
        for item in data["dialogue"]:
            role = item["role"]
            text = item["text"]
            sat = item["satisfaction"]
            
            if "居民" in role:
                st.markdown(f"""
                <div style="background-color: #f0fdf4; border-left: 5px solid #22c55e; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                    <span style="color: #15803d; font-weight: bold; font-size: 1.1em;">🌳 {role} (满意度: {sat}%)</span>
                    <p style="color: #1e293b; margin-top: 5px; font-size: 0.95em;">{text}</p>
                </div>
                """, unsafe_allow_html=True)
            elif "开发" in role:
                st.markdown(f"""
                <div style="background-color: #fffbeb; border-left: 5px solid #fbbf24; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                    <span style="color: #b45309; font-weight: bold; font-size: 1.1em;">🏢 {role} (满意度: {sat}%)</span>
                    <p style="color: #1e293b; margin-top: 5px; font-size: 0.95em;">{text}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #eff6ff; border-left: 5px solid #3b82f6; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                    <span style="color: #1d4ed8; font-weight: bold; font-size: 1.1em;">📐 {role} (满意度: {sat}%)</span>
                    <p style="color: #1e293b; margin-top: 5px; font-size: 0.95em;">{text}</p>
                </div>
                """, unsafe_allow_html=True)
                
        # Draw Plotly radar
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            roles = [item["role"] for item in data["dialogue"]]
            sats = [item["satisfaction"] for item in data["dialogue"]]
            roles.append(roles[0])
            sats.append(sats[0])
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=sats,
                theta=roles,
                fill='toself',
                fillcolor='rgba(16, 185, 129, 0.2)',
                line=dict(color='#10b981', width=2),
                name='博弈主体满意度'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100]),
                    angularaxis=dict(direction="clockwise")
                ),
                showlegend=False,
                margin=dict(l=40, r=40, t=20, bottom=20),
                height=280
            )
            st.plotly_chart(fig, **stretch_width(st.plotly_chart))
            
        with col_c2:
            avg_sat = sum(item["satisfaction"] for item in data["dialogue"]) / 3.0
            st.metric("👥 协商共识指数 (Consensus Index)", f"{avg_sat:.1f}%")
            
            min_sat = min(item["satisfaction"] for item in data["dialogue"])
            if min_sat < 60:
                st.error(f"⚠️ **未达成共识**！最低满意度 ({min_sat}%) 低于更新启动阈值 (60%)。策略将退回重审，请重新发起博弈协商。")
            else:
                st.success(f"🎉 **共识达成成功**！全体利益主体满意度均达到法定更新基准阈值 (>=60%)。协商结论可作为下一步控规编制依据。")
                
            st.markdown(f"**利益平衡解读**：\n*{data['reasoning']}*")
