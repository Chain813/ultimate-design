import streamlit as st
from PIL import Image as PILImage
from src.ui.design_system import render_section_intro
from src.ui.streamlit_compat import stretch_width
from src.engines.drawing_prompt_templates import get_templates_by_stage, build_drawing_prompt, generate_drawing_prompt_with_llm, get_all_template_names
from src.engines.drawing_pipeline import DrawingPipeline


def render_drawing_prompt_ui(stage_code: str, key_prefix: str, stage_title: str):
    """
    Render a unified Drawing Prompt Generation UI component with pre-upload fields,
    DeepSeek API integration, and SD rendering.
    """
    render_section_intro(f"{stage_title}图纸提示词", "基于研究区域数据生成 Image 2.0 专业图纸提示词。", eyebrow="Drawing Prompts")

    with st.sidebar:
        model_tag = st.text_input("DeepSeek 模型标签", value="deepseek-v4-pro", key=f"{key_prefix}_model")

    templates = get_templates_by_stage(stage_code)

    if templates:
        selected_tmpl = st.selectbox("选择图纸模板", [t.name for t in templates], key=f"{key_prefix}_draw_sel")
        tmpl = next(t for t in templates if t.name == selected_tmpl)
        st.markdown(f"**图纸说明：** {tmpl.description}")

        st.markdown("#### 渲染底图与合成图框上传")
        st.caption("在调用大模型生成提示词与后续发送渲染管线前，请先设置好相应的图像素材。")

        col_img1, col_img2, col_img3 = st.columns(3)
        with col_img1:
            base_map_file = st.file_uploader(
                "1. AIGC 底图 / 线稿 (Base Map)",
                type=["png", "jpg", "jpeg"],
                key=f"{key_prefix}_base_map",
                help="用于图生图 (Img2Img) 或 ControlNet 线稿提取的基础图像。"
            )
        with col_img2:
            scope_mask_file = st.file_uploader(
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

        if st.button(
            "调用 DeepSeek 生成完整提示词",
            type="primary",
            key=f"{key_prefix}_gen",
            **stretch_width(st.button),
        ):
            with st.spinner("DeepSeek 推理生成中..."):
                result = generate_drawing_prompt_with_llm(selected_tmpl, model=model_tag)
            st.text_area("完整 Image 2.0 英文提示词 (可直接拷贝至 Midjourney/SD)", value=result, height=350, key=f"{key_prefix}_result")

            # ---- One-click render ----
            st.markdown("---")
            render_section_intro("一键出图", "自动生成提示词并调用 SD 渲染，全程无需手动干预。", eyebrow="One-Click")

            enable_quality = st.checkbox(
                "启用质量评估闭环（自动检测显存，下载 Gemma 模型）",
                key=f"{key_prefix}_quality",
            )

            if st.button("一键出图", type="primary", key=f"{key_prefix}_oneclick"):
                pipeline = DrawingPipeline()
                progress_bar = st.progress(0, text="准备中...")

                def update_progress(**kwargs):
                    step_idx = kwargs.get("step_index", 0)
                    total = kwargs.get("total_steps", 1)
                    progress_bar.progress(
                        (step_idx + 0.5) / total,
                        text=f"步骤 {step_idx + 1}/{total}...",
                    )

                with st.spinner("管线执行中..."):
                    if enable_quality:
                        result = pipeline.generate_with_quality_loop(selected_tmpl, on_progress=update_progress)
                    else:
                        result = pipeline.generate_single(selected_tmpl, mode="auto", on_progress=update_progress)

                progress_bar.progress(1.0, text="完成!")
                if result.success:
                    st.image(result.image, caption=f"{selected_tmpl} - 渲染完成")
                    st.session_state[f"{key_prefix}_sd_result"] = result.image
                else:
                    st.error(f"出图失败：{result.error}")

                if result.success and result.quality_report:
                    qr = result.quality_report
                    st.markdown("---")
                    st.markdown("**质量评估结果**")
                    col_q1, col_q2, col_q3 = st.columns(3)
                    col_q1.metric("综合评级", qr.rating)
                    col_q2.metric("视觉评分", f"{qr.visual_score}/10")
                    col_q3.metric("内容评分", f"{qr.content_score}/10")
                    if qr.issue_types:
                        st.warning(f"发现的问题：{', '.join(qr.issue_types)}")
                    if qr.suggestions:
                        st.info(f"修正建议：{', '.join(qr.suggestions)}")

            # ---- SD Render Section ----
            st.markdown("---")
            render_section_intro("SD 渲染生成", "将提示词直接发送至本地 Stable Diffusion WebUI 进行渲染。", eyebrow="SD Render")

            col_mode, col_cn = st.columns(2)
            with col_mode:
                render_mode = st.selectbox(
                    "渲染模式",
                    ["img2img + ControlNet", "txt2img (纯文生图)", "inpainting (局部重绘)"],
                    key=f"{key_prefix}_render_mode",
                )
            with col_cn:
                cn_module = st.selectbox(
                    "ControlNet 算子",
                    ["canny", "depth", "mlsd", "lineart", "none"],
                    key=f"{key_prefix}_cn_module",
                )

            denoising = st.slider("重绘强度 (Denoising)", 0.1, 1.0, 0.55, 0.05, key=f"{key_prefix}_denoising")

            if st.button("开始 SD 渲染", type="primary", key=f"{key_prefix}_sd_run"):
                from src.engines.stable_diffusion_engine import SDPipeline

                progress_bar = st.progress(0, text="准备渲染...")

                def update_progress(**kwargs):
                    step_idx = kwargs.get("step_index", 0)
                    total = kwargs.get("total_steps", 1)
                    progress_bar.progress(
                        (step_idx + 0.5) / total,
                        text=f"渲染步骤 {step_idx + 1}/{total}...",
                    )

                try:
                    pipe = SDPipeline()

                    if render_mode == "txt2img (纯文生图)":
                        pipe.txt2img(prompt=result, negative_prompt="", width=1024, height=768)
                    else:
                        if base_map_file is not None:
                            init_img = PILImage.open(base_map_file)
                        else:
                            init_img = PILImage.new("RGB", (512, 512), "#1e293b")

                        if render_mode == "inpainting (局部重绘)" and scope_mask_file is not None:
                            mask_img = PILImage.open(scope_mask_file).convert("L")
                            pipe.inpaint(init_img, mask_img, prompt=result, negative_prompt="", denoising=denoising)
                        else:
                            pipe.img2img(init_img, prompt=result, negative_prompt="", denoising=denoising)

                        if cn_module != "none":
                            pipe.add_controlnet(init_img, module=cn_module, model=cn_module)

                    with st.spinner("SD 渲染中，请耐心等待..."):
                        sd_result = pipe.run(on_progress=update_progress)

                    progress_bar.progress(1.0, text="渲染完成!")
                    if sd_result.images:
                        st.image(
                            sd_result.images[0],
                            caption=f"渲染结果 (seed: {sd_result.seed}, 耗时: {sd_result.elapsed_seconds}s)",
                        )
                        st.session_state[f"{key_prefix}_sd_result"] = sd_result.images[0]

                except Exception as e:
                    st.error(f"SD 渲染失败: {e}")

    else:
        st.info("暂无本阶段图纸模板。")

    # ---- Batch generation panel ----
    st.markdown("---")
    render_section_intro("批量出图", "一次性选择多张图纸进行批量生成。", eyebrow="Batch Mode")

    all_names = get_all_template_names()
    selected_templates = st.multiselect(
        "选择要生成的图纸",
        all_names,
        key=f"{key_prefix}_batch_select",
    )

    batch_mode = st.radio(
        "生成模式",
        ["全自动", "确认后渲染"],
        horizontal=True,
        key=f"{key_prefix}_batch_mode",
    )

    if selected_templates and st.button("批量生成", type="primary", key=f"{key_prefix}_batch_run"):
        pipeline = DrawingPipeline()
        overall_progress = st.progress(0, text=f"批量生成 0/{len(selected_templates)}")

        def batch_progress(**kwargs):
            current = kwargs.get("current", 0)
            total = kwargs.get("total", 1)
            name = kwargs.get("template_name", "")
            overall_progress.progress(current / total, text=f"批量生成 {current}/{total}: {name}")

        mode = "auto" if batch_mode == "全自动" else "confirm"
        results = pipeline.generate_batch(selected_templates, mode=mode, on_progress=batch_progress)

        overall_progress.progress(1.0, text="批量生成完成!")

        success_count = sum(1 for r in results if r.success)
        st.info(f"完成：{success_count}/{len(results)} 张成功")

        for r in results:
            with st.expander(f"{r.template_name} - {'成功' if r.success else '失败'}", expanded=not r.success):
                if r.success and r.image:
                    st.image(r.image, caption=r.template_name)
                elif r.success and r.prompt:
                    st.text_area("生成的提示词（确认后渲染）", value=r.prompt, height=200, key=f"{key_prefix}_batch_prompt_{r.template_name}")
                else:
                    st.error(r.error)
