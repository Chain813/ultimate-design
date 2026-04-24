import streamlit as st
import time
import json
import os
import plotly.graph_objects as go
from src.engines.core_engine import call_llm_engine, call_llm_engine_stream, is_demo_mode, get_plot_diagnostics, generate_policy_matrix
from src.ui.ui_components import render_top_nav, render_engine_status_alert

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
        from src.engines.core_engine import get_cached_db_embeddings
        db_emb, _ = get_cached_db_embeddings()
        if db_emb:
            st.write(f"✅ 已加载 {len(db_emb)} 条政策向量，语义检索就绪")
        else:
            st.write("⚠️ 向量模型未就绪，将使用关键词匹配模式")
        rag_status.update(label="✅ RAG 知识库预热完成", state="complete", expanded=False)
    st.session_state["rag_warmed"] = True

# --- CSS 样式注入 (巅峰版 Glassmorphism 角色卡片) ---
st.markdown("""
<style>
    /* 🎭 Glassmorphism 角色卡片 */
    .role-card {
        position: relative;
        padding: 20px 24px;
        border-radius: 16px;
        margin-bottom: 18px;
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
        border-radius: 16px 16px 0 0;
    }
    .role-card.resident { border-left: 4px solid #f59e0b; }
    .role-card.resident::before { background: linear-gradient(90deg, #f59e0b, transparent); }
    .role-card.developer { border-left: 4px solid #10b981; }
    .role-card.developer::before { background: linear-gradient(90deg, #10b981, transparent); }
    .role-card.planner { border-left: 4px solid #6366f1; }
    .role-card.planner::before { background: linear-gradient(90deg, #6366f1, transparent); }

    .role-header {
        display: flex; align-items: center; gap: 12px;
        margin-bottom: 12px;
    }
    .role-avatar {
        width: 42px; height: 42px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 22px;
    }
    .role-name {
        font-size: 15px; font-weight: 700; color: #e2e8f0;
    }
    .role-stance {
        font-size: 11px; color: #94a3b8; font-weight: 400;
    }
    .role-content {
        font-size: 14px; color: #e2e8f0; line-height: 1.8;
    }

    /* 📋 议题档案袋 */
    .issue-archive {
        background: rgba(99, 102, 241, 0.06);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
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
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    
    /* 🗳️ 共识度仪表 */
    .consensus-bar {
        height: 6px; border-radius: 3px;
        background: rgba(99, 102, 241, 0.15);
        margin-top: 8px; overflow: hidden;
    }
    .consensus-fill {
        height: 100%; border-radius: 3px;
        transition: width 1s ease;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ 数字城市议事厅：多主体博弈推演")
st.info("基于 **Gemma 4** 本地大模型，模拟长春城市更新中的多方利益交锋与政策共识。")
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
    if "issue_archive" not in st.session_state:
        st.session_state["issue_archive"] = []
    
    if st.session_state["issue_archive"]:
        for i, item in enumerate(st.session_state["issue_archive"]):
            with st.expander(f"📋 议题 #{i+1}: {item['title'][:20]}...", expanded=False):
                st.markdown(f"<div style='font-size:12px; color:#cbd5e1;'>{item['content']}</div>", unsafe_allow_html=True)
    else:
        st.caption('暂无历史议题。点击「生成智能议题」后将自动归档。')

# ==========================================
# 📍 五阶段循证规划推演工作流
# ==========================================
st.markdown("---")

# --- 五阶段流程可视化 ---
st.markdown("""
<div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px 24px; margin-bottom: 20px;">
<div style="color: #a5b4fc; font-weight: 800; font-size: 15px; margin-bottom: 14px; text-align: center;">🔬 循证规划五阶段推演工作流 <span style="font-size: 11px; color: #64748b; font-weight: 400;">（每阶段输出自动传递至下一阶段，形成完整证据链）</span></div>
<div style="display: flex; align-items: flex-start; justify-content: center; gap: 6px; flex-wrap: nowrap;">

<div style="flex: 1; text-align: center; min-width: 0;">
<div style="background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.4); border-radius: 10px; padding: 10px 6px; margin-bottom: 6px;">
<div style="font-size: 18px;">📊</div>
<div style="font-size: 11px; font-weight: 700; color: #e2e8f0;">1. 前期分析</div>
</div>
<div style="font-size: 9px; color: #94a3b8; line-height: 1.4;">读取MPI/GVI/POI<br>诊断数据，输出<br><b style="color:#a5b4fc;">问题清单</b></div>
</div>

<div style="color: #818cf8; font-size: 18px; padding-top: 16px;">→</div>

<div style="flex: 1; text-align: center; min-width: 0;">
<div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 10px 6px; margin-bottom: 6px;">
<div style="font-size: 18px;">📚</div>
<div style="font-size: 11px; font-weight: 700; color: #e2e8f0;">2. 方案借鉴</div>
</div>
<div style="font-size: 9px; color: #94a3b8; line-height: 1.4;">自动提取开题报告<br>4个案例，输出<br><b style="color:#34d399;">对标分析</b></div>
</div>

<div style="color: #818cf8; font-size: 18px; padding-top: 16px;">→</div>

<div style="flex: 1; text-align: center; min-width: 0;">
<div style="background: rgba(236, 72, 153, 0.15); border: 1px solid rgba(236, 72, 153, 0.4); border-radius: 10px; padding: 10px 6px; margin-bottom: 6px;">
<div style="font-size: 18px;">💡</div>
<div style="font-size: 11px; font-weight: 700; color: #e2e8f0;">3. 设计理念</div>
</div>
<div style="font-size: 9px; color: #94a3b8; line-height: 1.4;">融合前两阶段+<br>保护条例，提炼<br><b style="color:#ec4899;">核心策略</b></div>
</div>

<div style="color: #818cf8; font-size: 18px; padding-top: 16px;">→</div>

<div style="flex: 1; text-align: center; min-width: 0;">
<div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 10px; padding: 10px 6px; margin-bottom: 6px;">
<div style="font-size: 18px;">⚖️</div>
<div style="font-size: 11px; font-weight: 700; color: #e2e8f0;">4. 问题-策略</div>
</div>
<div style="font-size: 9px; color: #94a3b8; line-height: 1.4;">三角色博弈协商<br>问题→策略→依据<br><b style="color:#f59e0b;">对应表</b></div>
</div>

<div style="color: #818cf8; font-size: 18px; padding-top: 16px;">→</div>

<div style="flex: 1; text-align: center; min-width: 0;">
<div style="background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4); border-radius: 10px; padding: 10px 6px; margin-bottom: 6px;">
<div style="font-size: 18px;">🎯</div>
<div style="font-size: 11px; font-weight: 700; color: #e2e8f0;">5. 空间成果</div>
</div>
<div style="font-size: 9px; color: #94a3b8; line-height: 1.4;">全链路汇总生成<br>规划导则+红头<br><b style="color:#a78bfa;">成果文件</b></div>
</div>

</div>
</div>
""", unsafe_allow_html=True)

p4_mode = st.radio("⬇️ 选择推演阶段", [
    "📊 阶段一：前期分析",
    "📚 阶段二：方案借鉴",
    "💡 阶段三：设计理念",
    "⚖️ 阶段四：问题-策略对应",
    "🎯 阶段五：空间成果方案"
], horizontal=True, key="p4_tab_mode")

st.markdown("---")
if p4_mode == "📊 阶段一：前期分析":
    st.markdown("### 📊 阶段一：前期数据诊断与问题清单生成")
    st.info("💡 本阶段自动读取第 1、2 实验室的 MPI/GVI/POI 真实数据，由 AI 生成有理有据的问题诊断报告。")

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
    st.markdown("### 📚 阶段二：开题报告案例自动提取与对标分析")
    st.info("💡 系统将自动读取 `docs/开题报告_案例摘要.md` 中的 4 个案例（2 国内 + 2 国外），结合阶段一的问题清单生成对标分析。")

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
    st.markdown("### 💡 阶段三：设计理念提炼")
    st.info("💡 融合前两阶段成果 + 开题报告设计主题，提炼核心设计理念与策略。")
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
    st.markdown("### ⚖️ 阶段四：多主体博弈 → 问题-策略对应表")
    st.info("💡 三角色围绕阶段三策略展开博弈，生成【问题→策略→依据→空间落位】对应表。")
    s3 = st.session_state.get("stage3_output", "")
    proposal = st.text_area("✍️ 微更新构思或争议点：", value=s3[:300] if s3 else "", placeholder="例如：将铁北旧厂房改造为电竞创业园...", height=120)
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
            st.subheader("📊 共识度雷达 + 问题-策略对应表")
            r_col, t_col = st.columns([1, 2])
            with r_col:
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=list(voting_scores.values())+[list(voting_scores.values())[0]], theta=list(voting_scores.keys())+[list(voting_scores.keys())[0]], fill='toself', fillcolor='rgba(99,102,241,0.15)', line=dict(color='#818cf8', width=2)))
                fig.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(range=[0,100], gridcolor='rgba(99,102,241,0.15)'), angularaxis=dict(gridcolor='rgba(99,102,241,0.15)')), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, font=dict(color='#94a3b8'))
                st.plotly_chart(fig, use_container_width=True)
            with t_col:
                sp = f"""基于博弈记录生成Markdown表格【问题-策略对应表】：
{str(results)[:3000]}
格式：| 问题 | 策略 | 政策依据 | 空间落位 | 共识度 |"""
                stream = call_llm_engine_stream(prompt=sp, system_prompt="高级城市更新研究员。策略须在容积率≤1.4、限高≤18m约束下。", model=model_tag)
                summary = st.write_stream(stream)
                if isinstance(summary, str):
                    st.session_state["stage4_output"] = summary
                    st.toast("✅ 阶段四完成！", icon="⚖️")

elif p4_mode == "🎯 阶段五：空间成果方案":
    st.markdown("### 🎯 阶段五：空间成果方案汇总")
    st.info("💡 汇总全部四阶段成果，生成最终规划导则，可导出红头 Word。")
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
                wb = generate_official_word_doc(title="伪满皇宫周边街区微更新规划导则", body_text=final)
                if wb:
                    st.download_button("📥 导出红头公文 (Word)", wb, file_name="规划导则_红头.docx", use_container_width=True)
            except Exception:
                pass
            st.toast("🎉 五阶段推演完成！", icon="🎯")

