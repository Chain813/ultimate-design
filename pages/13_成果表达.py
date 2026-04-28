"""阶段 13：成果表达 —— 图纸提示词总览 + 效果图管理 + 成果导出。"""

import streamlit as st
from pathlib import Path
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.ui.module_summary import render_stage_summary
from src.engines.drawing_prompt_templates import (
    DRAWING_TEMPLATES,
    get_templates_by_stage,
    build_drawing_prompt,
    generate_drawing_prompt_with_llm,
)
from src.workflow.stage_data_bus import load_stage_output, render_evidence_chain_bar

st.set_page_config(page_title="13 成果表达", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="成果表达",
    description="整理全流程图纸提示词、效果图集和成果导出，为图册制作和答辩汇报提供支撑。",
    eyebrow="Stage 13",
    tags=["图纸提示词总览", "效果图管理", "Word/CSV 导出"],
)
render_evidence_chain_bar("13", ["10", "11", "12", "13"])

SUB_OPTIONS = ["📋 图纸提示词总览", "🖼️ AIGC 效果图管理", "📤 成果导出中心"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "📋 图纸提示词总览":
    render_section_intro(
        "全流程图纸提示词模板库",
        "一览全部预设图纸模板，可按阶段筛选，支持一键生成数据注入后的 Image 2.0 提示词。",
        eyebrow="All Drawing Prompts",
    )

    with st.sidebar:
        model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p13_model")
        stage_filter = st.selectbox("按阶段筛选", ["全部"] + [f"{t.stage} {t.chapter}" for t in DRAWING_TEMPLATES], key="p13_filter")

    import pandas as pd
    if stage_filter == "全部":
        filtered = DRAWING_TEMPLATES
    else:
        code = stage_filter[:2]
        filtered = get_templates_by_stage(code)

    rows = [{"阶段": t.stage, "图纸名称": t.name, "章节": t.chapter, "说明": t.description} for t in filtered]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    render_summary_cards([
        {"value": len(DRAWING_TEMPLATES), "title": "预设模板", "desc": "全流程图纸提示词模板"},
        {"value": len(set(t.stage for t in DRAWING_TEMPLATES)), "title": "覆盖阶段", "desc": "已配置模板的阶段数"},
    ])

    selected_tmpl = st.selectbox("选择模板生成完整提示词", [t.name for t in filtered], key="p13_tmpl")
    if selected_tmpl:
        tmpl = next(t for t in DRAWING_TEMPLATES if t.name == selected_tmpl)
        prompt_text, _ = build_drawing_prompt(selected_tmpl)
        st.text_area("数据注入后的提示词", value=prompt_text, height=300)
        if st.button("🧠 调用 Gemma 4 生成", type="primary", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_drawing_prompt_with_llm(selected_tmpl, model=model_tag)
            st.text_area("完整 Image 2.0 提示词", value=result, height=400)
            st.download_button("📥 下载", result, file_name=f"{selected_tmpl}_prompt.md", mime="text/markdown", use_container_width=True)

elif selected_sub == "🖼️ AIGC 效果图管理":
    render_section_intro("AIGC 效果图管理", "管理和展示历次 AIGC 推演生成的效果图。", eyebrow="Gallery")
    gallery_path = Path("data/aigc_gallery")
    if gallery_path.exists():
        images = sorted(gallery_path.glob("*.png")) + sorted(gallery_path.glob("*.jpg"))
        if images:
            render_summary_cards([
                {"value": len(images), "title": "效果图", "desc": "AIGC 推演历史画廊"},
            ])
            cols = st.columns(3)
            for idx, img in enumerate(images):
                with cols[idx % 3]:
                    st.image(str(img), caption=img.stem, use_container_width=True)
        else:
            st.info("暂无效果图。请在 AIGC 推演页面生成后自动归档。")
    else:
        st.info("data/aigc_gallery 目录不存在。效果图将在 AIGC 推演时自动创建。")

elif selected_sub == "📤 成果导出中心":
    render_section_intro("成果导出中心", "导出全流程成果文件。", eyebrow="Export Center")

    # 导则文本
    guideline = load_stage_output("12", "design_guideline", "")
    if guideline:
        st.download_button("📥 城市设计导则 (Markdown)", guideline, file_name="城市设计导则.md", use_container_width=True)
        try:
            from src.utils.document_generator import generate_official_word_doc
            wb = generate_official_word_doc(title="伪满皇宫周边街区微更新规划导则", text_content=guideline)
            if wb:
                st.download_button("📥 红头公文 (Word)", wb, file_name="规划导则_红头.docx", use_container_width=True)
        except Exception:
            pass
    else:
        st.info("请先在 Stage 12 生成导则文本。")

    # MPI 报告
    mpi = load_stage_output("05", "mpi_ranking", [])
    if mpi:
        import pandas as pd
        csv = pd.DataFrame(mpi).to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 MPI 评估排行榜 (CSV)", csv, file_name="MPI_Report.csv", use_container_width=True)

    # 诊断报告
    diagnosis = load_stage_output("05", "diagnosis_report", "")
    if diagnosis:
        st.download_button("📥 前期诊断报告 (Markdown)", diagnosis, file_name="诊断报告.md", use_container_width=True)

st.markdown("---")
render_stage_summary(
    stage_code="13",
    title="成果交付完整度",
    findings=[
        {"point": f"预设 {len(DRAWING_TEMPLATES)} 个数据驱动的图纸提示词模板", "evidence": "覆盖图册结构全部章节"},
        {"point": "支持 Markdown/Word/CSV 多格式成果导出", "evidence": "导出中心统一管理"},
        {"point": "全部图纸提示词均基于研究区域实际数据自动注入", "evidence": "空间引擎 + 诊断引擎数据源"},
    ],
    methodology="基于全流程数据总线的成果汇总与导出",
    implication="支撑图册制作、展板编排和答辩汇报的完整成果交付",
)
