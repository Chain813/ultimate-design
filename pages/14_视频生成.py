"""阶段 14：视频生成 —— 基于 HyperFrames 的项目汇报视频生成。"""

import streamlit as st
import subprocess
from pathlib import Path
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.workflow.stage_data_bus import render_evidence_chain_bar

st.set_page_config(page_title="14 视频生成", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="视频生成",
    description="基于 HyperFrames 框架，一键生成项目答辩汇报视频（~9 分钟）。",
    eyebrow="Stage 14",
    tags=["HyperFrames", "视频渲染", "答辩汇报"],
)
render_evidence_chain_bar("14", ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13"])

SUB_OPTIONS = ["🎬 视频渲染", "📋 旁白脚本", "⚙️ 设置"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

COMPOSER_DIR = Path(__file__).resolve().parents[1] / "tools" / "video_generator" / "composer"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "tools" / "video_generator" / "output"


def get_ffmpeg_path():
    """获取 FFmpeg 路径"""
    import shutil
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    # 尝试常见安装路径
    possible = list(Path("C:/Users").rglob("ffmpeg.exe"))
    return str(possible[0]) if possible else None


def check_dependencies():
    """检查渲染依赖"""
    issues = []
    import shutil
    if not shutil.which("node"):
        issues.append("Node.js 未安装")
    if not get_ffmpeg_path():
        issues.append("FFmpeg 未安装")
    if not (COMPOSER_DIR / "node_modules").exists():
        issues.append("npm 依赖未安装（运行 cd tools/video_generator/composer && npm install）")
    if not (COMPOSER_DIR / "index.html").exists():
        issues.append("合成文件 index.html 不存在")
    return issues


if selected_sub == "🎬 视频渲染":
    render_section_intro("视频渲染", "选择渲染质量并生成 MP4 视频文件。", eyebrow="Render")

    # 依赖检查
    issues = check_dependencies()
    if issues:
        st.warning("依赖检查：\n" + "\n".join(f"- {i}" for i in issues))
    else:
        st.success("所有依赖已就绪")

    render_summary_cards([
        {"value": "14", "title": "视频段落", "desc": "开场 + 13 个阶段"},
        {"value": "~9 分钟", "title": "预计时长", "desc": "555 秒完整版"},
        {"value": "1920×1080", "title": "分辨率", "desc": "Full HD 输出"},
    ])

    col1, col2 = st.columns(2)
    with col1:
        quality = st.selectbox(
            "渲染质量",
            ["draft（快速预览，低分辨率）", "standard（标准质量）", "high（高质量，耗时较长）"],
            index=1,
            key="p14_quality",
        )
    with col2:
        quality_map = {
            "draft（快速预览，低分辨率）": "draft",
            "standard（标准质量）": "standard",
            "high（高质量，耗时较长）": "high",
        }
        selected_quality = quality_map[quality]

    st.markdown("---")

    col_render, col_preview = st.columns(2)

    with col_render:
        if st.button("🎬 开始渲染", type="primary", use_container_width=True):
            if issues:
                st.error("请先解决依赖问题")
            else:
                output_name = f"final_{selected_quality}.mp4"
                output_path = OUTPUT_DIR / output_name
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

                progress_bar = st.progress(0, text="准备渲染...")
                status_text = st.empty()

                cmd = ["npx", "hyperframes", "render", "--quality", selected_quality, "-o", f"../output/{output_name}"]

                try:
                    import time
                    start_time = time.time()

                    process = subprocess.Popen(
                        cmd,
                        cwd=str(COMPOSER_DIR),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                    )

                    for line in process.stdout:
                        line = line.strip()
                        if "Capturing frame" in line:
                            try:
                                parts = line.split("frame ")[1].split("/")
                                current = int(parts[0])
                                total = int(parts[1].split(" ")[0])
                                progress = current / total
                                progress_bar.progress(progress, text=f"渲染中... {current}/{total} 帧")
                            except (IndexError, ValueError):
                                pass
                        elif "%" in line:
                            status_text.text(line)

                    process.wait()
                    elapsed = time.time() - start_time

                    if process.returncode == 0:
                        progress_bar.progress(1.0, text="渲染完成!")
                        st.success(f"视频渲染成功！耗时 {elapsed:.0f} 秒")
                        st.info(f"输出文件：{output_path}")

                        if output_path.exists():
                            size_mb = output_path.stat().st_size / 1024 / 1024
                            st.metric("文件大小", f"{size_mb:.1f} MB")

                            with open(output_path, "rb") as f:
                                st.download_button(
                                    "📥 下载视频",
                                    f,
                                    file_name=output_name,
                                    mime="video/mp4",
                                    use_container_width=True,
                                )
                    else:
                        st.error(f"渲染失败（退出码 {process.returncode}）")

                except Exception as e:
                    st.error(f"渲染异常：{e}")

    with col_preview:
        if st.button("👁️ 浏览器预览", use_container_width=True):
            if issues:
                st.error("请先解决依赖问题")
            else:
                st.info("正在启动预览服务器，请在浏览器中查看...")
                try:
                    subprocess.Popen(
                        ["npx", "hyperframes", "preview"],
                        cwd=str(COMPOSER_DIR),
                    )
                    st.success("预览服务器已启动，请访问 http://localhost:3000")
                except Exception as e:
                    st.error(f"启动失败：{e}")

    # 显示已生成的视频
    st.markdown("---")
    st.markdown("### 📁 已生成的视频")
    if OUTPUT_DIR.exists():
        videos = sorted(OUTPUT_DIR.glob("*.mp4"))
        if videos:
            for v in videos:
                size_mb = v.stat().st_size / 1024 / 1024
                col_name, col_size, col_action = st.columns([3, 1, 1])
                with col_name:
                    st.text(v.name)
                with col_size:
                    st.text(f"{size_mb:.1f} MB")
                with col_action:
                    with open(v, "rb") as f:
                        st.download_button("下载", f, file_name=v.name, mime="video/mp4", key=f"dl_{v.name}")
        else:
            st.info("暂无已生成的视频。")
    else:
        st.info("输出目录不存在。")

elif selected_sub == "📋 旁白脚本":
    render_section_intro("旁白脚本", "视频各段落的旁白时间点标记，用于配音对齐。", eyebrow="Script")

    # 从 HTML 文件中提取段落信息
    sections = [
        {"time": "00:00", "name": "开场", "narration": "数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计"},
        {"time": "00:15", "name": "01 任务解读", "narration": "任务解读：梳理任务书红线限制，建立初始认知框架"},
        {"time": "00:45", "name": "02 资料收集", "narration": "资料收集：多源数据汇聚，建立数据中台"},
        {"time": "01:15", "name": "03 现场调研", "narration": "现场调研：实地踏勘，记录街道空间与环境问题"},
        {"time": "01:55", "name": "04 现状分析", "narration": "现状分析：3D全息数据底座，多层叠加展示空间现状"},
        {"time": "02:45", "name": "05 问题诊断", "narration": "问题诊断：MPI更新潜力排行与地块诊断雷达"},
        {"time": "03:35", "name": "06 目标定位", "narration": "目标定位：数字孪生·古今共振设计理念"},
        {"time": "04:10", "name": "07 设计策略", "narration": "设计策略：三主体博弈与多主体共识"},
        {"time": "05:00", "name": "08 总体城市设计", "narration": "总体城市设计：总平面图与空间结构推演"},
        {"time": "05:50", "name": "09 专项系统设计", "narration": "专项系统设计：道路交通、慢行系统、公共空间、绿地景观"},
        {"time": "06:35", "name": "10 重点地段深化", "narration": "重点地段深化：5个重点地块的AIGC效果图与Before/After对比"},
        {"time": "07:25", "name": "11 实施路径", "narration": "实施路径：近期微更新、中期功能置换、远期整体提升"},
        {"time": "07:55", "name": "12 城市设计导则", "narration": "城市设计导则：地块控制图则与街道断面设计"},
        {"time": "08:25", "name": "13 成果表达", "narration": "成果表达：核心指标汇总与3D全息方案回顾"},
    ]

    import pandas as pd
    df = pd.DataFrame(sections)
    st.dataframe(df, use_container_width=True, hide_index=True)

    script_text = "\n".join(f"[{s['time']}] {s['name']}: {s['narration']}" for s in sections)
    st.download_button(
        "📥 下载旁白脚本",
        script_text,
        file_name="旁白脚本.txt",
        mime="text/plain",
    )

elif selected_sub == "⚙️ 设置":
    render_section_intro("渲染设置", "配置 HyperFrames 渲染参数。", eyebrow="Settings")

    st.markdown("### 环境信息")
    import shutil
    col1, col2, col3 = st.columns(3)
    with col1:
        node_ver = shutil.which("node")
        st.metric("Node.js", "已安装" if node_ver else "未安装")
    with col2:
        ffmpeg_ver = get_ffmpeg_path()
        st.metric("FFmpeg", "已安装" if ffmpeg_ver else "未安装")
    with col3:
        chrome_path = Path.home() / ".cache" / "hyperframes" / "chrome"
        st.metric("Chrome", "已安装" if chrome_path.exists() else "未安装")

    st.markdown("### 合成文件")
    index_html = COMPOSER_DIR / "index.html"
    if index_html.exists():
        with st.expander("查看 index.html 内容"):
            st.code(index_html.read_text(encoding="utf-8")[:5000], language="html")
    else:
        st.warning("index.html 不存在")

    st.markdown("### 数据文件")
    data_dir = COMPOSER_DIR / "data"
    if data_dir.exists():
        json_files = list(data_dir.rglob("*.json"))
        st.text(f"数据文件数：{len(json_files)}")
        for f in json_files:
            st.text(f"  {f.relative_to(data_dir)}")
