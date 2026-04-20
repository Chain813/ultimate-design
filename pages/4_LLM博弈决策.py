import streamlit as st
import time
from core_engine import call_llm_engine, is_demo_mode
from ui_components import render_top_nav, render_engine_status_alert

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
</style>
""", unsafe_allow_html=True)

st.title("🏛️ 数字城市议事厅：多主体博弈推演")
st.info("基于 **Gemma 4** 本地大模型，模拟长春城市更新中的多方利益交锋与政策共识。")
if is_demo_mode():
    st.success("🎭 演示模式已激活 — 将使用预置角色回复，无需 Ollama 服务。")

# --- 侧边栏配置 ---
with st.sidebar:
    st.header("⚙️ 决策引擎设置")
    model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e4b-it-q4_K_M")
    temp = st.slider("决策倾向 (Temperature)", 0.0, 1.0, 0.7)
    st.markdown("---")
    st.markdown("### 👥 当前席位：")
    st.markdown("1. **老王 (居民代表)**: 关注环境、配套、拆迁")
    st.markdown("2. **赵总 (开发商)**: 关注收益、密度、商业")
    st.markdown("3. **李工 (规划专家)**: 关注文脉、规范、公益")

# --- 主交互区 ---
proposal = st.text_area("✍️ 请输入当前的微更新构思或争议点：", 
                      placeholder="例如：提议将铁北旧厂房整体改造为电竞创业园，并拆除外围少量围墙以增加通达性...",
                      height=100)

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

        for name, config in roles.items():
            with st.spinner(f"{name} 正在审议方案..."):
                resp = call_llm_engine(
                    prompt=f"针对以下城市更新提案，请发表你的真实看法和建议：\n提案内容：{proposal}",
                    system_prompt=config["system"],
                    model=model_tag
                )
                results[name] = resp

                # 解析思维链与正式回复
                cot_text = ""
                display_text = resp
                if "【思考过程】" in resp and "【正式回复】" in resp:
                    parts = resp.split("【正式回复】")
                    cot_text = parts[0].replace("【思考过程】", "").strip()
                    display_text = parts[1].strip() if len(parts) > 1 else resp

                with chat_container:
                    st.markdown(f"""
                    <div class="chat-card {config['class']}">
                        <div class="role-label">{name}</div>
                        <div>{display_text}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if cot_text:
                        with st.expander(f"🧠 {name} 思维链展示"):
                            st.markdown(cot_text)

                time.sleep(0.5)

        st.markdown("---")
        st.subheader("📋 数字化多方协商报告 (预览)")
        summary_prompt = f"请总结以下三方的观点冲突点与潜在共识，并给出最终的政策建议：\n{str(results)}"
        with st.spinner("AI 正在生成综合评估报告..."):
            summary = call_llm_engine(
                prompt=summary_prompt,
                system_prompt="你是一位高级城市更新政策研究员。",
                model=model_tag
            )
            st.markdown(summary)
            
            st.download_button("📥 导出协商报告 (TXT)", f"协商议题：{proposal}\n\n评估总结：\n{summary}", file_name="consultation_report.txt")
