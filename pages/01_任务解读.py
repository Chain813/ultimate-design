"""阶段 01：任务解读 —— 项目边界锁定、任务书/开题报告展示。"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.ui.streamlit_compat import stretch_width
from src.ui.module_summary import render_stage_summary
from src.engines.drawing_prompt_templates import get_templates_by_stage, build_drawing_prompt, generate_drawing_prompt_with_llm
from src.workflow.stage_data_bus import save_stage_output, render_evidence_chain_bar
from src.config import DOCS_DIR, META_DIR
from src.utils.text_io import read_text_with_fallback
from pathlib import Path
from src.ui.drawing_prompt_ui import render_drawing_prompt_ui

st.set_page_config(page_title="01 任务解读", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

TASK_BOOK_PATH = DOCS_DIR / "毕业设计任务书.pdf"
PROPOSAL_PATH = DOCS_DIR / "毕业设计开题报告.pdf"

render_page_banner(
    title="任务解读",
    description="明确研究范围、设计深度和成果形式，锁定任务书与开题报告中的核心要求。",
    eyebrow="Stage 01",
    tags=["研究范围锁定", "任务书解析", "开题报告对照", "技术路线"],
    metrics=[
        {"value": "150 公顷", "label": "研究范围", "meta": "任务书明确的核心片区"},
        {"value": "5 个", "label": "深化地段", "meta": "任务书要求重点设计单元"},
        {"value": "4 项", "label": "核心痛点", "meta": "开题报告现状诊断结论"},
    ],
)
render_evidence_chain_bar("01", ["01", "02", "03", "04", "05"])

SUB_OPTIONS = ["📋 项目概况", "📄 任务书与开题报告", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "📋 项目概况":
    render_section_intro("项目基本信息", "锁定研究边界、设计深度和核心任务。", eyebrow="Project Brief")
    info_data = {
        "项目名称": "AI赋能下的伪满皇宫周边街区更新规划设计",
        "设计类型": "城市更新 · 历史街区 · 数字孪生",
        "研究范围": "约150公顷，由长春大街、长白路、东九条、亚泰快速路围合",
        "设计深度": "总体城市设计 + 5个重点地块深化设计",
        "成果形式": "A3图册（≥60页）+ A1展板（≥3张）+ 规划文本 + PPT",
        "核心矛盾": "历史保护与活力不足、工业低效、社区老化、交通割裂",
        "技术特色": "GIS + CV + POI + NLP/LLM + AIGC + 数字孪生",
    }
    for k, v in info_data.items():
        st.markdown(f"**{k}**：{v}")

    save_stage_output("01", "project_info", info_data)

elif selected_sub == "📄 任务书与开题报告":
    render_section_intro("任务书 / 开题报告资料台", "核对原始文档并查看已萃取的关键信息。", eyebrow="Research Inputs")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 📕 毕业设计任务书")
            st.caption("官方下发的设计要求与边界限定文件。")
            if TASK_BOOK_PATH.exists():
                st.download_button(
                    "📥 下载任务书 PDF",
                    TASK_BOOK_PATH.read_bytes(),
                    file_name=TASK_BOOK_PATH.name,
                    mime="application/pdf",
                    type="primary",
                    **stretch_width(st.download_button),
                )
            else:
                st.warning("未找到任务书文件。")
            
            mission_path = META_DIR / "mission_text.txt"
            if mission_path.exists():
                mission_text = read_text_with_fallback(mission_path)
                with st.expander("👁️ 查看任务书核心摘录", expanded=True):
                    # HTML formatting for a sleek, dark-themed scrollable text block
                    st.markdown(
                        f'''<div style="font-size:13px; color:rgba(255,255,255,0.75); line-height:1.6; 
                        max-height:280px; overflow-y:auto; padding:12px; 
                        background:rgba(0,0,0,0.25); border-radius:8px; border: 1px solid rgba(255,255,255,0.05);">
                        {mission_text[:1800].replace(chr(10), "<br>")}</div>''', 
                        unsafe_allow_html=True
                    )

    with col2:
        with st.container(border=True):
            st.markdown("#### 📗 毕业设计开题报告")
            st.caption("前期调研、文献综述与核心技术路线推演报告。")
            if PROPOSAL_PATH.exists():
                st.download_button(
                    "📥 下载开题报告 PDF",
                    PROPOSAL_PATH.read_bytes(),
                    file_name=PROPOSAL_PATH.name,
                    mime="application/pdf",
                    type="primary",
                    **stretch_width(st.download_button),
                )
            else:
                st.warning("未找到开题报告文件。")
            
            with st.expander("👁️ 查看核心框架提纲", expanded=True):
                st.markdown(
                    '''<div style="font-size:13px; color:rgba(255,255,255,0.75); line-height:1.6; 
                    max-height:280px; overflow-y:auto; padding:12px; 
                    background:rgba(0,0,0,0.25); border-radius:8px; border: 1px solid rgba(255,255,255,0.05);">
                    <b style="color:rgba(255,255,255,0.9);">第一部分：现状研判与问题痛点</b><br>
                    • 历史文脉断裂与空间感知弱化<br>
                    • 工业遗存与建筑资产闲置低效<br>
                    • 跨铁路交通微循环与慢行系统不畅<br><br>
                    <b style="color:rgba(255,255,255,0.9);">第二部分：目标定位与愿景</b><br>
                    数字孪生驱动的“古今共振”街区微更新规划<br><br>
                    <b style="color:rgba(255,255,255,0.9);">第三部分：拟采用的核心技术路线</b><br>
                    <code>GIS底座构建</code> ➔ <code>多源数据语义萃取</code> ➔ <code>AHP-MPI 潜力评估</code> ➔ <code>AIGC (SD/ControlNet) 推演</code>
                    </div>''', 
                    unsafe_allow_html=True
                )

elif selected_sub == "🖼️ 图纸提示词生成":
    render_drawing_prompt_ui("01", key_prefix="p1", stage_title="任务解读")


st.markdown("---")
render_stage_summary(
    stage_code="01",
    title="项目边界与任务要求锁定",
    findings=[
        {"point": "研究范围约 150 公顷，涵盖 5 个重点深化地段", "evidence": "任务书明确的核心片区边界"},
        {"point": "核心任务为系统性概念设计 + 数字孪生与 AIGC 推演表达", "evidence": "任务书核心任务条款"},
        {"point": "四大核心痛点：用地混杂、交通割裂、老龄化、环境品质不足", "evidence": "开题报告现状诊断结论"},
    ],
    methodology="基于毕业设计任务书与开题报告的文本解析",
    implication="为后续资料收集（Stage 02）和现场调研（Stage 03）提供了明确的工作边界",
)
