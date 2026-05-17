"""阶段 06：目标定位 —— 全域宏观设计目标策划 + 案例借鉴。

基于前期量化诊断（Stage 05）产出的空间数据：土地利用结构、POI密度、
GVI绿视率、MPI排行等，生成覆盖全域的、落到空间上的设计目标体系。

核心输出：设计愿景、目标体系、策略方向（均以空间数据为依据）。
"""

from pathlib import Path
import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.spatial_data_injector import (
    get_full_spatial_context,
    get_landuse_summary,
    get_poi_summary,
    get_gvi_summary,
    get_key_plots_summary,
)
from src.workflow.stage_data_bus import (
    save_stage_output, load_stage_output, render_evidence_chain_bar,
)
from src.workflow.stage_keys import SK
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="06 目标定位", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

graphic_svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 200" width="100%" height="100%" style="max-width: 600px; filter: drop-shadow(0 15px 25px rgba(0,0,0,0.3));">
  <defs>
    <linearGradient id="g_base" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(30, 41, 59, 0.6)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.8)"/>
    </linearGradient>
    <linearGradient id="g_ai" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(56, 189, 248, 0.1)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.9)"/>
    </linearGradient>
    <linearGradient id="g_out" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(99, 102, 241, 0.15)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.9)"/>
    </linearGradient>
    
    <filter id="f_cyan" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="f_indigo" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <path d="M 160 50 C 220 50, 240 100, 300 100" fill="none" stroke="#475569" stroke-width="1.5" stroke-dasharray="4,3"/>
  <path d="M 160 100 L 300 100" fill="none" stroke="#38bdf8" stroke-width="2" stroke-dasharray="5,4" filter="url(#f_cyan)"/>
  <path d="M 160 150 C 220 150, 240 100, 300 100" fill="none" stroke="#475569" stroke-width="1.5" stroke-dasharray="4,3"/>
  
  <path d="M 440 100 L 500 100" fill="none" stroke="#6366f1" stroke-width="2" stroke-dasharray="5,4" filter="url(#f_indigo)"/>
  <path d="M 500 100 C 530 100, 520 60, 550 60" fill="none" stroke="#475569" stroke-width="1.5"/>
  <path d="M 500 100 C 530 100, 520 140, 550 140" fill="none" stroke="#475569" stroke-width="1.5"/>

  <rect x="10" y="35" width="150" height="30" rx="6" fill="url(#g_base)" stroke="#334155" stroke-width="1"/>
  <text x="85" y="55" fill="#94a3b8" font-size="11" font-family="sans-serif" text-anchor="middle">土地利用与建筑密度</text>

  <rect x="10" y="80" width="150" height="40" rx="8" fill="url(#g_base)" stroke="#38bdf8" stroke-width="1.5" filter="url(#f_cyan)"/>
  <text x="85" y="105" fill="#e2e8f0" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="bold">全域多源空间数据</text>

  <rect x="10" y="135" width="150" height="30" rx="6" fill="url(#g_base)" stroke="#334155" stroke-width="1"/>
  <text x="85" y="155" fill="#94a3b8" font-size="11" font-family="sans-serif" text-anchor="middle">POI/GVI 活力与品质</text>

  <rect x="300" y="65" width="140" height="70" rx="12" fill="url(#g_ai)" stroke="#38bdf8" stroke-width="2" filter="url(#f_cyan)"/>
  <text x="370" y="95" fill="#38bdf8" font-size="16" font-family="sans-serif" text-anchor="middle" font-weight="900">AI 推理中枢</text>
  <text x="370" y="118" fill="#bae6fd" font-size="11" font-family="sans-serif" text-anchor="middle">DeepSeek 大模型</text>

  <rect x="550" y="40" width="120" height="40" rx="6" fill="url(#g_out)" stroke="#6366f1" stroke-width="1.5"/>
  <text x="610" y="65" fill="#e2e8f0" font-size="12" font-family="sans-serif" text-anchor="middle" font-weight="bold">全域宏观设计目标</text>
  
  <rect x="550" y="120" width="120" height="40" rx="6" fill="url(#g_out)" stroke="#6366f1" stroke-width="1.5"/>
  <text x="610" y="145" fill="#e2e8f0" font-size="12" font-family="sans-serif" text-anchor="middle" font-weight="bold">区域经济策划体系</text>

  <circle cx="160" cy="100" r="4" fill="#38bdf8"/>
  <circle cx="300" cy="100" r="4" fill="#38bdf8"/>
  <circle cx="440" cy="100" r="4" fill="#6366f1"/>
</svg>
"""

render_page_banner(
    title="目标定位",
    description="基于全域空间数据（土地利用、POI、GVI、MPI）和前期诊断结果，"
                "制定覆盖整个研究范围的宏观设计目标与区域经济策划体系。",
    eyebrow="Stage 06",
    tags=["全域目标", "空间数据驱动", "经济策划", "案例借鉴"],
    graphic_html=graphic_svg
)
render_evidence_chain_bar("06", ["05", "06", "07"])

with st.sidebar:
    model_tag = st.selectbox(
        "DeepSeek 模型",
        ["deepseek-v4-flash", "deepseek-v4-pro"],
        index=1,  # 默认使用 Pro 进行深度策划
        key="p6_model",
        help="deepseek-v4-pro 适合深度策划，deepseek-v4-flash 适合快速迭代",
    )

SUB_OPTIONS = ["📚 案例对标分析", "🎯 全域设计目标策划"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

# ═══════════════════════════════════════════
# 空间数据面板 —— 始终显示，确保透明度
# ═══════════════════════════════════════════
with st.expander("📊 空间数据概览（驱动本阶段所有分析）", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 🏘️ 土地利用")
        st.text(get_landuse_summary())
    with c2:
        st.markdown("#### 📍 POI 分布")
        st.text(get_poi_summary())
    with c3:
        st.markdown("#### 🌿 街景品质 (GVI)")
        st.text(get_gvi_summary())

    st.markdown("#### 🏗️ 重点更新单元")
    st.text(get_key_plots_summary())

# ═══════════════════════════════════════════
# 模块一：案例对标分析
# ═══════════════════════════════════════════

if selected_sub == "📚 案例对标分析":
    render_section_intro(
        "案例对标分析",
        "读取开题报告案例摘要，与前期诊断问题做对标，"
        "提炼可落地的本地化设计原则。",
        eyebrow="Case Benchmark",
    )

    case_context = ""
    case_path = "docs/开题报告_案例摘要.md"
    if Path(case_path).exists():
        with open(case_path, "r", encoding="utf-8") as f:
            case_context = f.read()
        st.success(f"✅ 已加载案例文件（{len(case_context)} 字）")
    else:
        st.warning("⚠️ 未找到 docs/开题报告_案例摘要.md，将使用内置案例。")

    s1 = st.session_state.get("stage1_output", load_stage_output("05", SK.DIAGNOSIS_REPORT, ""))

    if st.button("📖 生成案例对标报告", type="primary", key="s2_btn", **stretch_width(st.button)):
        # 注入空间数据上下文
        spatial_ctx = get_full_spatial_context()
        prompt = f"""基于开题报告案例：{case_context[:3000]}
以及阶段一诊断问题：{s1[:2000] if s1 else '用地结构失衡、交通割裂、老龄化、环境品质匮乏'}

【研究范围空间数据】：
{spatial_ctx[:3000]}

生成【案例对标分析报告】：
1. 每个案例含【核心经验】【对标问题】【本地化建议（必须结合上述空间数据）】
2. 最后提炼 3-4 条核心设计原则
3. 每条原则必须明确其所回应的空间短板（如"居住用地占比过半""绿视率不足15%"等具体数据）"""
        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="城市更新比较研究专家。分析紧密结合伪满皇宫周边街区实际空间数据。",
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 50:
            st.session_state["stage2_output"] = result
            save_stage_output("06", SK.CASE_BENCHMARK, result)

    if st.session_state.get("stage2_output"):
        st.markdown("#### 📋 案例对标报告")
        st.markdown(st.session_state["stage2_output"])


# ═══════════════════════════════════════════
# 模块二：全域设计目标策划
# ═══════════════════════════════════════════

elif selected_sub == "🎯 全域设计目标策划":
    render_section_intro(
        "全域设计目标策划",
        "融合前期诊断、空间数据与案例经验，提炼覆盖整个研究范围的"
        "设计愿景、分层目标体系和区域经济策划方向。",
        eyebrow="Strategic Visioning",
    )

    s1 = st.session_state.get("stage1_output", load_stage_output("05", SK.DIAGNOSIS_REPORT, ""))
    s2 = st.session_state.get("stage2_output", load_stage_output("06", SK.CASE_BENCHMARK, ""))

    if st.button("🎯 生成全域设计目标", type="primary", key="s3_btn", **stretch_width(st.button)):
        spatial_ctx = get_full_spatial_context()
        prompt = f"""基于：
【前期诊断问题】{s1[:1500] if s1 else '用地结构失衡、交通割裂、老龄化、环境品质匮乏'}
【案例借鉴经验】{s2[:1500] if s2 else '广州永庆坊微改造、北京白塔寺数字织补、伦敦国王十字站城融合'}
【主题】"数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计"

【研究范围全域空间数据】：
{spatial_ctx[:4000]}

请生成覆盖**整个研究范围**的【全域设计目标策划报告】：

一、总体设计愿景（1段，50-100字）

二、分层目标体系（4-5条），每条须包含：
  - 目标名称
  - 所回应的具体空间短板（必须引用上述空间数据中的具体数字）
  - 对应的策略方向
  - 空间落位指引（具体到哪些地块或区域）

三、区域经济策划方向：
  - 如何利用伪满皇宫的文化IP与区位禀赋，进行全域维度的业态重构与空间织补
  - 如何盘活整个研究范围的经济，并使其文化/经济辐射力扩散至全区乃至全城
  - 具体的政策抓手和产业导入路径

四、土地利用优化建议：
  - 基于当前土地利用结构（居住用地占比{'>50%'}、商业活力不足等），提出功能调整方向
  - 每条建议必须标注影响范围和预期效果"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt=(
                "你是一位资深城乡规划学术导师，精通循证规划和区域经济策划。"
                "请严格基于提供的空间量化数据进行分析，禁止空泛陈述。"
                "每一个目标和建议都必须落到空间上，引用具体的数据指标。"
            ),
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 50:
            st.session_state["stage3_output"] = result
            save_stage_output("06", SK.DESIGN_CONCEPT, result)

    if st.session_state.get("stage3_output"):
        st.markdown("#### 📋 全域设计目标策划报告")
        st.markdown(st.session_state["stage3_output"])

st.markdown("---")
render_stage_summary(
    stage_code="06",
    title="全域设计愿景与目标体系",
    findings=[
        {"point": "借鉴广州永庆坊、北京白塔寺、伦敦国王十字等案例经验", "evidence": "开题报告案例摘要数据库"},
        {"point": "基于全域土地利用结构（居住50%+商业14%+办公10%）提出功能优化方向", "evidence": "landuse_clipped.geojson 空间统计"},
        {"point": "提炼'数字孪生·古今共振'的总体设计理念，每条目标落到具体空间", "evidence": "融合前期诊断与全域空间数据"},
        {"point": "制定区域经济策划方向：利用伪满皇宫文化IP盘活区域经济", "evidence": "POI/GVI数据 + 区位分析"},
    ],
    methodology="基于 DeepSeek API 的循证推演，融合案例对标与全域空间量化数据驱动",
    implication="为设计策略（Stage 07）的多主体协商提供了理念框架、目标体系和空间落位指引",
)
