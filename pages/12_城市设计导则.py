"""阶段 12：城市设计导则 —— 分板块多轮深度生成 + Word 导出。

核心机制：将导则拆分为 6+ 大板块，对每个板块单独调用 DeepSeek-V4 Pro
进行深度展开（不限字数），注入本地 CSV/GIS 数据作为量化依据，
最终汇总为一份极度详实的《城市设计导则》长卷。
"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream, call_llm_engine
from src.engines.spatial_data_injector import get_full_spatial_context
from src.workflow.stage_data_bus import (
    save_stage_output, load_stage_output, render_evidence_chain_bar,
)
from src.workflow.stage_keys import SK
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="12 城市设计导则", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="城市设计导则",
    description="分板块深度生成：将导则拆分为多个专项模块，"
                "对每个模块注入真实空间数据并单独调用 DeepSeek-V4 Pro 进行深度展开，"
                "确保导则每一条都详实、精准、有理有据。",
    eyebrow="Stage 12",
    tags=["分板块生成", "数据驱动", "不限字数", "管控条文", "Word 导出"],
)
render_evidence_chain_bar("12", ["05", "06", "07", "12"])

with st.sidebar:
    model_tag = st.selectbox(
        "DeepSeek 模型",
        ["deepseek-v4-flash", "deepseek-v4-pro"],
        index=1,  # 导则必须用旗舰推理模型
        key="p12_model",
        help="城市设计导则必须使用 deepseek-v4-pro 确保深度与精准度",
    )

# ═══════════════════════════════════════════
# 导则板块定义
# ═══════════════════════════════════════════

GUIDELINE_SECTIONS = [
    {
        "id": "1",
        "title": "总则与基本原则",
        "description": "编制目的、适用范围、规划依据（含法规文件清单）、术语定义、基本设计原则",
        "data_hint": "引用 Boundary_Scope 研究范围、项目背景",
    },
    {
        "id": "2",
        "title": "空间结构与功能布局",
        "description": "空间结构规划（一核多轴多片区）、功能分区、用地规划调整建议、开发强度控制",
        "data_hint": "引用 landuse_clipped.geojson 的用地分类统计",
    },
    {
        "id": "3",
        "title": "建筑风貌控制导则",
        "description": "高度分区控制（核心区≤9m/一般区≤18m/站前区≤24m）、色彩材质规范、"
                       "屋顶形式、立面改造标准、街墙界面连续性、重点保护建筑清单",
        "data_hint": "引用 Building_Footprints 的层高统计和天际线数据",
    },
    {
        "id": "4",
        "title": "道路交通与慢行系统导则",
        "description": "道路等级规划、断面设计标准、慢行网络贯通、"
                       "公共交通组织、停车规划、断头路打通计划",
        "data_hint": "引用 road_clipped.geojson 路网结构和 Traffic_Flow.csv",
    },
    {
        "id": "5",
        "title": "公共空间与景观绿化导则",
        "description": "三级公共空间体系、绿地系统规划、口袋公园设置标准、"
                       "广场节点设计导引、街道家具规范、GVI 提升目标",
        "data_hint": "引用 GVI_Results_Analysis.csv 绿视率数据",
    },
    {
        "id": "6",
        "title": "历史文化保护与活化导则",
        "description": "保护对象清单与分级、保护范围划定、风貌协调区管控、"
                       "活化利用策略、工业遗产活化方案",
        "data_hint": "引用伪满皇宫保护规划、历史建筑名录",
    },
    {
        "id": "7",
        "title": "业态管控与经济策划导则",
        "description": "业态引导清单（鼓励/限制/禁止）、商业运营模式、"
                       "文旅产业链构建、社区商业配比标准",
        "data_hint": "引用 POI 分布数据和 Stage 07 策略矩阵",
    },
    {
        "id": "8",
        "title": "基础设施与市政工程导则",
        "description": "给排水规划、电力通信、环卫设施、消防设施、无障碍设施标准",
        "data_hint": "引用城市基础设施规范",
    },
    {
        "id": "9",
        "title": "实施保障与管理机制",
        "description": "分期实施计划要点、资金保障机制、管理机制、"
                       "公众参与渠道、监督评估体系",
        "data_hint": "引用 Stage 11 实施路径数据",
    },
]

SUB_OPTIONS = ["📜 分板块导则生成", "📊 管控指标汇总", "📄 一键导出"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")


# ═══════════════════════════════════════════
# 分板块导则生成
# ═══════════════════════════════════════════

if selected_sub == "📜 分板块导则生成":
    render_section_intro(
        "分板块深度导则生成",
        "对每个导则板块单独调用 DeepSeek-V4 Pro 进行深度展开，"
        "注入真实空间数据作为量化依据。每板块不限字数，只要求详实、精准、有据。",
        eyebrow="Multi-Dispatch Generation",
    )

    # 加载前序数据
    s1 = load_stage_output("05", SK.DIAGNOSIS_REPORT, "")
    s3 = load_stage_output("06", SK.DESIGN_CONCEPT, "")
    s4 = load_stage_output("07", SK.STRATEGY_MATRIX, "")
    spatial_ctx = get_full_spatial_context()

    # 状态显示
    c1, c2, c3 = st.columns(3)
    c1.metric("诊断报告", "✅" if s1 else "⚠️ 缺失")
    c2.metric("设计目标", "✅" if s3 else "⚠️ 缺失")
    c3.metric("策略矩阵", "✅" if s4 else "⚠️ 缺失")

    st.markdown("---")

    # 检查已生成的板块
    generated_sections = {}
    for sec in GUIDELINE_SECTIONS:
        key = f"guideline_section_{sec['id']}"
        saved = load_stage_output("12", key, "")
        if saved:
            generated_sections[sec["id"]] = saved

    # 进度显示
    total = len(GUIDELINE_SECTIONS)
    done = len(generated_sections)
    st.progress(done / total, text=f"已生成 {done}/{total} 个板块")

    # 逐板块生成
    for sec in GUIDELINE_SECTIONS:
        key = f"guideline_section_{sec['id']}"
        is_done = sec["id"] in generated_sections

        with st.expander(
            f"{'✅' if is_done else '⬜'} 第{sec['id']}章 {sec['title']}",
            expanded=not is_done,
        ):
            st.markdown(f"**内容范围：** {sec['description']}")
            st.caption(f"📊 数据依据：{sec['data_hint']}")

            if is_done:
                st.markdown(generated_sections[sec["id"]])
                if st.button(f"🔄 重新生成第{sec['id']}章", key=f"regen_{sec['id']}"):
                    st.session_state[f"force_regen_{sec['id']}"] = True
                    st.rerun()

            if not is_done or st.session_state.get(f"force_regen_{sec['id']}", False):
                if st.button(
                    f"📝 生成第{sec['id']}章：{sec['title']}",
                    type="primary",
                    key=f"gen_{sec['id']}",
                ):
                    # 清除强制重新生成标记
                    st.session_state.pop(f"force_regen_{sec['id']}", None)

                    prompt = f"""你是长春市自然资源局首席规划师，正在编写《伪满皇宫周边街区更新规划设计·城市设计导则》。

请为【第{sec['id']}章 {sec['title']}】撰写完整、详实的导则正文。

═══ 本章要求 ═══
{sec['description']}

═══ 格式规范 ═══
1. 使用标准公文格式：{sec['id']}.1 / {sec['id']}.1.1 三级编号
2. 管控条文使用「应」「宜」「可」三级强度
3. 每条管控要求注明数据来源或政策依据
4. 涉及具体指标时，给出精确数值
5. 适当使用表格呈现指标体系
6. 不限字数，只要求详实、精准、有理有据
7. 不得使用「待补充」「TBD」等占位符

═══ 空间数据（务必引用）═══
{spatial_ctx[:3000]}

═══ 前期诊断（可引用）═══
{s1[:1500] if s1 else '暂无'}

═══ 策略矩阵（可引用）═══
{s4[:1500] if s4 else '暂无'}

═══ 项目基本信息 ═══
- 项目：数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计
- 地点：长春市宽城区，约150公顷
- 核心地标：伪满皇宫（全国重点文保单位）
- 管控红线：容积率≤1.4、核心区限高≤9m、一般区≤18m、绿地率≥25%

请撰写本章完整内容。"""

                    with st.spinner(f"正在深度生成第{sec['id']}章..."):
                        stream = call_llm_engine_stream(
                            prompt=prompt,
                            system_prompt=(
                                "你是长春市自然资源局首席规划师。"
                                "请撰写严谨、规范、可交付的导则正文。"
                                "每一条管控条文都必须有数据支撑或法规依据。"
                                "不限字数，深度展开。"
                            ),
                            model=model_tag,
                        )
                        result = st.write_stream(stream)

                    if isinstance(result, str) and len(result) > 200:
                        save_stage_output("12", key, result)
                        st.success(f"第{sec['id']}章生成完成（{len(result)} 字）")
                        st.rerun()
                    else:
                        st.error("生成失败或内容过短，请重试。")

    # 汇总所有板块
    st.markdown("---")
    if done == total:
        st.success(f"🎉 全部 {total} 个板块已生成完成！")
        if st.button("📄 汇总为完整导则", type="primary", **stretch_width(st.button)):
            full_guideline = ""
            for sec in GUIDELINE_SECTIONS:
                key = f"guideline_section_{sec['id']}"
                content = load_stage_output("12", key, "")
                full_guideline += f"\n\n{'='*50}\n# 第{sec['id']}章 {sec['title']}\n{'='*50}\n\n{content}"
            save_stage_output("12", SK.DESIGN_GUIDELINE, full_guideline)
            total_chars = len(full_guideline)
            st.success(f"导则汇总完成！总计 {total_chars} 字")

            # 导出
            col_md, col_word = st.columns(2)
            with col_md:
                st.download_button(
                    "📥 导出完整导则 (Markdown)",
                    full_guideline,
                    file_name="城市设计导则_完整版.md",
                    use_container_width=True,
                )
            with col_word:
                try:
                    from src.utils.document_generator import generate_official_word_doc
                    wb = generate_official_word_doc(
                        title="伪满皇宫周边街区更新规划设计·城市设计导则",
                        text_content=full_guideline,
                    )
                    if wb:
                        st.download_button(
                            "📥 导出红头公文 (Word)",
                            wb,
                            file_name="城市设计导则_正式版.docx",
                            use_container_width=True,
                        )
                except Exception:
                    pass


# ═══════════════════════════════════════════
# 管控指标汇总
# ═══════════════════════════════════════════

elif selected_sub == "📊 管控指标汇总":
    render_section_intro("管控指标体系", "汇总城市设计导则的核心管控指标。", eyebrow="Control Indicators")

    import pandas as pd
    indicators = [
        {"管控类型": "用地功能", "管控内容": "主导功能、兼容功能、禁止功能", "控制要求": "混合用地比例≥30%", "依据": "城市更新政策"},
        {"管控类型": "开发强度", "管控内容": "容积率、建筑密度、绿地率", "控制要求": "容积率≤1.4，绿地率≥25%", "依据": "历史文化名城保护规划"},
        {"管控类型": "建筑高度", "管控内容": "高度分区、天际线控制", "控制要求": "核心区≤9m，一般区≤18m，站前≤24m", "依据": "伪满皇宫视廊保护"},
        {"管控类型": "建筑界面", "管控内容": "街墙连续性、首层开放度", "控制要求": "街墙连续率≥70%，首层通透率≥60%", "依据": "街道设计导则"},
        {"管控类型": "建筑风貌", "管控内容": "色彩、材质、屋顶形式", "控制要求": "暖灰色调为主，禁止大面积玻璃幕墙", "依据": "风貌协调区管控要求"},
        {"管控类型": "公共空间", "管控内容": "开放空间比例、可达性", "控制要求": "步行5分钟覆盖率≥80%", "依据": "完整社区建设标准"},
        {"管控类型": "绿化景观", "管控内容": "绿视率、行道树间距", "控制要求": "GVI目标≥20%，行道树间距≤8m", "依据": "GVI现状分析"},
        {"管控类型": "慢行交通", "管控内容": "步行宽度、骑行空间", "控制要求": "人行道≥2m，骑行道≥1.5m", "依据": "无障碍设计标准"},
        {"管控类型": "业态管控", "管控内容": "鼓励/限制/禁止业态", "控制要求": "文创占比≥15%，限制低端批发", "依据": "产业导入策略"},
    ]
    st.dataframe(pd.DataFrame(indicators), hide_index=True, **stretch_width(st.dataframe))


# ═══════════════════════════════════════════
# 一键导出
# ═══════════════════════════════════════════

elif selected_sub == "📄 一键导出":
    render_section_intro("导则导出", "导出已生成的完整导则。", eyebrow="Export")
    saved_guideline = load_stage_output("12", SK.DESIGN_GUIDELINE, "")
    if saved_guideline:
        st.success(f"导则已就绪（{len(saved_guideline)} 字）")
        st.download_button(
            "📥 导出完整导则 (Markdown)",
            saved_guideline,
            file_name="城市设计导则_完整版.md",
            use_container_width=True,
        )
    else:
        st.info("尚未汇总完整导则，请先在「分板块导则生成」中完成所有板块。")


st.markdown("---")
render_stage_summary(
    stage_code="12",
    title="城市设计导则体系",
    findings=[
        {"point": "导则覆盖9大板块：总则、空间、建筑、交通、景观、历史、业态、市政、实施", "evidence": "城市设计导则标准体系"},
        {"point": "核心区限高≤9m，一般区≤18m，容积率≤1.4", "evidence": "历史文化名城保护规划约束"},
        {"point": "分板块深度生成，每板块注入真实空间数据，不限字数", "evidence": "DeepSeek-V4 Pro 分发式调用"},
    ],
    methodology="分板块多轮深度生成引擎 + 全域空间数据驱动 + RAG 政策检索",
    implication="为成果表达（Stage 13）提供了可交付的导则文本和管控指标体系",
)
