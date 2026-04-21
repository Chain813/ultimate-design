import streamlit as st
import time
import json
from src.engines.core_engine import call_llm_engine, call_llm_engine_stream, is_demo_mode, get_plot_diagnostics, generate_policy_matrix
from src.ui.ui_components import render_top_nav, render_engine_status_alert

st.set_page_config(page_title="LLM 多方参与决策 - 数字议事厅", layout="wide")
render_top_nav()
render_engine_status_alert()

# --- CSS 样式注入 ---
st.markdown("""
<style>
    .chat-card {
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 5px solid #007bff;
        background-color: rgba(255,255,255,0.05);
    }
    .role-label {
        font-weight: bold;
        color: #007bff;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }
    .resident { border-left-color: #ff9800; }
    .developer { border-left-color: #4caf50; }
    .planner { border-left-color: #2196f3; }
    .policy-card {
        background: rgba(99, 102, 241, 0.06);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
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
    model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M")
    temp = st.slider("决策倾向 (Temperature)", 0.0, 1.0, 0.7)
    st.markdown("---")
    st.markdown("### 👥 当前席位：")
    st.markdown("1. **老王 (居民代表)**: 关注环境、配套、拆迁")
    st.markdown("2. **赵总 (开发商)**: 关注收益、密度、商业")
    st.markdown("3. **李工 (规划专家)**: 关注文脉、规范、公益")

    st.markdown("---")
    st.markdown("### 🔧 辅助工具")
    enable_policy_check = st.checkbox("📜 启用政策合规校验", value=True, key="enable_policy")

# ==========================================
# 📍 地块议题自动生成 (Phase 4 新增)
# ==========================================
st.markdown("---")
st.markdown("### 📍 智能议题生成器")

auto_col, manual_col = st.columns([1, 1])

with auto_col:
    st.markdown("#### 🤖 基于诊断数据自动生成议题")
    diagnostics = get_plot_diagnostics()
    if diagnostics:
        plot_names = [d["name"] for d in diagnostics]
        selected_plot = st.selectbox("选择重点地块：", plot_names, key="p4_plot_sel")
        
        selected_diag = next(d for d in diagnostics if d["name"] == selected_plot)
        
        # 展示地块概况
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("面积", f"{selected_diag['area_ha']} ha")
        m2.metric("MPI", f"{selected_diag['mpi_score']}")
        m3.metric("POI", f"{selected_diag['poi_count']}")
        m4.metric("GVI", f"{selected_diag['gvi_mean']}")

        # 自动生成议题
        auto_strategies = {
            "高MPI (>70)": f"提议对{selected_plot}进行整体功能更新，引入社区服务中心、口袋公园和文创商业，同时保留原有历史建筑立面。",
            "低GVI (<20)": f"提议在{selected_plot}增设垂直绿化和口袋公园，将绿视率从当前 {selected_diag['gvi_mean']}% 提升至 25% 以上。",
            "多POI (>5)": f"提议优化{selected_plot}的商业业态布局，引导低端批发市场向文旅零售转型，提升街区品质与经济活力。",
            "默认": f"提议对{selected_plot}({selected_diag['area_ha']}ha) 实施微更新改造，主要策略包括风貌修缮、功能织补和慢行系统优化。",
        }

        if selected_diag["mpi_score"] > 70:
            auto_proposal = auto_strategies["高MPI (>70)"]
        elif selected_diag["gvi_mean"] < 20 and selected_diag["gvi_mean"] > 0:
            auto_proposal = auto_strategies["低GVI (<20)"]
        elif selected_diag["poi_count"] > 5:
            auto_proposal = auto_strategies["多POI (>5)"]
        else:
            auto_proposal = auto_strategies["默认"]
        
        if st.button("📝 生成智能议题", key="auto_gen_btn"):
            st.session_state["p4_proposal"] = auto_proposal
            st.rerun()
    else:
        st.warning("暂无地块诊断数据")

with manual_col:
    st.markdown("#### ✍️ 手动输入议题")

# --- 主交互区 ---
proposal = st.text_area("✍️ 请输入当前的微更新构思或争议点：", 
                      value=st.session_state.get("p4_proposal", ""),
                      placeholder="例如：提议将铁北旧厂房整体改造为电竞创业园，并拆除外围少量围墙以增加通达性...",
                      height=100)

# ==========================================
# 📜 政策合规校验面板 (Phase 4 新增)
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
        # 定义角色 Prompt
        cot_instruction = "\n\n请在回复时，先用【思考过程】标签展示你的推理链条（考虑了哪些因素、权衡了什么），然后再给出【正式回复】。格式如下：\n【思考过程】...\n【正式回复】..."
        roles = {
            "🏠 居民代表 (老王)": {
                "system": "你是一位在长春铁北生活了30年的老街坊老王。你性格感性，说话带有一点东北味。你关注的是生活便利、拆迁安置是否合理，以及家门口那棵老树能不能保住。你对过度商业化持怀疑态度。" + cot_instruction,
                "class": "resident"
            },
            "💰 开发商 (赵总)": {
                "system": "你是一位负责长春历史街区开发的商业项目策划人赵总。你极其理性，满脑子都是投资收益比、容积率、首层商业租金。你希望引入高溢价的现代业态，认为只有商业成功才能真正救活老区。" + cot_instruction,
                "class": "developer"
            },
            "📐 规划专家 (李工)": {
                "system": "你是一位参与长春150公顷微更新项目的规划师李工。你说话严谨、学院派。你关注的是《名城保护条例》、中轴线视廊、历史肌理的缝合。你试图在各方利益中寻找一种符合上位规划的科学平衡点。" + cot_instruction,
                "class": "planner"
            }
        }

        # 容器
        chat_container = st.container()
        results = {}

        for name, role_cfg in roles.items():
            with chat_container:
                st.markdown(f"""
                <div class="chat-card {role_cfg['class']}">
                    <div class="role-label">{name}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 🚀 V3.0 流式打字机输出
                stream = call_llm_engine_stream(
                    prompt=f"针对以下城市更新提案，请发表你的真实看法和建议：\n提案内容：{proposal}",
                    system_prompt=role_cfg["system"],
                    model=model_tag
                )
                resp = st.write_stream(stream)
                results[name] = resp

                # 解析思维链与正式回复
                if isinstance(resp, str) and "【思考过程】" in resp and "【正式回复】" in resp:
                    parts = resp.split("【正式回复】")
                    cot_text = parts[0].replace("【思考过程】", "").strip()
                    if cot_text:
                        with st.expander(f"🧠 {name} 思维链展示"):
                            st.markdown(cot_text)

                time.sleep(0.3)

        st.markdown("---")
        st.subheader("📋 数字化多方协商报告 (预览)")
        summary_prompt = f"请总结以下三方的观点冲突点与潜在共识，并给出最终的政策建议：\n{str(results)}"
        
        # 🚀 V3.0 综合报告也使用流式输出
        summary_stream = call_llm_engine_stream(
            prompt=summary_prompt,
            system_prompt="你是一位高级城市更新政策研究员。",
            model=model_tag
        )
        summary = st.write_stream(summary_stream)
        
        st.toast("🎉 多方博弈评估报告已生成！请审阅下载。", icon="🤝")

        # --- 结构化报告导出 (Phase 4 增强) ---
        if isinstance(summary, str):
            # 组装结构化 Markdown 报告
            report_md = f"""# 🏛️ 数字城市议事厅 — 多方协商报告

## 📋 议题
{proposal}

## 🗣️ 各方发言记录
"""
            for role_name, role_resp in results.items():
                report_md += f"\n### {role_name}\n{role_resp}\n"
            
            report_md += f"\n---\n## 📊 综合评估与政策建议\n{summary}\n"
            
            # 添加政策合规矩阵
            if enable_policy_check:
                matrix = generate_policy_matrix(proposal)
                if matrix:
                    report_md += "\n---\n## 📜 政策合规对照矩阵\n\n"
                    report_md += "| 来源 | 条款摘要 | 合规性 |\n| --- | --- | --- |\n"
                    for item in matrix:
                        report_md += f"| {item['source']} | {item['clause'][:80]}... | {item['compliance_note']} |\n"

            st.download_button(
                "📥 导出结构化协商报告 (Markdown)",
                report_md,
                file_name="consultation_report.md",
                use_container_width=True
            )

