import streamlit as st
import shutil
import io
from pathlib import Path
from PIL import Image
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.ui.module_summary import render_stage_summary
from src.workflow.stage_data_bus import load_stage_output, render_evidence_chain_bar
from src.workflow.stage_keys import SK
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="13 成果表达", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="成果表达",
    description="全新工作流：1. Python 渲染矢量数据底图 -> 2. 人机协同网页 LLM 重绘 -> 3. 自动化标准红头图框封装。",
    eyebrow="Stage 13",
    tags=["数据底图渲染", "协同重绘", "图纸封装"],
)
render_evidence_chain_bar("13", ["10", "11", "12", "13"])

SUB_OPTIONS = ["🗺️ 数据底图渲染", "🤖 协同重绘中心", "🖼️ 图册自动组装", "📤 文档导出"]
selected_sub = st.radio("工作流步骤", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

ROOT = Path(__file__).resolve().parent.parent

if selected_sub == "🗺️ 数据底图渲染":
    render_section_intro(
        "数据底图渲染中心",
        "使用 Python 直接从 GIS 空间数据库中渲染纯色块、线稿的高精度矢量底图。",
        eyebrow="Step 1: Python Maps",
    )
    st.info("此模块调用 `scripts/export_high_precision_gis.py` 基于真实的空间数据（道路、建筑、水系）出图。")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🚀 一键生成所有空间底图", type="primary", **stretch_width(st.button)):
            with st.spinner("正在启动 Python 空间渲染引擎..."):
                import subprocess
                import sys
                script_path = ROOT / "scripts" / "export_high_precision_gis.py"
                res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, encoding="utf-8")
                if res.returncode == 0:
                    st.success("高精度空间底图生成完毕！存放在 `output/high_precision/` 目录中。")
                else:
                    st.error(f"生成失败：\n{res.stderr}")
                    
    with col2:
        output_dir = ROOT / "output/high_precision"
        if output_dir.exists():
            images = list(output_dir.glob("*.png"))
            if images:
                st.markdown(f"**已生成底图 ({len(images)} 张)：**")
                for img_path in images:
                    st.image(str(img_path), caption=img_path.name, width=400)
            else:
                st.write("目前没有生成好的空间底图。")
        else:
            st.write("目前没有生成好的空间底图。")

elif selected_sub == "🤖 协同重绘中心":
    render_section_intro(
        "网页大模型协同重绘",
        "将渲染出的底图配合限定提示词，发送给网页版 Gemini/ChatGPT 视觉模型进行画质美化。",
        eyebrow="Step 2: AI Rendering",
    )
    
    st.markdown("### 提示词生成器")
    st.write("在网页端让 AI 重绘时，必须加上以下强制性提示词，防止 AI 胡乱修改数据边界：")
    
    prompt = (
        "这是一张基于 GIS 真实数据生成的城市规划矢量分析图。请你充当顶级的建筑可视化插画师，将这张图重绘为高保真的竞赛级图纸。\n\n"
        "【强制约束】\n"
        "1. 绝不允许改变任何线条的走向、粗细、位置。\n"
        "2. 绝不允许改变任何色块的边缘、形状和尺寸。\n"
        "3. 绝不允许虚构不存在的道路、建筑或文字。\n\n"
        "【渲染要求】\n"
        "仅在原图的基础上增加材质感、光影厚度（例如玻璃质感、建筑阴影）、环境光遮蔽（AO）和微弱的辉光效果。整体风格保持深色极简的高级蓝黑冷色调。保留透明背景或纯深色背景。"
    )
    st.text_area("复制此提示词", value=prompt, height=250)
    st.info("💡 提示：请下载上一阶段生成的图纸，连同上述提示词一起发送给网页端的大语言模型（推荐 Gemini 1.5 Pro / ChatGPT-4o）。")

elif selected_sub == "🖼️ 图册自动组装":
    render_section_intro(
        "自动图框封装",
        "将网页端重绘后得到的高质量渲染图上传，系统将自动使用 Python 为其套上标准工程红头图框。",
        eyebrow="Step 3: Auto Framing",
    )
    
    col_up, col_form = st.columns([1, 1])
    with col_up:
        uploaded_img = st.file_uploader("📤 上传您通过 AI 重绘后的图纸 (PNG/JPG)", type=["png", "jpg", "jpeg"])
        if uploaded_img:
            st.image(uploaded_img, caption="重绘图纸预览", use_container_width=True)
            
    with col_form:
        st.markdown("### 图框内容配置")
        drawing_title = st.text_input("图纸标题", value="核心地段空间节点分析图")
        chapter_name = st.selectbox("章节名", ["01 项目认知篇", "02 数据诊断篇", "03 价值评估篇", "04 策略生成篇", "05 总体规划篇"])
        drawing_num = st.text_input("图纸编号", value="DR-001")
        
        # 尝试调用 LLM 写总结
        if st.button("🧠 AI 生成图面说明 (基于 Stage 05/08 数据)", **stretch_width(st.button)):
            from src.engines.llm_engine import call_llm_engine
            stage_data = load_stage_output("08", SK.SPATIAL_STRUCTURE, "缺失数据")
            sys_p = "你是一个规划师，写一段 50 字以内的图面说明文字。"
            prompt_p = f"请结合之前的规划数据：{stage_data}，为名为“{drawing_title}”的图纸写一段专业的图册文字总结。"
            res = call_llm_engine(prompt_p, sys_p)
            st.session_state["p13_summary"] = res
            
        summary_text = st.text_area("图面说明 (可手动修改)", value=st.session_state.get("p13_summary", "展示本项目的总体空间意向，突显历史资源与商业活力的融合..."))
        
        legend_items = [
            ("历史保护建筑", "#FF1493"),
            ("核心商业区", "#FFA500"),
            ("生态绿地", "#A0D8EF"),
        ]
        st.caption("预设图例：历史保护建筑, 核心商业区, 生态绿地")

    st.markdown("---")
    if uploaded_img and st.button("🎨 一键生成标准图纸", type="primary", **stretch_width(st.button)):
        with st.spinner("Python PIL 正在合成工程图框..."):
            from src.engines.frame_generator import compose_framed_sheet, sheet_to_bytes
            main_img = Image.open(uploaded_img).convert("RGBA")
            framed_img = compose_framed_sheet(
                main_image=main_img,
                title=drawing_title,
                chapter=chapter_name,
                summary=summary_text,
                legend_items=legend_items,
                drawing_number=drawing_num,
                scale_text="1:5000",
            )
            img_bytes = sheet_to_bytes(framed_img)
            
        st.success("✅ 图框合成成功！")
        st.image(framed_img, caption="最终合成图纸预览", use_container_width=True)
        st.download_button(
            "📥 下载最终图纸 (高清 A3)",
            img_bytes,
            file_name=f"{drawing_num}_{drawing_title}.png",
            mime="image/png",
            **stretch_width(st.download_button)
        )

elif selected_sub == "📤 文档导出":
    render_section_intro("全案文档导出", "导出前期分析诊断与总体设计导则文本。", eyebrow="Document Export")
    
    col1, col2 = st.columns(2)
    with col1:
        guideline = load_stage_output("12", SK.DESIGN_GUIDELINE, "")
        if guideline:
            st.download_button("📥 下载城市设计导则 (Markdown)", guideline, file_name="城市设计导则.md", **stretch_width(st.download_button))
        else:
            st.info("暂无导则数据，请在 Stage 12 生成。")
            
    with col2:
        diagnosis = load_stage_output("05", SK.DIAGNOSIS_REPORT, "")
        if diagnosis:
            st.download_button("📥 下载前期诊断报告 (Markdown)", diagnosis, file_name="诊断报告.md", **stretch_width(st.download_button))
        else:
            st.info("暂无诊断数据，请在 Stage 05 生成。")

st.markdown("---")
render_stage_summary(
    stage_code="13",
    title="全栈闭环重构完备度",
    findings=[
        {"point": "完全放弃重型 SD 渲染引擎", "evidence": "极大提升出图速度，消除崩溃隐患"},
        {"point": "引入人机协同工作流", "evidence": "数据图 Python 直出，视觉美化交由网页 LLM 解决"},
        {"point": "自动化的工程排版引擎", "evidence": "内置 A3 工程图框与排版美学，实现工业级出图标准"},
    ],
    methodology="轻量化 Python 制图引擎 + Web LLM 高质渲染 + Python PIL 自动化图框",
    implication="彻底打通城乡规划专业级展板自动排版与汇报图册生产线",
)
