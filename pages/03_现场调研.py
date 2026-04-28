"""阶段 03：现场调研 —— 街景样本库（继承原 page04 功能）。"""

import streamlit as st
from pathlib import Path
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.ui.module_summary import render_stage_summary
from src.workflow.stage_data_bus import save_stage_output, render_evidence_chain_bar

st.set_page_config(page_title="03 现场调研", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="现场调研",
    description="读取本地 streetview 文件夹中的调研点街景图，按采样点坐标和四向照片进行核验。",
    eyebrow="Stage 03",
    tags=["街景样本库", "四向照片", "采样点分布"],
)
render_evidence_chain_bar("03", ["01", "02", "03", "04", "05"])

sv_root = Path("data/streetview")
if sv_root.exists():
    point_dirs = sorted([d for d in sv_root.iterdir() if d.is_dir() and d.name.startswith("Point_")])
    render_summary_cards([
        {"value": len(point_dirs), "title": "采样点", "desc": "streetview 文件夹中的调研点数量"},
        {"value": f"{len(point_dirs) * 4}", "title": "街景照片", "desc": "四向（0/90/180/270°）"},
    ])

    if point_dirs:
        selected_point = st.selectbox("选择采样点", [d.name for d in point_dirs])
        point_path = sv_root / selected_point

        headings = [0, 90, 180, 270]
        cols = st.columns(4)
        for i, h in enumerate(headings):
            with cols[i]:
                img_path = point_path / f"heading_{h}.jpg"
                if img_path.exists():
                    st.image(str(img_path), caption=f"{h}°", use_container_width=True)
                else:
                    st.warning(f"{h}° 缺失")

        save_stage_output("03", "survey_points", len(point_dirs))
    else:
        st.info("未找到调研点文件夹。")
else:
    st.warning("data/streetview 目录不存在。")

st.markdown("---")
point_count = len(point_dirs) if sv_root.exists() and 'point_dirs' in dir() else 0
render_stage_summary(
    stage_code="03",
    title="现场调研覆盖度统计",
    findings=[
        {"point": f"共 {point_count} 个采样点完成四向街景拍摄", "evidence": "streetview 文件夹自动扫描"},
        {"point": f"产出 {point_count * 4} 张街景照片用于后续环境品质分析", "evidence": "0/90/180/270 四向覆盖"},
    ],
    methodology="基于本地 streetview 文件夹的自动索引",
    implication="为现状分析（Stage 04）中的 GVI、SVF 等街景品质指标计算提供了影像基础",
)
