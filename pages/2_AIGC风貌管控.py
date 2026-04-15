import streamlit as st
import time
import os
from PIL import Image
from io import BytesIO
from core_engine import run_realtime_sd
from ui_components import render_top_nav

st.set_page_config(page_title="风貌管控 | 微更新平台", layout="wide", initial_sidebar_state="expanded")

render_top_nav()

st.markdown("<h2>基于 Stable Diffusion + ControlNet 的街区风貌修缮推演</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ 专家级渲染参数")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem;'>Advanced AIGC Parameters</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("#### 🛠️ ControlNet 骨架引擎")
    cn_mode = st.selectbox(
        "空间约束算子 (Preprocessor)",
        [
            "Canny (精细边缘特征提取)",
            "MLSD (建筑直线/透视提取)",
            "Depth (深度空间透视估计)",
            "Seg (城市语义分割掩码)"
        ]
    )
    cn_weight = st.slider("结构控制权重 (Control Weight)", 0.0, 2.0, 1.0, 0.1)

    st.markdown("---")
    st.markdown("#### 🧠 潜空间采样器矩阵")
    sampler = st.selectbox(
        "采样算法 (Sampler)",
        ["DPM++ 2M Karras (推荐)", "Euler a", "DDIM", "Heun"]
    )
    steps = st.slider("迭代步数 (Sampling Steps)", 10, 80, 20, 5)
    cfg = st.slider("提示词相关性 (CFG Scale)", 1.0, 15.0, 7.0, 0.5)

work_col, result_col = st.columns([1, 1.3])

with work_col:
    st.markdown("#### 📥 现状数据输入")
    uploaded_file = st.file_uploader("上传长春历史街区现状照片 (支持 JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.session_state['aigc_img_bytes'] = uploaded_file.getvalue()

    st.markdown("---")
    st.markdown("#### ⚙️ 核心控制算子 (ControlNet Engine)")

    style_mode = st.selectbox(
        "选择目标微更新风格：",
        ["工业遗迹复兴 (Industrial Loft)", "历史风貌修缮 (Heritage Repair)", "现代极简介入 (Minimalist Intervention)", "古今共振：新旧材质织补介入", "社区微更新：口袋公园激活", "站城融合：商业化缝合"]
    )

    prompt = st.text_area("增量提示词 (Prompt Enhancement):",
                          value="architectural photography, resonance of past and present, historic brick building integrated with modern sleek glass extension, architectural contrast, harmonious urban design, dramatic lighting, high quality, 8k resolution",
                          height=100)
                          
    neg_prompt = st.text_area("反向提示词 (Negative Prompt):",
                          value="ugly, blurry, low resolution, deformed, messy wires, bad architecture, chaotic traffic, distorted people",
                          height=70)

    col_a, col_b = st.columns(2)
    with col_a:
        strength = st.slider("重绘幅度 (Denoising)", 0.1, 1.0, 0.55, 0.05)
    with col_b:
        seed = st.number_input("随机种子 (Seed)", value=428931, step=1)

    generate_btn = st.button("🚀 启动大模型联觉生成 (Render)", use_container_width=True, type="primary")

with result_col:
    st.markdown("#### 👁️ 微更新前后风貌对比")

    if 'aigc_img_bytes' not in st.session_state:
        st.info("💡 请在左侧上传一张待改造的街景实测图，并设定风格算子。")
        st.markdown("""
        <div style='text-align: center; padding: 50px; background: #f8f9fa; border-radius: 10px; border: 2px dashed #bdc3c7;'>
            <h3 style='color: #7f8c8d;'>等待视觉信号接入...</h3>
        </div>
        """, unsafe_allow_html=True)
    else:
        original_img = Image.open(BytesIO(st.session_state['aigc_img_bytes']))
        
        with st.expander("✂️ 第一步：图像几何校正与裁剪 (实时预览)", expanded=True):
            pc1, pc2 = st.columns([1, 2])
            with pc1:
                angle = st.slider("🔄 旋转角度", -180, 180, 0, key="rotate_slider")
                st.markdown("---")
                t_c = st.slider("⬆️ 顶切", 0, 50, 0, key="tc")
                b_c = st.slider("⬇️ 底切", 0, 50, 0, key="bc")
                l_c = st.slider("⬅️ 左切", 0, 50, 0, key="lc")
                r_c = st.slider("➡️ 右切", 0, 50, 0, key="rc")
            with pc2:
                work_img = original_img.copy()
                if angle != 0:
                    work_img = work_img.rotate(angle, expand=True, fillcolor=(255, 255, 255))
                w_w, w_h = work_img.size
                left, top = int(w_w * l_c / 100), int(w_h * t_c / 100)
                right, bottom = w_w - int(w_w * r_c / 100), w_h - int(w_h * b_c / 100)
                if left < right and top < bottom:
                    work_img = work_img.crop((left, top, right, bottom))
                st.image(work_img, caption="📏 待渲染底图预览", use_container_width=True)

        if not generate_btn:
            pass
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()

            for p in range(0, 81, 20):
                progress_bar.progress(p)
                status_text.text(f"正在调动本地 GPU 计算资源与模型权重... {p}%")
                time.sleep(0.1)

            res_img = run_realtime_sd(work_img, prompt, neg_prompt, steps, cfg, strength)

            if res_img:
                progress_bar.progress(100)
                status_text.success("✅ 渲染成功！空间特征匹配完毕。")
                comp_col1, comp_col2 = st.columns(2)
                with comp_col1:
                    st.image(work_img, caption="Before: 现状实景 (已裁剪)", use_container_width=True)
                with comp_col2:
                    st.image(res_img, caption=f"After: {style_mode} AIGC 成果图", use_container_width=True)
                    
                    buf = BytesIO()
                    res_img.save(buf, format="JPEG")
                    st.download_button("📥 下载渲染成果", buf.getvalue(), "result.jpg", "image/jpeg", use_container_width=True)
            else:
                st.error("❌ 渲染失败，请检查您的 SD API 服务是否开启。")