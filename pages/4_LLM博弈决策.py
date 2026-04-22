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
# 📍 LLM 决策维标
# ==========================================
st.markdown("---")
p4_mode = st.radio("⬇️ 选择议事工作流", ["🗣️ 多向演进协商", "📜 政策实施制定", "🗺️ 区域发展策划"], horizontal=True, key="p4_tab_mode")

st.markdown("---")
if p4_mode == "🗣️ 多向演进协商":
    st.markdown("### 📍 智能议题生成与多向演化推演")

    auto_col, manual_col = st.columns([1, 1])

    with auto_col:
        st.markdown("#### 🤖 基于诊断数据的 AI 议题生成")
        diagnostics = get_plot_diagnostics()
        if diagnostics:
            plot_names = [d["name"] for d in diagnostics]
            selected_plot = st.selectbox("选择重点地块：", plot_names, key="p4_plot_sel",
                                         help="此处列出的地块来自 01 实验室的 MPI 评估结果，已按更新潜力排序。")
            
            selected_diag = next(d for d in diagnostics if d["name"] == selected_plot)
            
            # 展示地块概况
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("面积", f"{selected_diag['area_ha']} ha", help="地块净用地面积（公顷）")
            m2.metric("MPI", f"{selected_diag['mpi_score']}", help="微更新潜力指数：综合评价该地块实施更新改造的紧迫性与可行性。>70 为高潜力地块。")
            m3.metric("POI", f"{selected_diag['poi_count']}", help="兴趣点数量（Point of Interest）：反映周边商业及公共服务设施的密集程度。")
            m4.metric("GVI", f"{selected_diag['gvi_mean']}", help="绿视率（Green View Index）：基于街景图像分析的人眼可视绿色植被占比，参照《城市居住区规划设计标准》(GB50180-2018) 绿地率不低于 30%。")

            if st.button("🧠 生成 AI 智能议题 (接入本地大模型)", key="auto_gen_btn", type="primary"):
                with st.spinner("正在调用本地大模型生成高质量议题..."):
                    issue_prompt = f"""你是长春宽城区铁北片区的城市更新规划顾问。
基于以下地块诊断数据：
- 地块名称：{selected_plot}
- 占地面积：{selected_diag['area_ha']} 公顷
- 微更新潜力指数（MPI）：{selected_diag['mpi_score']}
- 周边 POI 数量：{selected_diag['poi_count']}
- 绿视率（GVI）：{selected_diag['gvi_mean']}%

请生成 3 个具有明显差异性的城市微更新议题方案。每个议题格式如下：
【议题标题】...
【核心矛盾】...  
【更新策略】...
【空间落位】具体到街道或建筑群名称"""

                    stream = call_llm_engine_stream(
                        prompt=issue_prompt,
                        system_prompt="你是一位扎根长春铁北片区的资深城市规划师。请结合伪满皇宫周边街区的实际空间特征，给出具体到街道和建筑群的更新方案。注意：建设控制地带容积率不超过 1.4，建筑高度不超过 18m，核心保护区不超过 9m。",
                        model=model_tag
                    )
                    generated_text = st.write_stream(stream)
                    
                    if isinstance(generated_text, str) and len(generated_text) > 20:
                        st.session_state["p4_proposal"] = generated_text
                        # 归档到侧边栏
                        st.session_state["issue_archive"].append({
                            "title": f"{selected_plot} 的 AI 议题",
                            "content": generated_text[:500]
                        })
                        st.toast("✅ 议题已生成并归档至侧边栏", icon="📂")
        else:
            st.warning("暂无地块诊断数据")

    with manual_col:
        st.markdown("#### ✍️ 手动输入议题")

    # --- 主交互区 ---
    proposal = st.text_area("✍️ 请输入当前的微更新构思或争议点：", 
                          value=st.session_state.get("p4_proposal", ""),
                          placeholder="例如：提议将铁北旧厂房整体改造为电竞创业园，并拆除外围少量围墙以增加通达性...",
                          height=120)

    # ==========================================
    # 📜 政策合规校验面板
    # ==========================================
    if enable_policy_check and proposal:
        with st.expander("📜 政策合规性校验 (RAG 法规检索)", expanded=False):
            matrix = generate_policy_matrix(proposal)
            if matrix:
                for item in matrix:
                    st.markdown(f"""
                    <div class="policy-card">
                        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                            <span style="color:#a5b4fc; font-weight:700; font-size:13px;">{item['source']}</span>
                            <span style="font-size:12px;">{item['compliance_note']}</span>
                        </div>
                        <p style="color:#cbd5e1; font-size:12px; margin:0; line-height:1.5;">{item['clause']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("未检索到相关政策条文。")

    if st.button("🚀 开启多方协商推演", use_container_width=True, type="primary"):
        if not proposal:
            st.warning("请输入提案内容以开始协商。")
        else:
            # 定义角色 Prompt (人格化 + 红线底盘)
            core_constraint = "\n\n【底盘红线（你要铭记但不必在每句话中引述）】：1. 历史保护建筑必须完整保留；2. 建设控制地带容积率 ≤ 1.4，建筑限高 ≤ 18m（核心区 ≤ 9m）；3. 遵守《长春市历史文化名城保护条例》。\n"
            cot_instruction = "\n\n请先用【思考过程】展示你的推理链，再用【正式回复】给出你的对外立场。"
            
            roles = {
                "🏠 居委会老王": {
                    "system": "你是老王，在长春铁北住了30年的社区居委会代表。你说话直率，偶尔用东北方言。你最惦记的是：菜市场别搬远了、老年人看病方便、家门口的树别砍了、拆迁补偿得到位。你对搞高端商业很反感，觉得那是给外地人消费的，跟老街坊没关系。" + core_constraint + cot_instruction,
                    "class": "resident",
                    "avatar": "👴",
                    "color": "#f59e0b",
                    "stance_label": "社区民生优先"
                },
                "💰 开发商赵总": {
                    "system": "你是赵总，负责长春铁北片区更新的商业开发运营者。你精于计算，满脑子都是投资回报比和坪效。你认为没有商业运营注入，老城活化就是空谈。你想争取更高的容积率以摊薄土地成本，但你也清楚保护区有 1.4 的红线限制不能碰。你的话语风格势利但专业。" + core_constraint + cot_instruction,
                    "class": "developer",
                    "avatar": "💼",
                    "color": "#10b981",
                    "stance_label": "商业可持续导向"
                },
                "📐 规划师李工": {
                    "system": "你是李工，吉林建筑大学城乡规划系出身的注册规划师，现就职于长春市自然资源局。你用词严谨，常引用专业术语。你坚持：任何更新动作都必须在法定红线内推进。你高度关注伪满皇宫的天际线视廊保护、历史风貌建筑的修旧如旧，以及新旧空间肌理的织补缝合。你试图在公众利益和市场资本之间寻找科学平衡点。" + core_constraint + cot_instruction,
                    "class": "planner",
                    "avatar": "📐",
                    "color": "#6366f1",
                    "stance_label": "法定规划合规"
                }
            }

            chat_container = st.container()
            results = {}
            voting_scores = {}  # 共识度评分

            for name, role_cfg in roles.items():
                with chat_container:
                    # 渲染 Glassmorphism 角色卡片
                    st.markdown(f"""
                    <div class="role-card {role_cfg['class']}">
                        <div class="role-header">
                            <div class="role-avatar" style="background: {role_cfg['color']}20; border: 2px solid {role_cfg['color']};">
                                {role_cfg['avatar']}
                            </div>
                            <div>
                                <div class="role-name">{name}</div>
                                <div class="role-stance">立场倾向：{role_cfg['stance_label']}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 🚀 流式打字机输出
                    stream = call_llm_engine_stream(
                        prompt=f"针对以下城市更新提案，以你的立场和人格发表真实看法和建议：\n提案内容：{proposal}",
                        system_prompt=role_cfg["system"],
                        model=model_tag
                    )
                    resp = st.write_stream(stream)
                    results[name] = resp

                    # 解析思维链
                    if isinstance(resp, str) and "【思考过程】" in resp and "【正式回复】" in resp:
                        parts = resp.split("【正式回复】")
                        cot_text = parts[0].replace("【思考过程】", "").strip()
                        if cot_text:
                            with st.expander(f"🧠 {name} 推理链路透视"):
                                st.markdown(cot_text)

                    # 模拟共识评分 (基于文本长度和关键词匹配)
                    if isinstance(resp, str):
                        score = 50  # 基础分
                        if "同意" in resp or "赞成" in resp or "支持" in resp: score += 20
                        if "反对" in resp or "不同意" in resp or "不行" in resp: score -= 20
                        if "妥协" in resp or "折中" in resp or "可以考虑" in resp: score += 10
                        voting_scores[name] = max(10, min(95, score))
                    
                    time.sleep(0.3)

            # ==========================================
            # 📊 多方共识度雷达图
            # ==========================================
            st.markdown("---")
            st.subheader("📊 多方共识度可视化分析")
            
            radar_col, report_col = st.columns([1, 2])
            
            with radar_col:
                categories = list(voting_scores.keys())
                values = list(voting_scores.values())
                
                fig_consensus = go.Figure()
                fig_consensus.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    fillcolor='rgba(99, 102, 241, 0.15)',
                    line=dict(color='#818cf8', width=2),
                    name='共识度'
                ))
                fig_consensus.update_layout(
                    polar=dict(
                        bgcolor='rgba(0,0,0,0)',
                        radialaxis=dict(visible=True, range=[0, 100], showticklabels=True, gridcolor='rgba(99,102,241,0.15)', color='#94a3b8'),
                        angularaxis=dict(gridcolor='rgba(99,102,241,0.15)', color='#e2e8f0'),
                    ),
                    showlegend=False,
                    title=dict(text="🗳️ 各方赞同度", font=dict(size=14, color='#a5b4fc')),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=60, r=60, t=50, b=30),
                    height=300,
                    font=dict(color='#94a3b8')
                )
                st.plotly_chart(fig_consensus, use_container_width=True)

            with report_col:
                st.subheader("📋 多方演化方向评估报告")
                summary_prompt = f"""分析以下三方在城市更新提案中的观点冲突与潜在共识。
请在报告末尾给出【3种空间演化方向】，每种方向需包含：
1. 演化主题（如"文旅复兴"/"活态宜居"/"针灸式织补"）
2. 核心空间策略（具体到街区和建筑群名称）
3. 对三方利益的影响评估

各方发言记录：
{str(results)}
"""
                summary_stream = call_llm_engine_stream(
                    prompt=summary_prompt,
                    system_prompt="你是一位高级城市更新政策研究员，站在研究区域空间尺度上进行资源调配。请确保三种演化方向都在容积率≤1.4和限高≤18m的约束下。",
                    model=model_tag
                )
                summary = st.write_stream(summary_stream)
            
            st.toast("🎉 多方博弈评估报告已生成！", icon="🤝")

            # --- 结构化报告导出 ---
            if isinstance(summary, str):
                report_md = f"""# 🏛️ 数字城市议事厅 — 多方协商报告

## 📋 议题
{proposal}

## 🗣️ 各方发言记录
"""
                for role_name, role_resp in results.items():
                    report_md += f"\n### {role_name}\n{role_resp}\n"
                
                report_md += f"\n---\n## 📊 综合评估与政策建议\n{summary}\n"
                
                if enable_policy_check:
                    matrix = generate_policy_matrix(proposal)
                    if matrix:
                        report_md += "\n---\n## 📜 政策合规对照矩阵\n\n"
                        report_md += "| 来源 | 条款摘要 | 合规性 |\n| --- | --- | --- |\n"
                        for item in matrix:
                            report_md += f"| {item['source']} | {item['clause'][:80]}... | {item['compliance_note']} |\n"

                st.download_button(
                    "📥 导出结构化推演报告 (Markdown)",
                    report_md,
                    file_name="consultation_evolution_report.md",
                    use_container_width=True
                )

elif p4_mode == "📜 政策实施制定":
    st.markdown("### 📜 政策实施制定 (Policy Formulation)")
    st.info("💡 核心算法层已挂载《长春市宽城区城市更新重点指导意见建议》及十四五规划等 248 条语料切片，将执行 RAG 加强文本生成。")
    
    policy_target = st.text_input("请输入您希望生成政策导则的目标对象或概念",
                                  value="",
                                  placeholder="例如：『中车老厂区工业遗存活化导则』",
                                  help="您可以输入具体的地块名称、建筑群组或更新策略方向，系统将结合 RAG 知识库自动生成符合长春地方规范的政策导则。")
    if st.button("📝 生成专属实操政策大纲", type="primary"):
        if not policy_target:
            st.warning("请先输入需要制定政策的目标概念。")
        else:
            rag_context = ""
            file_paths = [
                "docs/长春市宽城区城市更新重点指导意见建议.md",
                "docs/中共长春市委关于制定长春市国民经济和社会发展第十五个五年规划的建议.md"
            ]
            for p in file_paths:
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        rag_context += f.read()[:2000] + "\n\n"
            
            prompt = f"基于以下政府更新意见与五年规划文件精神：\n{rag_context}\n\n请为【{policy_target}】起草一份专业的城市微更新政策实施导则。要求结构严谨，必须符合标准公文排版规范，包括：\n- 使用加粗居中大标题\n- 使用严格的分级标号（1. 1.1 1.1.1）\n- 内容包含：1.总体导向 2. 空间底线约束（容积率≤1.4, 限高≤18m） 3. 业态引入门槛 4. 立面修缮规范 5. 历史建筑保护措施。"
            sys_prompt = "你是一位就职于长春市自然资源局的首席城市规划师，擅于撰写严谨落地的高质量政府规划实施细则。必须输出标准行政公文格式（分级标号明确，禁止使用随意的表情符号）。回答请具体到宽城区铁北片区的实际情况。"
            
            st.markdown("#### 📄 自动政策制定生成台")
            stream = call_llm_engine_stream(prompt=prompt, system_prompt=sys_prompt, model=model_tag)
            generated_text = st.write_stream(stream)
            
            if isinstance(generated_text, str) and len(generated_text) > 50:
                st.download_button(
                    "📥 导出政策导则全文 (Markdown)",
                    generated_text,
                    file_name=f"{policy_target}_实施导则.md",
                    use_container_width=True
                )

elif p4_mode == "🗺️ 区域发展策划":
    st.markdown("### 🗺️ 区域发展策划 (Regional Dev Strategy)")
    st.info("💡 该模块已成功挂载《宽城区伪满皇宫周边缺乏业态分析》，将针对当前街区的短板输出补齐与提升的策划大纲。")
    
    if st.button("🚀 启动自动化片区统筹策划", type="primary"):
        ana_path = "docs/宽城区伪满皇宫周边缺乏业态分析.md"
        biz_context = ""
        if os.path.exists(ana_path):
            with open(ana_path, "r", encoding="utf-8") as f:
                biz_context = f.read()
                
        prompt = f"基于以下最新的伪满皇宫周边业态痛点分析：\n{biz_context}\n\n请输出一份【宽城铁北伪满皇宫片区统筹发展策划书】。要求：\n1. 必须符合标准公文排版规范，包括居中加粗大标题与严格的分级标号（1. 1.1 1.1.1）。\n2. 不仅要修补空间，更要策划出2-3个爆款的'触媒项目引爆点'（如：沉浸式光影秀、站城融合MALL等），给出它们在片区中的具体空间落位逻辑与资金反哺模式。\n3. 注意：所有方案必须在容积率≤1.4和限高≤18m的约束下执行。"
        sys_prompt = "你是一位顶尖的商业地产与城市更新全案策划专家，善于以爆款项目带动老城复兴。你的方案必须具体到宽城区铁北的实际街区，且输出文本必须是格式严谨的正式项目汇报书（分级标号明确）。"
        
        st.markdown("#### 📊 片区统筹联动与触媒项目清单")
        stream = call_llm_engine_stream(prompt=prompt, system_prompt=sys_prompt, model=model_tag)
        generated_text = st.write_stream(stream)
        
        if isinstance(generated_text, str) and len(generated_text) > 50:
            st.download_button(
                "📥 导出区域发展策划书全文 (Markdown)",
                generated_text,
                file_name="区域统筹发展策划书.md",
                use_container_width=True
            )
