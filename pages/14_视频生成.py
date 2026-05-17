import streamlit as st
from pathlib import Path

from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.workflow.stage_data_bus import load_stage_output, render_evidence_chain_bar
from src.workflow.stage_keys import SK
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="14 视频生成", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="视频生成与全流程分镜",
    description="自动抓取各阶段诊断与推演数据，为您生成精准的页面录屏分镜脚本与旁白台词，辅助完成汇报视频录制。",
    eyebrow="Stage 14",
    tags=["智能分镜系统", "数据注入", "脚本导出"],
)
render_evidence_chain_bar("14", ["05", "07", "08", "09", "10", "13", "14"])

st.info("💡 **架构升级说明**：考虑到网页动态交互录屏的复杂性，系统现采用【智能导演分镜模式】。它会将您前序分析出的核心矛盾、潜力地块、空间结构等真实数据无缝编织进旁白词中，您只需对照脚本操作鼠标录制即可获得专业汇报视频。")

# --- 抓取各阶段真实数据 ---
diag_report = load_stage_output("05", SK.DIAGNOSIS_REPORT, "（暂未执行问题诊断）")
mpi_ranking = load_stage_output("05", SK.MPI_RANKING, [])
top_plot_name = mpi_ranking[0]['name'] if mpi_ranking else "（未识别核心地块）"

vision = load_stage_output("06", SK.DESIGN_CONCEPT, "数字孪生·古今共振")
strategy = load_stage_output("07", SK.STRATEGY_MATRIX, "（未形成设计策略）")
spatial_struct = load_stage_output("08", SK.SPATIAL_STRUCTURE, "（未定义空间结构）")
traffic_sys = load_stage_output("09", SK.TRAFFIC_SYSTEM, "（未生成交通方案）")

# --- 构建脚本 ---
script_md = f"""# 🎬 伪满皇宫周边街区更新平台 - 全流程汇报分镜脚本

> **系统提示**：这是一份为您量身定制的录屏导演脚本。**操作动作**指导您的鼠标和页面切换，**旁白台词**中已经自动注入了您在本平台前序阶段实盘推演出的真实数据。

---

## 【00:00 - 00:20】开场与任务认知
- **操作动作**：打开平台首页 (01 任务解读)，缓慢滚动展示任务红线边界图。
- **旁白台词**：各位评委老师好，欢迎审阅我们的城市更新智能推演平台。本项目位于长春市宽城区，我们面对的是一片紧邻伪满皇宫的复杂老旧街区。如何平衡历史保护与城市复兴，是我们平台重点解决的课题。

## 【00:20 - 00:50】数据底座与多维摸底
- **操作动作**：切换至 `04 现状分析` 页面，点击左侧边栏的几个图层开关（如：路网、建筑肌理），展示 3D 底座的交互。
- **旁白台词**：平台建立了强大的数字孪生底座。在这里，我们汇聚了 POI、路网、建筑轮廓以及基于 AI 视觉识别的街景绿视率。通过这些精细的三维数据底板，我们将模糊的城市现状进行了极致的量化。

## 【00:50 - 01:30】智能问题诊断
- **操作动作**：进入 `05 问题诊断` 页面，鼠标高亮 MPI 综合评价的雷达图，并在排行榜上停留。
- **旁白台词**：在深度诊断环节，平台并没有停留在表面。基于测算，系统得出当前的诊断结论是：**{str(diag_report)[:60]}...**。特别值得注意的是，系统利用 MPI 更新潜力模型，精准锚定了 **{top_plot_name}** 等极具潜力的关键地块，为后续的靶向更新指明了方向。

## 【01:30 - 02:10】目标定位与多方博弈
- **操作动作**：进入 `07 设计策略`，展示三主体博弈沙盘。
- **旁白台词**：在确立了“**{vision[:30]}**”的愿景后，我们引入了政府、开发商、民众三方博弈模型。平台推演出的核心策略是：**{str(strategy)[:80]}...**，以此达成多主体利益最大化的共识。

## 【02:10 - 02:50】总体城市设计推演
- **操作动作**：进入 `08 总体城市设计`，操作用地分布调整滑块，展示动态图表的变化。
- **旁白台词**：在总规层面，平台通过大模型推演构建了“**{str(spatial_struct)[:50]}...**”的空间骨架。更重要的是，我们开发了交互式的用地沙盘，不同用地配比对城市活力、环境品质的冲击均可实现实时推演。

## 【02:50 - 03:20】专项系统深化
- **操作动作**：进入 `09 专项系统设计`，下拉展示交通、慢行或公共空间面板。
- **旁白台词**：针对专项支撑系统，平台输出的策略强调量化落实。以交通系统为例，方案明确：**{str(traffic_sys)[:70]}...**。这些系统如同毛细血管，支撑起了整体骨架。

## 【03:20 - 04:10】重点地段 AIGC 重塑
- **操作动作**：进入 `10 重点地段深化`，展示人群行为画像，接着快速切换到 `13 成果表达` 展示最终自动生成的图册和图框。
- **旁白台词**：宏观战略最终必须落地。针对之前识别出的重点地段，系统反推了精细的人群画像和空间指标。在最终的成果表达中，我们摒弃了传统的臃肿管线，采用 Python 矢量制图与 Web大语言模型画质增强相结合的人机协同流，最后由系统自动封装标准的红头工程图框，实现了从数据到图纸的完美闭环。

## 【04:10 - 04:30】结尾与展望
- **操作动作**：回到平台首页，或者展示 `12 城市设计导则` 的导出界面。
- **旁白台词**：以上就是通过我们开发的智能推演平台所完成的全案演示。通过数据驱动、AI 辅助和人机协同，我们正在探索一种更加理性、高效、透明的城市设计新范式。感谢聆听！

---
"""

st.markdown("### 📝 您专属的视频录制分镜脚本")
st.markdown(
    """
    <div style="background-color: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; height: 400px; overflow-y: auto;">
        """ + script_md.replace("\n", "<br>") + """
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])
with col1:
    st.download_button(
        "📥 下载完整 Markdown 脚本",
        script_md,
        file_name="项目展示分镜脚本.md",
        mime="text/markdown",
        **stretch_width(st.download_button)
    )

with col2:
    st.info("🎙️ **配音建议**：您可以使用剪映的「文本朗读」功能，或者使用免费的 Edge-TTS，将上述加粗的旁白转化为真人解说音频，然后在剪辑软件中对齐您的录屏画面。")
