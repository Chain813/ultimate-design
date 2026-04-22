import streamlit as st
import streamlit.components.v1 as components
import time
import os
import base64
from PIL import Image
from io import BytesIO
from src.engines.core_engine import run_realtime_sd, is_demo_mode, get_plot_diagnostics
from src.ui.ui_components import render_top_nav, render_engine_status_alert

st.set_page_config(page_title="风貌管控 | 微更新平台", layout="wide", initial_sidebar_state="expanded")

render_top_nav()
render_engine_status_alert()

# 🚀 算力管家：自动检测并提供一键启动 SD/Ollama
from src.utils.daemon_manager import render_daemon_control_panel
render_daemon_control_panel()

st.markdown("<h2>基于先验路网约束的街区风貌推演系统</h2>", unsafe_allow_html=True)

# ==========================================
# 📍 地块导向推演模式 (Phase 3 新增)
# ==========================================
if 'aigc_history' not in st.session_state:
    st.session_state['aigc_history'] = []

plot_col, mode_col = st.columns([1, 1])
with plot_col:
    diagnostics = get_plot_diagnostics()
    if diagnostics:
        plot_names = ["🔧 自由模式 (手动选择)"] + [f"📍 {d['name']} (MPI:{d['mpi_score']})" for d in diagnostics]
        plot_sel = st.selectbox("🎯 地块导向推演", plot_names, key="aigc_plot_sel")
    else:
        plot_sel = "🔧 自由模式 (手动选择)"
        st.caption("未检测到地块数据，使用自由模式")

with mode_col:
    if plot_sel != "🔧 自由模式 (手动选择)" and diagnostics:
        sel_name = plot_sel.split(" (MPI:")[0].replace("📍 ", "")
        sel_diag = next((d for d in diagnostics if d['name'] == sel_name), None)
        if sel_diag:
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("面积", f"{sel_diag['area_ha']}ha")
            mc2.metric("MPI", f"{sel_diag['mpi_score']}")
            mc3.metric("POI", f"{sel_diag['poi_count']}")
            mc4.metric("GVI", f"{sel_diag['gvi_mean']}")

            # 自动匹配策略方向
            if sel_diag['gvi_mean'] > 0 and sel_diag['gvi_mean'] < 15:
                st.info(f"💡 {sel_name} 绿视率偏低 ({sel_diag['gvi_mean']}%)，推荐 **方向四：生活圈品质与环境**")
            elif sel_diag['poi_count'] > 5:
                st.info(f"💡 {sel_name} POI密度高 ({sel_diag['poi_count']})，推荐 **方向三：新旧共生与空间衔接**")
            elif sel_diag['mpi_score'] > 70:
                st.info(f"💡 {sel_name} 更新潜力高 ({sel_diag['mpi_score']})，推荐 **方向二：工业遗产活化与再生**")
            else:
                st.info(f"💡 {sel_name} 建议采用 **方向一：历史风貌保护与修复**")

st.markdown("---")

# ==========================================
# 📍 AIGC 制图视阈切换 (Phase 5 新增)
# ==========================================
aigc_mode = st.radio("⬇️ 选择空间生形模式", 
    ["🏙️ 街区全景透视推演 (现状修缮)", "🗺️ 概念总平面图生形 (辅助设计)", "🦅 轴测鸟瞰空间体块模拟 (辅助设计)"],
    horizontal=True, key="p3_aigc_mode")

st.markdown("---")

with st.sidebar:
    st.markdown("### ⚙️ 空间测算与约束参数")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem;'>Spatial Constraint Settings</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("#### 🛠️ 空间格局约束骨架")
    cn_mode = st.selectbox(
        "空间约束算子 (Preprocessor)",
        [
            "Canny (精细边缘特征提取)",
            "MLSD (建筑直线/透视提取)",
            "Depth (深度空间透视估计)",
            "Seg (城市语义分割掩码)"
        ]
    )
    cn_weight = st.slider("结构网格贴合度 (Constraint Weight)", 0.0, 2.0, 1.0, 0.1, help="ControlNet 对原始路网/建筑轮廓的约束强度。数值越高，AI 生成的方案越严格遵循原有的空间肌理和路网走向。建议历史保护区设为 1.2-1.5。")

    st.markdown("---")
    st.markdown("#### 🧠 衍生算法核心矩阵")
    sampler = st.selectbox(
        "采样算法 (Sampler)",
        ["DPM++ 2M Karras (推荐)", "Euler a", "DDIM", "Heun"]
    )
    steps = st.slider("迭代步数 (Sampling Steps)", 10, 80, 20, 5, help="扩散模型的去噪迭代次数。步数越多图像越精细，但耗时也越长。20 步适合快速草案预览，40+ 步适合最终出图。")
    cfg = st.slider("提示词相关性 (CFG Scale)", 1.0, 15.0, 7.0, 0.5, help="引导权重：控制生成结果对文本描述（规划意向词）的依从程度。7.0 为平衡值，>10 时构图会极度贴合描述但可能出现色彩失真。")

work_col, result_col = st.columns([1, 1.5]) # 略微增加结果区权重，确保 4:3 比例展示舒适

with work_col:
    st.markdown("#### 📥 现状数据输入")
    
    if aigc_mode == "🏙️ 街区全景透视推演 (现状修缮)":
        st.info("💡 请上传现状街道实拍图以供 Canny/Seg 算子提取风貌底线结构。")
        upload_label = "上传长春历史街区现状场景图 (JPG/PNG)"
        default_cn = "Canny (精细边缘特征提取)"
    elif aigc_mode == "🗺️ 概念总平面图生形 (辅助设计)":
        st.info("💡 请上传 GIS/AutoCAD 导出的【路网与地块结构线图截图(黑白配色佳)】，通过 Seg 算子推演建筑体块肌理分布。")
        upload_label = "上传地块路网基底图/二调影像图 (JPG/PNG)"
        default_cn = "Seg (城市语义分割掩码)"
    else:
        st.info("💡 请上传【谷歌/百度无纹理的高清卫星大图】，系统将自动套用 Depth 深度透视算子生成立体的概念白模/鸟瞰草图。")
        upload_label = "上传区域 2D 航拍图/卫星框选图 (JPG/PNG)"
        default_cn = "Depth (深度空间透视估计)"
        
    uploaded_file = st.file_uploader(upload_label, type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        # 如果是新上传的文件，则重置结果缓存
        if 'last_uploaded_file_bytes' not in st.session_state or st.session_state['last_uploaded_file_bytes'] != file_bytes:
            st.session_state['aigc_img_bytes'] = file_bytes
            st.session_state['last_uploaded_file_bytes'] = file_bytes
            if 'aigc_result_img' in st.session_state:
                del st.session_state['aigc_result_img']
            st.rerun()

    st.markdown("---")
    st.markdown("#### ⚙️ 规划算子 (Planning Operators)")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        green_weight = st.slider("🌿 景观介入度 (Greening)", 0.0, 2.0, 1.0, 0.1, help="控制 AI 在生成方案中植入绿色景观元素的强度。参照《城市绿地规划标准》(GB/T51346-2019)，绿地率不宜低于 30%。")
        heritage_weight = st.slider("🏛️ 历史锚定力 (Heritage)", 0.0, 2.0, 1.0, 0.1, help="历史风貌保护权重。数值越高，生成方案对原有建筑轮廓、红砖灰瓦等历史要素的保留程度越强。伪满皇宫周边建议 ≥1.3。")
    with col_p2:
        modern_weight = st.slider("✨ 现代介入感 (Modernity)", 0.0, 2.0, 1.0, 0.1)
        cinematic_weight = st.slider("🎬 表现力负载 (Cinematic)", 0.0, 2.0, 1.0, 0.1)

    # 📑 学术级二阶段策略库 (具象化精修版)
    academic_strategies = {
        "📂 方向一：历史风貌保护与修复": {
            "伪满时期建筑原真性修复": "authentic Manchu-style architecture facades, weathered red bricks and grey stone, historical window frames, classical cornice details, traditional Changchun masonry",
            "旧城历史肌理精准织补": "restoration of intricate urban fabric, small-scale brick infill, traditional narrow alleys, connecting old walls with new mortar, preserving 150-hectare historic grid"
        },
        "📂 方向二：工业遗产活化与再生": {
            "铁北工业厂房艺术化改造": "Tiebei red-brick factory renovation, saw-tooth roofs, massive steel trusses, huge glass windows, art gallery in warehouse, industrial loft aesthetic",
            "工业记忆景观叙事重构": "rusty mechanical parts as landmarks, old steam pipes, weathered metal sculptures, industrial park landscape, memory of Tiebei labor"
        },
        "📂 方向三：新旧共生与空间衔接": {
            "新旧材质对比与织补介入": "material contrast, sleek modern glass pavilion touching old rough brick wall, mirror reflections on heritage, architectural surgery",
            "小微空间功能复合微介入": "active ground floor cafes in old blocks, small community bookstores, multi-functional wooden decks, hybrid social spaces"
        },
        "📂 方向四：生活圈品质与环境": {
            "15分钟邻里生活圈激活": "vibrant street life, elders playing chess on public tables, children playing, diverse seating, neighborhood center vitality",
            "街道全要素慢行系统更新": "safe pedestrian crosswalks, tactile paving, cozy wooden benches, smart street lamps, low-speed traffic signs, bicycles"
        },
        "📂 方向五：智慧图景与科技介入": {
            "人文活力流转的日常场景": "human-centric urban space, clusters of local residents interacting, participatory furniture, temporary market stalls, inclusive community hub",
            "数字化激活的科技增强图景": "glowing digital data nodes on old facades, augmented reality projections, holographic city information, sleek futuristic smart furniture, high-tech urban layer"
        }
    }

    # 第一步：选择更新方向
    direction_mode = st.selectbox("第一步：选择更新方向", list(academic_strategies.keys()))
    
    # 第二步：确定设计方案
    strategy_options = list(academic_strategies[direction_mode].keys())
    style_mode = st.selectbox("第二步：确定设计方案", strategy_options)
    
    # 获取底层原始咒语
    base_p = academic_strategies[direction_mode][style_mode]
    dynamic_parts = []
    
    # 🌿 景观介入度 (全时段生效) - 增强关键词表现力
    dynamic_parts.append(f"(lush green vegetation, garden plants, trees, vertical greening:{green_weight})")
    # 🏛️ 历史锚定力 (全时段生效)
    dynamic_parts.append(f"(preservation of historical industrial texture, ancient bricks:{heritage_weight})")
    # ✨ 现代介入感 (全时段生效)
    dynamic_parts.append(f"(sleek minimalist glass extension, futuristic materials, modern architectural fusion:{modern_weight})")
    
    final_prompt = f"{base_p}, {', '.join(dynamic_parts)}, architectural photography, extremely high quality, 8k, professional lighting"
    if cinematic_weight > 1.0: 
        final_prompt += f", (dramatic cinematic lighting, volumetric light, unreal engine 5 render:{cinematic_weight})"

    # 智能联动引擎 (Intelligent Sync Engine)
    if 'last_auto_prompt' not in st.session_state:
        st.session_state['last_auto_prompt'] = final_prompt
    if 'manual_prompt' not in st.session_state:
        st.session_state['manual_prompt'] = final_prompt

    # 关键逻辑：如果当前框内内容与上一次自动生成的一致，说明用户未手动修改，则跟随滑块更新
    if st.session_state['manual_prompt'] == st.session_state['last_auto_prompt']:
        st.session_state['manual_prompt'] = final_prompt
        st.session_state['last_auto_prompt'] = final_prompt
    
    # 如果切换了模板，强制同步
    if 'last_style_mode' not in st.session_state:
        st.session_state['last_style_mode'] = style_mode
    if st.session_state['last_style_mode'] != style_mode:
        st.session_state['manual_prompt'] = final_prompt
        st.session_state['last_auto_prompt'] = final_prompt
        st.session_state['last_style_mode'] = style_mode

    prompt = st.text_area("实时生成咒语 (Live Prompt):", value=st.session_state['manual_prompt'], height=130, key="prompt_input")
    st.session_state['manual_prompt'] = prompt # 实时回存
                          
    neg_prompt = st.text_area("反向提示词 (Negative Prompt):",
                          value="ugly, blurry, low resolution, deformed, messy wires, bad architecture, chaotic traffic, distorted people",
                          height=70)

    if 'current_seed' not in st.session_state:
        st.session_state['current_seed'] = 428931

    col_a, col_b = st.columns(2)
    with col_a:
        strength = st.slider("重绘幅度 (Denoising)", 0.1, 1.0, 0.55, 0.05, help="💡 指示 AI 对原图的修改力度。若需观察滑块带来的显著变化，建议调至 0.6 以上。")
    with col_b:
        bc1, bc2 = st.columns([2, 1])
        with bc1:
            seed = st.number_input("随机种子 (Seed)", value=st.session_state['current_seed'], step=1)
        with bc2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎲", help="随机生成一个新的种子"):
                import random
                st.session_state['current_seed'] = random.randint(1, 999999999)
                st.rerun()

    generate_btn = st.button("🚀 启动视觉图景衍生测算 (Render)", use_container_width=True, type="primary")

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

            # 映射 ControlNet Preprocessor
            cn_map = {
                "Canny (精细边缘特征提取)": "canny",
                "MLSD (建筑直线/透视提取)": "mlsd",
                "Depth (深度空间透视估计)": "depth",
                "Seg (城市语义分割掩码)": "seg"
            }
            
            cn_model_map = {
                "Canny (精细边缘特征提取)": "control_v11p_sd15_canny",
                "MLSD (建筑直线/透视提取)": "control_v11p_sd15_mlsd",
                "Depth (深度空间透视估计)": "control_v11f1p_sd15_depth",
                "Seg (城市语义分割掩码)": "control_v11p_sd15_seg"
            }

            with st.spinner("⏳ 量子计算集群正高速重构空间特征图谱 ..."):
                res_img = run_realtime_sd(
                    work_img, prompt, neg_prompt, steps, cfg, strength,
                    cn_module=cn_map.get(cn_mode, "none"),
                    cn_model=cn_model_map.get(cn_mode, "none"),
                    cn_weight=cn_weight,
                    sampler_name=sampler.split(" (")[0],
                    seed=seed
                )

            if res_img:
                st.session_state['aigc_result_img'] = res_img # 持久化结果
                progress_bar.progress(100)
                status_text.success("✅ 渲染成功！引擎算力已全部释放。")
                st.toast("✅ 街区风貌更新图层已生成！", icon="🎨")

    # 👁️ 结果展示逻辑 (持久化) — Image Compare Slider
    active_img = st.session_state.get('aigc_result_img')
    if active_img and 'aigc_img_bytes' in st.session_state:
        before_img = Image.open(BytesIO(st.session_state['aigc_img_bytes']))

        def _img_to_b64(img):
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return base64.b64encode(buf.getvalue()).decode()

        b64_before = _img_to_b64(before_img)
        b64_after = _img_to_b64(active_img)

        slider_html = f"""
        <style>
            .img-comp-container {{
                position: relative; width: 100%; overflow: hidden;
                border-radius: 12px; border: 1px solid rgba(99,102,241,0.3);
            }}
            .img-comp-container img {{ display: block; width: 100%; }}
            .img-comp-overlay {{
                position: absolute; top: 0; left: 0; width: 50%; height: 100%; overflow: hidden;
            }}
            .img-comp-overlay img {{ position: absolute; top: 0; left: 0; width: 200%; max-width: none; }}
            .img-comp-slider {{
                position: absolute; top: 0; width: 3px; height: 100%;
                background: #818cf8; left: 50%; cursor: ew-resize; z-index: 10;
                box-shadow: 0 0 10px rgba(129,140,248,0.8);
            }}
            .img-comp-slider::after {{
                content: '\\2039\\203A'; position: absolute; top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                background: #818cf8; color: white; border-radius: 50%;
                width: 36px; height: 36px; display: flex; align-items: center;
                justify-content: center; font-size: 18px; font-weight: bold;
                box-shadow: 0 0 15px rgba(129,140,248,0.6);
            }}
            .label-tag {{
                position: absolute; bottom: 12px; padding: 4px 10px;
                background: rgba(0,0,0,0.6); color: #f8fafc; border-radius: 6px;
                font-size: 10px; font-weight: 600; z-index: 5;
            }}
            .label-before {{ left: 12px; }}
            .label-after {{ right: 12px; }}
        </style>
        <div class="img-comp-container" id="imgComp">
            <img src="data:image/jpeg;base64,{b64_after}" style="width:100%;">
            <div class="img-comp-overlay" id="overlay">
                <img src="data:image/jpeg;base64,{b64_before}">
            </div>
            <div class="img-comp-slider" id="slider"></div>
            <div class="label-tag label-before">Before 现状</div>
            <div class="label-tag label-after">After AIGC</div>
        </div>
        <script>
        (function() {{
            const container = document.getElementById('imgComp');
            const overlay = document.getElementById('overlay');
            const slider = document.getElementById('slider');
            let isDragging = false;
            function updatePos(x) {{
                const rect = container.getBoundingClientRect();
                let pos = Math.max(0.05, Math.min(0.95, (x - rect.left) / rect.width));
                overlay.style.width = (pos * 100) + '%';
                slider.style.left = (pos * 100) + '%';
            }}
            slider.addEventListener('mousedown', () => isDragging = true);
            document.addEventListener('mouseup', () => isDragging = false);
            document.addEventListener('mousemove', (e) => {{ if (isDragging) updatePos(e.clientX); }});
            slider.addEventListener('touchstart', () => isDragging = true);
            document.addEventListener('touchend', () => isDragging = false);
            document.addEventListener('touchmove', (e) => {{ if (isDragging) updatePos(e.touches[0].clientX); }});
        }})();
        </script>
        """
        components.html(slider_html, height=500, scrolling=False)

        buf = BytesIO()
        active_img.save(buf, format="JPEG")
        st.download_button("📥 下载渲染成果", buf.getvalue(), "result.jpg", "image/jpeg", use_container_width=True)

        # 保存到推演历史 (Phase 3 新增)
        if generate_btn and active_img:
            hist_entry = {
                "plot": plot_sel if plot_sel != "🔧 自由模式 (手动选择)" else "自由模式",
                "strategy": style_mode,
                "direction": direction_mode,
                "prompt_excerpt": prompt[:80] + "...",
                "strength": strength,
            }
            # 保存缩略图
            thumb = active_img.copy()
            thumb.thumbnail((300, 300))
            thumb_buf = BytesIO()
            thumb.save(thumb_buf, format="JPEG", quality=70)
            hist_entry["thumb_b64"] = base64.b64encode(thumb_buf.getvalue()).decode()
            st.session_state['aigc_history'].append(hist_entry)
    else:
        if generate_btn:
            if is_demo_mode():
                st.info("🎭 演示模式：显示预置占位图。请替换 assets/demo_aigc_result.png 为真实渲染成果。")
            else:
                st.error("❌ 渲染失败，请检查您的 SD API 服务是否开启。")

# ==========================================
# 🖼️ 推演历史对比画廊 (Phase 3 新增)
# ==========================================
if st.session_state.get('aigc_history'):
    st.markdown("---")
    st.markdown("### 🖼️ 推演历史对比画廊")
    st.caption(f"共 {len(st.session_state['aigc_history'])} 次推演记录 (本次会话)")

    gallery_cols = st.columns(min(len(st.session_state['aigc_history']), 4))
    for i, entry in enumerate(st.session_state['aigc_history'][-8:]):  # 最多展示最近 8 条
        with gallery_cols[i % len(gallery_cols)]:
            st.markdown(f"""
            <div style="background:rgba(99,102,241,0.06); border:1px solid rgba(99,102,241,0.15);
                        border-radius:10px; padding:10px; margin-bottom:8px; text-align:center;">
                <img src="data:image/jpeg;base64,{entry['thumb_b64']}" style="width:100%; border-radius:8px; margin-bottom:6px;">
                <p style="color:#a5b4fc; font-size:12px; font-weight:700; margin:0;">{entry['strategy']}</p>
                <p style="color:#64748b; font-size:11px; margin:2px 0;">{entry['plot']} | 重绘: {entry['strength']}</p>
            </div>
            """, unsafe_allow_html=True)

    latest_strategy = st.session_state['aigc_history'][-1]['strategy']
    hist_count = len(st.session_state['aigc_history'])
    st.markdown(f"""
    <div class="academic-conclusion-box" style="margin-top:20px; margin-bottom:15px;">
        <div class="academic-conclusion-title">🎯 视觉推演归敛结论</div>
        <div class="academic-conclusion-text">
            当前诊断单元已累计完成 {hist_count} 组空间形态衍生的参数化比选。最新推演采用的【{latest_strategy}】范式，在保护历史原生肌理结构与现代业态功能植入之间展现出较高的参数适配性。本图景可作为下一阶段建筑扩初设计的意向边界参考。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ 清空推演历史", key="clear_history"):
        st.session_state['aigc_history'] = []
        st.rerun()