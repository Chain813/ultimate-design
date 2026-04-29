import streamlit as st
from src.ui.design_system import render_section_intro
from src.engines.drawing_prompt_templates import get_templates_by_stage, build_drawing_prompt, generate_drawing_prompt_with_llm

def render_drawing_prompt_ui(stage_code: str, key_prefix: str, stage_title: str):
    """
    Render a unified Drawing Prompt Generation UI component with pre-upload fields
    and DeepSeek API integration.
    """
    render_section_intro(f"{stage_title}图纸提示词", "基于研究区域数据生成 Image 2.0 专业图纸提示词。", eyebrow="Drawing Prompts")
    
    with st.sidebar:
        model_tag = st.text_input("DeepSeek 模型标签", value="deepseek-v4-pro", key=f"{key_prefix}_model")
    
    templates = get_templates_by_stage(stage_code)
    
    if templates:
        selected_tmpl = st.selectbox("选择图纸模板", [t.name for t in templates], key=f"{key_prefix}_draw_sel")
        tmpl = next(t for t in templates if t.name == selected_tmpl)
        st.markdown(f"**图纸说明：** {tmpl.description}")
        
        # UI for Image/Mask uploads before generating prompt
        st.markdown("#### 📤 渲染底图与合成图框上传")
        st.caption("在调用大模型生成提示词与后续发送渲染管线前，请先设置好相应的图像素材。")
        
        col_img1, col_img2, col_img3 = st.columns(3)
        with col_img1:
            st.file_uploader(
                "1. AIGC 底图 / 线稿 (Base Map)", 
                type=["png", "jpg", "jpeg"], 
                key=f"{key_prefix}_base_map",
                help="用于图生图 (Img2Img) 或 ControlNet 线稿提取的基础图像。"
            )
        with col_img2:
            st.file_uploader(
                "2. 研究范围蒙版 (Scope Mask)", 
                type=["png", "jpg", "jpeg"], 
                key=f"{key_prefix}_scope_mask",
                help="尺寸必须与底图完全一致。黑白蒙版，白色区域代表允许 AI 重绘 (Inpainting) 的有效研究范围。"
            )
        with col_img3:
            st.file_uploader(
                "3. 标准排版图框 (Title Block)", 
                type=["png", "pdf", "jpg", "jpeg"], 
                key=f"{key_prefix}_title_block",
                help="此文件将不会送入 AI。当 AI 绘图完毕后，系统会将其作为透明图层强制叠加在最上层，保护文字不被 AI 修改。"
            )
            
        st.markdown("---")
        
        prompt_text, _ = build_drawing_prompt(selected_tmpl)
        st.text_area("数据注入后的系统提示词片段", value=prompt_text, height=200, key=f"{key_prefix}_preview")
        
        if st.button("🧠 调用 DeepSeek 生成完整提示词", type="primary", use_container_width=True, key=f"{key_prefix}_gen"):
            with st.spinner("DeepSeek 推理生成中..."):
                result = generate_drawing_prompt_with_llm(selected_tmpl, model=model_tag)
            st.text_area("完整 Image 2.0 英文提示词 (可直接拷贝至 Midjourney/SD)", value=result, height=350, key=f"{key_prefix}_result")
    else:
        st.info("暂无本阶段图纸模板。")
