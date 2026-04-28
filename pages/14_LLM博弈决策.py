import streamlit as st
import time
import json
import os
import plotly.graph_objects as go
from src.engines.llm_engine import call_llm_engine, call_llm_engine_stream
from src.engines.site_diagnostic_engine import get_plot_diagnostics, generate_policy_matrix
from src.engines.drawing_prompt_engine import (
    BOOK_CHAPTERS,
    UPLOAD_CHANNELS,
    UPLOAD_REFERENCE_TEXT,
    ImagePromptRequest,
    build_image_prompt,
    get_drawing_profile,
    revise_prompt_by_rating,
)
from src.ui.chart_theme import apply_plotly_polar_theme
from src.ui.design_system import (
    render_page_banner,
    render_section_intro,
    render_summary_cards,
)
from src.ui.app_shell import (
    render_engine_status_alert,
    render_top_nav,
)
from src.utils.runtime_flags import is_demo_mode

st.set_page_config(page_title="LLM 多方参与决策 - 数字议事厅", layout="wide")
render_top_nav()
render_engine_status_alert()

# 🚀 算力管家：自动检测并提供一键启动 Ollama/SD
from src.utils.daemon_manager import render_daemon_control_panel
render_daemon_control_panel()

# 📊 RAG 知识库预热（带进度条）
if "rag_warmed" not in st.session_state:
    with st.status("⏳ 正在预热 RAG 政策知识库...", expanded=True) as rag_status:
        st.write("📂 加载政策文档切片...")
        from src.engines.rag_engine import get_cached_db_embeddings
        db_emb, _ = get_cached_db_embeddings()
        if db_emb:
            st.write(f"✅ 已加载 {len(db_emb)} 条政策向量，语义检索就绪")
        else:
            st.write("⚠️ 向量模型未就绪，将使用关键词匹配模式")
        rag_status.update(label="✅ RAG 知识库预热完成", state="complete", expanded=False)
    st.session_state["rag_warmed"] = True

if "issue_archive" not in st.session_state:
    st.session_state["issue_archive"] = []

render_page_banner(
    title="数字城市议事厅",
    description="以五阶段循证链路串联问题诊断、案例借鉴、设计理念、多主体博弈和成果导则，把政策约束、角色分歧和空间策略放进同一套协商界面。",
    eyebrow="Page 04",
    tags=["RAG 政策检索", "三角色协商", "五阶段证据链"],
    metrics=[
        {"value": 5, "label": "推演阶段", "meta": "从前期分析到最终成果导则"},
        {"value": 3, "label": "核心角色", "meta": "居民、开发商、规划师三方立场"},
        {"value": "已预热" if st.session_state.get("rag_warmed") else "未就绪", "label": "政策知识库", "meta": "用于协商前的合规校验"},
        {"value": len(st.session_state["issue_archive"]), "label": "议题归档", "meta": "当前会话已保存的历史议题数量"},
    ],
)
render_summary_cards(
    [
        {"value": "证据链驱动", "title": "前序结果承接", "desc": "每一阶段输出会自动传递到下一阶段，不再重复录入。"},
        {"value": "政策约束在线", "title": "RAG 合规校验", "desc": "协商前先检索规划与保护条款，减少空泛表态。"},
        {"value": "角色冲突显性化", "title": "多主体博弈", "desc": "让居民、开发商和规划师的分歧直接映射为空间策略。"},
    ]
)

# --- CSS 样式注入 (巅峰版 Glassmorphism 角色卡片) ---
st.markdown("""
<style>
    /* 🎭 Glassmorphism 角色卡片 */
    .role-card {
        position: relative;
        padding: 16px 18px;
        border-radius: 14px;
        margin-bottom: 14px;
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        overflow: hidden;
    }
    .role-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 14px 14px 0 0;
    }
    .role-card.resident { border-left: 4px solid #f59e0b; }
    .role-card.resident::before { background: linear-gradient(90deg, #f59e0b, transparent); }
    .role-card.developer { border-left: 4px solid #10b981; }
    .role-card.developer::before { background: linear-gradient(90deg, #10b981, transparent); }
    .role-card.planner { border-left: 4px solid #6366f1; }
    .role-card.planner::before { background: linear-gradient(90deg, #6366f1, transparent); }

    .role-header {
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 10px;
    }
    .role-avatar {
        width: 38px; height: 38px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px;
    }
    .role-name {
        font-size: 14px; font-weight: 700; color: #e2e8f0;
    }
    .role-stance {
        font-size: 10px; color: #94a3b8; font-weight: 400;
    }
    .role-content {
        font-size: 13px; color: #e2e8f0; line-height: 1.7;
    }

    /* 📋 议题档案袋 */
    .issue-archive {
        background: rgba(99, 102, 241, 0.06);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 9px;
        padding: 8px 12px;
        margin-bottom: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .issue-archive:hover {
        border-color: rgba(99, 102, 241, 0.5);
        background: rgba(99, 102, 241, 0.1);
    }

    /* 📜 政策条文卡 */
    .policy-card {
        background: rgba(99, 102, 241, 0.06);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    
    /* 🗳️ 共识度仪表 */
    .consensus-bar {
        height: 6px; border-radius: 3px;
        background: rgba(99, 102, 241, 0.15);
        margin-top: 6px; overflow: hidden;
    }
    .consensus-fill {
        height: 100%; border-radius: 3px;
        transition: width 1s ease;
    }
</style>
""", unsafe_allow_html=True)

if is_demo_mode():
    st.success("🎭 演示模式已激活 — 将使用预置角色回复，无需 Ollama 服务。")

# --- 侧边栏配置 ---
with st.sidebar:
    st.header("⚙️ 决策引擎设置")
    model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M",
                              help="填写您通过 ollama pull 下载的模型全称。例如 gemma4:e2b-it-q4_K_M")
    temp = st.slider("决策倾向 (Temperature)", 0.0, 1.0, 0.7,
                     help="数值越高，角色的回答越具有创造性和发散性；数值越低，回答越保守和确定。一般建议 0.6-0.8。")
    st.markdown("---")
    st.markdown("### 👥 议事代表席位")
    st.markdown("""
    <div style="font-size:12px; color:#94a3b8; line-height:1.7;">
        <b style="color:#f59e0b;">1. 🏠 居委会老王</b>：在铁北住了30年的社区代表<br>
        <b style="color:#10b981;">2. 💰 开发商赵总</b>：负责片区商业化开发运营<br>
        <b style="color:#6366f1;">3. 📐 规划师李工</b>：城乡规划编制首席专家
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔧 辅助工具")
    enable_policy_check = st.checkbox("📜 启用政策合规校验", value=True, key="enable_policy",
                                      help="开启后，系统会在协商前自动检索 RAG 知识库中的法规条文，对提案进行合规性预审。")

    # 议题历史档案袋
    st.markdown("---")
    st.markdown("### 📂 议题档案袋")
    if st.session_state["issue_archive"]:
        for i, item in enumerate(st.session_state["issue_archive"]):
            with st.expander(f"📋 议题 #{i+1}: {item['title'][:20]}...", expanded=False):
                st.markdown(f"<div style='font-size:12px; color:#cbd5e1;'>{item['content']}</div>", unsafe_allow_html=True)
    else:
        st.caption('暂无历史议题。点击「生成智能议题」后将自动归档。')


def _detect_prompt_source_channels():
    """Infer which reference channels are already available in the local project data."""
    detected = []
    checks = [
        ("卫星底图", ["data/无纹理2D卫星图.png"]),
        ("红线边界图", ["data/shp/Boundary_Scope.geojson", "data/shp/Key_Plots_District.json"]),
        ("GIS专题图", ["data/GIS高对比度图纸.png", "data/土地利用分类图.png"]),
        ("建筑肌理图", ["data/shp/Building_Footprints.geojson"]),
        ("图例参考图", ["data/土地利用分类图.png", "data/GIS高对比度图纸.png"]),
    ]
    for channel, paths in checks:
        if any(os.path.exists(path) for path in paths):
            detected.append(channel)
    return detected


def _default_legend_for_profile(profile):
    if profile.precision == "一级精度":
        return "研究范围边界、五个重点地块、主要道路、建筑轮廓、用地或更新分类、保留/改造/新建控制分类"
    if profile.precision == "二级精度":
        return "评价等级、问题类型、策略类型、保护分区、更新潜力分区、公共空间与生态节点"
    return "输入、诊断、评价、推演、输出、反馈闭环；历史重点、问题预警、生态公共空间、AI推演节点"


def _render_upload_channel_picker(profile):
    detected_channels = _detect_prompt_source_channels()
    st.caption("系统会把本地已有数据与本次上传文件合并判断。未上传或未确认的资料不会被写入严格参考说明。")
    selected_channels = st.multiselect(
        "已确认可用于本图的资料通道",
        UPLOAD_CHANNELS,
        default=[channel for channel in detected_channels if channel in UPLOAD_CHANNELS],
        help="可直接勾选项目 data 目录中已有的数据，也可在下方上传临时参考图。",
        key="p4_prompt_confirmed_channels",
    )
    if profile.required_uploads:
        st.info("当前图纸建议/必须资料：" + "、".join(profile.required_uploads))

    uploaded_channels = set(selected_channels)
    with st.expander("固定上传通道（可选，文件仅用于确认本次提示词引用）", expanded=False):
        cols = st.columns(2)
        for idx, channel in enumerate(UPLOAD_CHANNELS):
            with cols[idx % 2]:
                files = st.file_uploader(
                    channel,
                    type=["png", "jpg", "jpeg", "webp", "pdf", "geojson", "json", "csv", "xlsx"],
                    accept_multiple_files=True,
                    key=f"p4_prompt_upload_{channel}",
                    help=UPLOAD_REFERENCE_TEXT.get(channel, ""),
                )
                if files:
                    uploaded_channels.add(channel)
    return list(uploaded_channels)


def _render_image_prompt_assistant():
    render_section_intro(
        "图纸提示词助手",
        "按照现有数据、阶段分析结果和上传资料完整性，生成可复制到 ChatGPT Image 2.0 的单张图纸提示词。",
        eyebrow="Image 2.0 Prompt",
    )

    s1 = st.session_state.get("stage1_output", "")
    s2 = st.session_state.get("stage2_output", "")
    s3 = st.session_state.get("stage3_output", "")
    s4 = st.session_state.get("stage4_output", "")
    selected_proposal = st.session_state.get("p4_selected_proposal", "")
    voting_scores = st.session_state.get("p4_voting_scores", {})

    ready_count = sum(1 for item in [s1, s2, s3, s4] if item)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("已读取阶段成果", f"{ready_count}/4")
    m2.metric("图纸生成方式", "提示词")
    m3.metric("图像模型调用", "不调用")
    m4.metric("缺失拦截", "开启")

    chapter_options = list(BOOK_CHAPTERS.keys())
    default_chapter_index = chapter_options.index("04 策略生成篇")

    st.markdown("#### 1. 图纸选择")
    c1, c2, c3 = st.columns([1.15, 1.25, 0.9])
    with c1:
        chapter = st.selectbox(
            "图册章节",
            chapter_options,
            index=default_chapter_index,
            key="p4_prompt_chapter",
        )
    drawing_options = BOOK_CHAPTERS[chapter]
    default_drawing = "总体策略图" if "总体策略图" in drawing_options else drawing_options[0]
    with c2:
        drawing_name = st.selectbox(
            "图纸名称",
            drawing_options,
            index=drawing_options.index(default_drawing),
            key=f"p4_prompt_drawing_{chapter}",
        )
    profile = get_drawing_profile(drawing_name)
    with c3:
        output_scene = st.selectbox(
            "输出场景",
            ["A3横版图册", "A1竖版展板", "方案汇报PPT"],
            key="p4_prompt_output_scene",
        )

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("图纸类型", profile.drawing_type)
    p2.metric("精度等级", profile.precision)
    p3.metric("真实数据", "必须" if profile.needs_real_data else "可选")
    p4.metric("AI发挥", "允许" if profile.allows_ai_expression else "受限")

    st.markdown("#### 2. 底图与资料")
    uploaded_channels = _render_upload_channel_picker(profile)

    st.markdown("#### 3. 必要信息")
    f1, f2 = st.columns([1, 1])
    with f1:
        aspect_ratio = st.selectbox(
            "画面比例",
            ["A3横版", "A1竖版", "16:9横版", "4:3横版"],
            key="p4_prompt_aspect",
        )
        layout_structure = st.selectbox(
            "版式结构",
            [
                "问题-策略-空间响应三栏结构",
                "地图主图 + 右侧图例 + 底部信息框",
                "环形闭环结构",
                "横向流程结构",
                "左侧结论栏 + 中央主图 + 右侧图例栏",
            ],
            key="p4_prompt_layout",
        )
        main_expression = st.text_area(
            "本图主要表达",
            value="将阶段四多主体博弈形成的问题-策略对应关系转译为图纸，突出共识策略、空间落位、政策依据和实施优先级。",
            height=92,
            key="p4_prompt_main_expression",
        )
        legend_content = st.text_area(
            "图例内容",
            value=_default_legend_for_profile(profile),
            height=92,
            key="p4_prompt_legend",
        )
    with f2:
        must_include = st.text_area(
            "必须出现的内容",
            value="研究范围边界、五个重点地块、伪满皇宫、长春站、伊通河、主要道路、问题-策略-空间响应标签。",
            height=92,
            key="p4_prompt_must_include",
        )
        key_plots = st.text_area(
            "重点地块 / 空间对象",
            value="五个重点地块、伪满皇宫周边街区、长春站TOD联系、伊通河生态联系。",
            height=92,
            key="p4_prompt_key_plots",
        )
        design_strategy = st.text_area(
            "设计策略",
            value=(s4[:520] if s4 else s3[:520] if s3 else "以保护优先、功能织补、慢行缝合、公共空间补足和智慧治理为核心策略。"),
            height=120,
            key="p4_prompt_design_strategy",
        )

    with st.expander("高级内容与文字规则", expanded=False):
        a1, a2 = st.columns(2)
        with a1:
            analysis_conclusion = st.text_area(
                "分析结论",
                value=(s1[:420] if s1 else "数据不足处使用占位符，不生成具体统计数值。"),
                height=100,
                key="p4_prompt_analysis_conclusion",
            )
            emphasized_problem = st.text_area(
                "需要强调的问题",
                value="用地混杂、交通割裂、公共空间不足、历史风貌保护与商业开发之间的冲突。",
                height=80,
                key="p4_prompt_problem",
            )
            emphasized_advantage = st.text_area(
                "需要强调的优势",
                value="伪满皇宫历史文化资源、长春站TOD潜力、伊通河生态联系、老城复兴示范价值。",
                height=80,
                key="p4_prompt_advantage",
            )
        with a2:
            avoid_content = st.text_area(
                "需要避免的内容",
                value="不要虚构边界、道路、地块、用地分类、统计数据、政策名称和大段说明文字。",
                height=100,
                key="p4_prompt_avoid",
            )
            mark_as_schematic = st.checkbox(
                "数据不足时标注“示意”",
                value=True,
                key="p4_prompt_schematic",
            )
            use_existing_results = st.checkbox(
                "嵌入页面4现有阶段结果",
                value=True,
                key="p4_prompt_use_existing",
            )
            text_rules = st.text_area(
                "文字规则",
                value="中文文字使用微软雅黑风格，英文辅助使用 Times New Roman 风格，只生成清晰标题和少量关键词；信息不全处使用占位符，避免乱码。",
                height=100,
                key="p4_prompt_text_rules",
            )

    evidence_blocks = {
        "阶段一前期诊断": s1,
        "阶段二案例借鉴": s2,
        "阶段三设计理念": s3,
        "阶段四博弈共识": s4,
        "当前微更新提案": selected_proposal,
        "角色共识度": json.dumps(voting_scores, ensure_ascii=False) if voting_scores else "",
    }

    request = ImagePromptRequest(
        chapter=chapter,
        drawing_name=drawing_name,
        drawing_type=profile.drawing_type,
        aspect_ratio=aspect_ratio,
        output_scene=output_scene,
        uploaded_channels=uploaded_channels,
        main_expression=main_expression,
        must_include=must_include,
        legend_content=legend_content,
        key_plots=key_plots,
        design_strategy=design_strategy,
        analysis_conclusion=analysis_conclusion,
        emphasized_problem=emphasized_problem,
        emphasized_advantage=emphasized_advantage,
        avoid_content=avoid_content,
        layout_structure=layout_structure,
        text_rules=text_rules,
        mark_as_schematic=mark_as_schematic,
        use_existing_results=use_existing_results,
        evidence_blocks=evidence_blocks,
    )

    st.markdown("#### 4. 完整性检查与生成")
    if st.button("生成 ChatGPT Image 2.0 图纸提示词", type="primary", use_container_width=True, key="p4_prompt_generate"):
        result = build_image_prompt(request)
        st.session_state["p4_image_prompt_result"] = result
        st.session_state.pop("p4_image_prompt_revised", None)

    result = st.session_state.get("p4_image_prompt_result")
    if result:
        for notice in result.notices:
            st.warning(notice) if not result.can_generate else st.info(notice)
        if result.missing_items:
            st.markdown("当前缺少：" + "、".join(result.missing_items))
        if not result.can_generate:
            st.error("因此暂不生成提示词。请补齐上述资料或必要字段后重新生成。")
            return
        if result.template_only:
            st.info("已按“视觉表达模板提示词”输出：不会生成具体热力、评价等级或统计结论。")
        st.text_area("完整 Image 2.0 提示词", value=result.prompt, height=430, key="p4_prompt_output")
        st.download_button(
            "下载提示词 Markdown",
            result.prompt,
            file_name=f"{result.profile.name}_Image2_prompt.md",
            mime="text/markdown",
            use_container_width=True,
        )

        st.markdown("#### 5. 成图评级与提示词修正")
        r1, r2 = st.columns([0.85, 1.15])
        with r1:
            rating = st.radio(
                "生成图片后评级",
                ["A级：可直接放入图册", "B级：需要轻微后期修改", "C级：只适合作为背景或灵感", "D级：不可用，需要重生成"],
                key="p4_prompt_rating",
            )
        with r2:
            issue_types = st.multiselect(
                "问题类型",
                ["文字不准", "文字乱码", "边界不准", "图例不准", "颜色不统一", "信息太密", "图面太杂", "画面太空", "风格不一致", "清晰度不足", "数据不真实"],
                key="p4_prompt_issue_types",
            )
        if st.button("根据评级修正提示词", use_container_width=True, key="p4_prompt_revise"):
            revised = revise_prompt_by_rating(result.prompt, rating, issue_types)
            st.session_state["p4_image_prompt_revised"] = revised
            if rating.startswith("A级"):
                st.session_state["p4_accepted_prompt_style"] = revised
                st.success("已标记为可用版本，后续相似图纸可继承该提示词结构。")

        revised_prompt = st.session_state.get("p4_image_prompt_revised")
        if revised_prompt:
            st.text_area("修正后提示词", value=revised_prompt, height=430, key="p4_prompt_revised_output")


subpage = st.query_params.get("sub", "多主体利益协商")

if subpage == "动态共识雷达":
    render_section_intro("动态共识雷达与策略归集", "独立查看多主体协商后的共识度雷达图和问题-策略归集结果。", eyebrow="Consensus Radar")
    if "p4_voting_scores" in st.session_state and "stage4_output" in st.session_state:
        voting_scores = st.session_state["p4_voting_scores"]
        summary = st.session_state["stage4_output"]
        r_col, t_col = st.columns([1, 2])
        with r_col:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=list(voting_scores.values())+[list(voting_scores.values())[0]], 
                theta=list(voting_scores.keys())+[list(voting_scores.keys())[0]], 
                fill='toself', fillcolor='rgba(99,102,241,0.15)', 
                line=dict(color='#818cf8', width=2)
            ))
            apply_plotly_polar_theme(fig, title="多主体共识度", height=350, radial_range=[0, 100], accent_color="#818cf8")
            st.plotly_chart(fig, use_container_width=True)
        with t_col:
            st.markdown(summary)
    else:
        st.warning("⚠️ 暂无共识数据。请先在左侧边栏返回【多主体利益协商】页面，并在“阶段四”中完成 AI 博弈推演。")
    st.stop()

P4_MODE_OPTIONS = [
    "📊 阶段一：前期分析",
    "📚 阶段二：方案借鉴",
    "💡 阶段三：设计理念",
    "⚖️ 阶段四：问题-策略对应",
    "🖼️ 图纸提示词助手",
    "🎯 阶段五：空间成果方案"
]
SUBPAGE_TO_MODE = {
    "多主体利益协商": "⚖️ 阶段四：问题-策略对应",
    "阶段一：前期分析": "📊 阶段一：前期分析",
    "阶段二：方案借鉴": "📚 阶段二：方案借鉴",
    "阶段三：设计理念": "💡 阶段三：设计理念",
    "阶段四：问题-策略对应": "⚖️ 阶段四：问题-策略对应",
    "图纸提示词助手": "🖼️ 图纸提示词助手",
    "空间成果方案": "🎯 阶段五：空间成果方案",
    "📊 阶段一：前期分析": "📊 阶段一：前期分析",
    "📚 阶段二：方案借鉴": "📚 阶段二：方案借鉴",
    "💡 阶段三：设计理念": "💡 阶段三：设计理念",
    "⚖️ 阶段四：问题-策略对应": "⚖️ 阶段四：问题-策略对应",
    "🖼️ 图纸提示词助手": "🖼️ 图纸提示词助手",
    "🎯 阶段五：空间成果方案": "🎯 阶段五：空间成果方案",
}
target_mode = SUBPAGE_TO_MODE.get(subpage)
if target_mode and st.session_state.get("p4_last_sub_param") != subpage:
    st.session_state["p4_tab_mode"] = target_mode
    st.session_state["p4_last_sub_param"] = subpage

if target_mode:
    p4_mode = target_mode
else:
    p4_mode = st.session_state.get("p4_tab_mode", "⚖️ 阶段四：问题-策略对应")
    if p4_mode not in P4_MODE_OPTIONS:
        p4_mode = "⚖️ 阶段四：问题-策略对应"
st.session_state["p4_tab_mode"] = p4_mode

st.markdown("---")
if p4_mode == "📊 阶段一：前期分析":
    render_section_intro("阶段一：前期数据诊断与问题清单生成", "自动读取第 1、2 实验室的 MPI / GVI / POI 数据，生成可引用的问题诊断报告。", eyebrow="Stage 01")

    diagnostics = get_plot_diagnostics()
    if diagnostics:
        plot_names = [d["name"] for d in diagnostics]
        selected_plot = st.selectbox("选择重点地块：", plot_names, key="p4_s1_plot")
        selected_diag = next(d for d in diagnostics if d["name"] == selected_plot)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("面积", f"{selected_diag['area_ha']} ha")
        m2.metric("MPI", f"{selected_diag['mpi_score']}")
        m3.metric("POI", f"{selected_diag['poi_count']}")
        m4.metric("GVI", f"{selected_diag['gvi_mean']}")

        if st.button("🔬 生成前期问题诊断报告", type="primary", key="s1_btn"):
            with st.status("🔬 AI 正在诊断...", expanded=True) as status:
                st.write("📊 注入 MPI/GVI/POI 数据至 Prompt...")
                prompt = f"""你是长春宽城区铁北片区的城市更新规划顾问。
基于以下来自本平台第 1、2 实验室的真实诊断数据：
- 地块名称：{selected_plot}
- 面积：{selected_diag['area_ha']} 公顷
- 微更新潜力指数（MPI）：{selected_diag['mpi_score']}（参照：>70 为高潜力）
- 周边 POI 设施数：{selected_diag['poi_count']}
- 绿视率（GVI）：{selected_diag['gvi_mean']}%（参照：GB50180-2018 要求绿地率≥30%）

请生成一份【前期问题诊断报告】。要求：
1. 必须列出 4-6 个具体问题，每个问题格式为：
   【问题编号】问题名称
   【数据依据】引用上述具体数据指标
   【政策依据】引用《长春市历史文化名城保护条例》或《宽城区城市更新三年行动计划》中的条文
   【严重程度】高/中/低
2. 最后给出问题优先级排序
3. 结合开题报告中指出的四大核心痛点：用地混杂(中车厂区空置率40%)、交通割裂、老龄化率30%、环境品质匮乏"""
                sys_prompt = "你是一位扎根长春铁北片区的资深城市规划诊断师。输出必须严格引用具体数据和政策条文编号，禁止空洞定性描述。"
                st.write("🤖 调用本地大模型生成中...")
                status.update(label="🤖 AI 正在生成诊断报告...", expanded=True)
            stream = call_llm_engine_stream(prompt=prompt, system_prompt=sys_prompt, model=model_tag)
            result = st.write_stream(stream)
            if isinstance(result, str) and len(result) > 50:
                st.session_state["stage1_output"] = result
                st.toast("✅ 阶段一完成！", icon="📊")
                st.rerun()
    else:
        st.warning("暂无地块诊断数据。")

    if st.session_state.get("stage1_output"):
        st.markdown("#### 📋 阶段一诊断报告")
        st.markdown(st.session_state["stage1_output"])
        if st.button("🗑️ 清除阶段一结果并重新生成", key="s1_clear"):
            del st.session_state["stage1_output"]
            st.rerun()

elif p4_mode == "📚 阶段二：方案借鉴":
    render_section_intro("阶段二：开题报告案例自动提取与对标分析", "自动读取 `docs/开题报告_案例摘要.md` 的案例摘要，并与阶段一问题清单做对标。", eyebrow="Stage 02")

    case_context = ""
    case_path = "docs/开题报告_案例摘要.md"
    if os.path.exists(case_path):
        with open(case_path, "r", encoding="utf-8") as f:
            case_context = f.read()
        st.success(f"✅ 已加载案例文件：{case_path}（{len(case_context)} 字）")
    else:
        st.error("❌ 未找到案例摘要文件，请确认 docs/开题报告_案例摘要.md 存在。")

    stage1_data = st.session_state.get("stage1_output", "（阶段一尚未执行，将使用开题报告中的四大痛点作为替代输入）")

    if st.button("📖 生成案例对标分析报告", type="primary", key="s2_btn"):
        prompt = f"""请基于以下开题报告中收集的 4 个案例借鉴：
{case_context[:3000]}

以及本项目阶段一诊断出的核心问题：
{stage1_data[:2000]}

生成一份【案例对标分析报告】。要求：
1. 对每个案例逐一分析，格式为：
   【案例名称】
   【核心经验】该案例最值得借鉴的 1-2 个做法
   【对标问题】该经验可以对应解决阶段一中的哪个具体问题
   【本地化建议】结合伪满皇宫周边的实际情况，该经验如何落地
2. 最后给出【案例经验综合提炼】，提炼出 3-4 条可直接指导本项目的核心设计原则"""
        sys_prompt = "你是一位城市更新领域的比较研究专家。分析必须紧密结合长春铁北片区的实际情况，禁止泛泛而谈。"
        stream = call_llm_engine_stream(prompt=prompt, system_prompt=sys_prompt, model=model_tag)
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 50:
            st.session_state["stage2_output"] = result
            st.toast("✅ 阶段二完成！", icon="📚")
            st.rerun()

    if st.session_state.get("stage2_output"):
        st.markdown("#### 📋 阶段二对标分析报告")
        st.markdown(st.session_state["stage2_output"])
        if st.button("🗑️ 清除并重新生成", key="s2_clear"):
            del st.session_state["stage2_output"]
            st.rerun()

elif p4_mode == "💡 阶段三：设计理念":
    render_section_intro("阶段三：设计理念提炼", "融合前两阶段成果和开题报告主题，提炼可直接落地的核心设计理念与策略。", eyebrow="Stage 03")
    s1 = st.session_state.get("stage1_output", "")
    s2 = st.session_state.get("stage2_output", "")
    case_ctx = ""
    if os.path.exists("docs/开题报告_案例摘要.md"):
        with open("docs/开题报告_案例摘要.md", "r", encoding="utf-8") as f:
            case_ctx = f.read()
    if st.button("💡 生成设计理念报告", type="primary", key="s3_btn"):
        prompt = f"""基于：
【阶段一·问题】{s1[:1500] if s1 else '用地混杂(空置率40%)、交通割裂、老龄化率30%、环境品质匮乏'}
【阶段二·案例】{s2[:1500] if s2 else '恩宁路微改造、白塔寺数字织补、国王十字站城融合、巴塞罗那超级街区'}
【开题报告主题】"数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计"
【四大策略】{case_ctx[case_ctx.find('五、四大设计策略'):] if '五、四大设计策略' in case_ctx else '精准感知、风貌生成、路网重构、社会协同'}

请生成【设计理念报告】：
1. 提炼 1 个总体设计理念
2. 提出 4 条策略，每条含：【策略名称】【理论依据】【解决的问题】【案例支撑】【空间方向】"""
        stream = call_llm_engine_stream(prompt=prompt, system_prompt="你是城乡规划学术导师，精通循证规划。输出必须有理有据。", model=model_tag)
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 50:
            st.session_state["stage3_output"] = result
            st.toast("✅ 阶段三完成！", icon="💡")
            st.rerun()
    if st.session_state.get("stage3_output"):
        st.markdown("#### 📋 阶段三设计理念报告")
        st.markdown(st.session_state["stage3_output"])
        if st.button("🗑️ 清除并重新生成", key="s3_clear"):
            del st.session_state["stage3_output"]
            st.rerun()

elif p4_mode == "⚖️ 阶段四：问题-策略对应":
    render_section_intro("阶段四：多主体博弈与问题-策略对应", "让三类角色围绕阶段三策略展开协商，并生成带依据和空间落位的对应表。", eyebrow="Stage 04")
    
    # --- ✨ 智能议题生成 (Phase 4 新增) ---
    st.markdown("#### ✨ 智能议题推荐")
    
    # 预置高质量议题
    preset_agendas = [
        {
            "title": "🏭 铁北工业遗产：保留原真性还是彻底商业化？",
            "content": "铁北老厂区拥有大面积红砖锯齿形厂房。规划师主张严格保护其历史风貌，限制内部改造幅度；而开发商认为必须允许加建玻璃幕墙、提升容积率以植入电竞和餐饮业态，否则无法收回投资。居民则更关心改造后是否对周边免费开放公共空间。"
        },
        {
            "title": "🏘️ 老旧小区改造：拆除违建补绿还是增加停车位？",
            "content": "老旧小区普遍面临空间极度局促的问题。目前绿视率不足 10%。社区提议拆除私搭乱建，全部用于增加绿化和口袋公园；但部分有车居民及物业强烈要求将腾退空间铺设透水砖，划定为停车位。如何平衡环境品质与停车刚需？"
        },
        {
            "title": "🚶 交通微循环：街道步行化改造与车流效率的冲突",
            "content": "为了提升 15 分钟生活圈品质，规划方案建议将主街部分路段压缩车道，拓宽慢行步道，并增加沿街外摆空间。但这可能导致早晚高峰周边路网拥堵加剧。居民担心出行不便，商家则支持步行化以增加客流。"
        }
    ]
    
    s1 = st.session_state.get("stage1_output", "")
    s2 = st.session_state.get("stage2_output", "")
    s3 = st.session_state.get("stage3_output", "")
    
    if "p4_generated_agendas" not in st.session_state:
        st.session_state["p4_generated_agendas"] = []
        
    if st.button("🔍 基于前序证据链智能生成议题", key="btn_gen_agendas"):
        if is_demo_mode():
            st.session_state["p4_generated_agendas"] = preset_agendas
            st.toast("演示模式：已加载预置更新议题", icon="💡")
        else:
            with st.spinner("🧠 正在结合前三阶段成果生成专属议题..."):
                prompt = f"""
基于以下循证推演的前三阶段成果：
【阶段一】{s1[:800]}
【阶段二】{s2[:800]}
【阶段三】{s3[:800]}

请针对长春铁北/伪满皇宫周边地块，生成 3 个具有争议性、多方利益冲突、且亟待通过博弈解决的“更新议题”。
要求：
1. 每个议题应包含一个明确的标题（title）和 100 字左右的背景说明（content）。
2. 涉及历史风貌保护与现代商业的矛盾、居民民生需求与开发成本的平衡等。
3. 请严格只输出一段 JSON 数组，格式如下：
[
  {{"title": "议题标题1", "content": "议题背景说明1"}},
  {{"title": "议题标题2", "content": "议题背景说明2"}},
  {{"title": "议题标题3", "content": "议题背景说明3"}}
]
"""
                sys_prompt = "你是一个专门输出 JSON 的机器人。不要输出任何除了 JSON 之外的说明文本或 markdown 标记。"
                try:
                    # 避免在生成大段内容时使用流式
                    raw_result = call_llm_engine(prompt=prompt, system_prompt=sys_prompt, model=model_tag)
                    import json
                    clean_result = raw_result.strip()
                    if clean_result.startswith("```json"):
                        clean_result = clean_result[7:]
                    if clean_result.startswith("```"):
                        clean_result = clean_result[3:]
                    if clean_result.endswith("```"):
                        clean_result = clean_result[:-3]
                    clean_result = clean_result.strip()
                    agendas = json.loads(clean_result)
                    if isinstance(agendas, list) and len(agendas) > 0:
                        st.session_state["p4_generated_agendas"] = agendas
                        st.toast("✅ 专属议题生成成功！", icon="✨")
                    else:
                        raise ValueError("JSON 结构错误")
                except Exception as e:
                    st.warning("大模型生成异常或未开启，已切换至高质量预置议题。")
                    st.session_state["p4_generated_agendas"] = preset_agendas
    
    # 渲染议题卡片
    if st.session_state["p4_generated_agendas"]:
        st.markdown("<br>", unsafe_allow_html=True)
        cols = st.columns(len(st.session_state["p4_generated_agendas"]))
        for idx, agenda in enumerate(st.session_state["p4_generated_agendas"]):
            with cols[idx]:
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 15px; height: 180px; overflow-y: auto;">
                    <div style="font-size: 14px; font-weight: 700; color: #a5b4fc; margin-bottom: 8px;">{agenda.get('title', '未命名议题')}</div>
                    <div style="font-size: 12px; color: #cbd5e1; line-height: 1.6;">{agenda.get('content', '')}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🎯 选定此议题", key=f"sel_agenda_{idx}", use_container_width=True):
                    st.session_state["p4_selected_proposal"] = agenda.get('content', '')
        st.markdown("---")

    default_proposal_value = st.session_state.get("p4_selected_proposal", s3[:300] if s3 else "")
    proposal = st.text_area("✍️ 微更新构思或争议点：", value=default_proposal_value, placeholder="例如：将铁北旧厂房改造为电竞创业园...", height=120)
    
    # 实时同步用户修改的值到 session (防止文本框锁定)
    if proposal != default_proposal_value:
        st.session_state["p4_selected_proposal"] = proposal
    if enable_policy_check and proposal:
        with st.expander("📜 政策合规校验 (RAG)", expanded=False):
            matrix = generate_policy_matrix(proposal)
            if matrix:
                for item in matrix:
                    st.markdown(f"""<div class="policy-card"><span style="color:#a5b4fc;font-weight:700;">{item['source']}</span> {item['compliance_note']}<br><span style="color:#cbd5e1;font-size:12px;">{item['clause']}</span></div>""", unsafe_allow_html=True)
    if st.button("🚀 开启多方协商推演", use_container_width=True, type="primary"):
        if not proposal:
            st.warning("请输入提案内容。")
        else:
            core_constraint = "\n\n【红线】：容积率≤1.4，限高≤18m（核心区≤9m），遵守《长春市历史文化名城保护条例》。\n"
            cot_instruction = "\n\n请用【思考过程】展示推理，【正式回复】给出立场，末行<SCORE:数值>打分(0-100)。"
            roles = {
                "🏠 老王": {"system": "你是老王，铁北住了30年的居委会代表。说话直率，偶尔东北方言。惦记菜市场、看病方便、别砍树。" + core_constraint + cot_instruction, "class": "resident", "avatar": "👴", "color": "#f59e0b", "stance_label": "社区民生优先"},
                "💰 赵总": {"system": "你是赵总，商业开发运营者。精于投资回报。想争取更高容积率但知道1.4红线。" + core_constraint + cot_instruction, "class": "developer", "avatar": "💼", "color": "#10b981", "stance_label": "商业回报导向"},
                "📐 李工": {"system": "你是李工，注册规划师。用词严谨，坚持法定红线，关注天际线视廊和修旧如旧。" + core_constraint + cot_instruction, "class": "planner", "avatar": "📐", "color": "#6366f1", "stance_label": "法定规划调停"}
            }
            results = {}
            voting_scores = {}
            memory_chain = ""
            for name, cfg in roles.items():
                st.markdown(f"""<div class="role-card {cfg['class']}"><div class="role-header"><div class="role-avatar" style="background:{cfg['color']}20;border:2px solid {cfg['color']};">{cfg['avatar']}</div><div><div class="role-name">{name}</div><div class="role-stance">立场：{cfg['stance_label']}</div></div></div></div>""", unsafe_allow_html=True)
                dp = f"针对提案发表看法：\n{proposal}"
                if memory_chain:
                    dp += f"\n\n【其他方观点，请针对反驳或妥协】：\n{memory_chain}"
                stream = call_llm_engine_stream(prompt=dp, system_prompt=cfg["system"], model=model_tag)
                resp = st.write_stream(stream)
                results[name] = resp
                if isinstance(resp, str):
                    clean = resp.split("【正式回复】")[-1].split("<SCORE:")[0].strip() if "【正式回复】" in resp else resp
                    memory_chain += f"[{name}]: {clean}\n---\n"
                    import re
                    m = re.search(r"<SCORE:\s*(\d+)\s*>", resp)
                    voting_scores[name] = max(0, min(100, int(m.group(1)) if m else 50))
                time.sleep(0.3)
            st.markdown("---")
            st.session_state["p4_voting_scores"] = voting_scores
            
            st.subheader("📊 问题-策略对应表")
            sp = f"""基于博弈记录生成Markdown表格【问题-策略对应表】：
{str(results)[:3000]}
格式：| 问题 | 策略 | 政策依据 | 空间落位 | 共识度 |"""
            stream = call_llm_engine_stream(prompt=sp, system_prompt="高级城市更新研究员。策略须在容积率≤1.4、限高≤18m约束下。", model=model_tag)
            summary = st.write_stream(stream)
            if isinstance(summary, str):
                st.session_state["stage4_output"] = summary
                st.success("✅ 阶段四完成！已生成共识度打分。请前往侧边栏【动态共识雷达】查看多维度雷达图谱。")
                st.toast("✅ 阶段四完成！", icon="⚖️")

elif p4_mode == "🖼️ 图纸提示词助手":
    _render_image_prompt_assistant()

elif p4_mode == "🎯 阶段五：空间成果方案":
    render_section_intro("阶段五：空间成果方案汇总", "汇总前四阶段结果，生成最终规划导则，并导出阶段成果文件。", eyebrow="Stage 05")
    s1 = st.session_state.get("stage1_output", "暂无")
    s2 = st.session_state.get("stage2_output", "暂无")
    s3 = st.session_state.get("stage3_output", "暂无")
    s4 = st.session_state.get("stage4_output", "暂无")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("阶段一", "✅" if s1 != "暂无" else "❌")
    c2.metric("阶段二", "✅" if s2 != "暂无" else "❌")
    c3.metric("阶段三", "✅" if s3 != "暂无" else "❌")
    c4.metric("阶段四", "✅" if s4 != "暂无" else "❌")
    if st.button("📄 生成最终规划导则", type="primary", key="s5_btn"):
        prompt = f"""基于四阶段证据链生成【规划导则成果书】：
【阶段一】{s1[:1000]}
【阶段二】{s2[:1000]}
【阶段三】{s3[:1000]}
【阶段四】{s4[:1000]}
要求：公文格式(1. 1.1 1.1.1)，含总体定位/现状/理念/分区策略/实施保障。每条策略注明数据和政策依据。容积率≤1.4、限高≤18m。"""
        stream = call_llm_engine_stream(prompt=prompt, system_prompt="长春市自然资源局首席规划师，标准行政公文格式。", model=model_tag)
        final = st.write_stream(stream)
        if isinstance(final, str) and len(final) > 100:
            st.session_state["stage5_output"] = final
            report = f"# 循证规划五阶段成果书\n\n## 阶段一\n{s1}\n\n## 阶段二\n{s2}\n\n## 阶段三\n{s3}\n\n## 阶段四\n{s4}\n\n## 阶段五\n{final}"
            st.download_button("📥 导出完整报告 (Markdown)", report, file_name="五阶段循证报告.md", use_container_width=True)
            try:
                from src.utils.document_generator import generate_official_word_doc
                wb = generate_official_word_doc(title="伪满皇宫周边街区微更新规划导则", text_content=final)
                if wb:
                    st.download_button("📥 导出红头公文 (Word)", wb, file_name="规划导则_红头.docx", use_container_width=True)
            except Exception:
                pass
            st.toast("🎉 五阶段推演完成！", icon="🎯")

