from pathlib import Path
import re

import pandas as pd
import streamlit as st

from src.config import DATA_FILES, STREETVIEW_DIR
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav


st.set_page_config(page_title="现场调研 | 街景样本库", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

def _point_id(path: Path) -> int:
    match = re.search(r"(\d+)$", path.name)
    return int(match.group(1)) if match else 0


@st.cache_data(ttl=600)
def load_streetview_index():
    if not STREETVIEW_DIR.exists():
        return []
    records = []
    for point_dir in sorted((p for p in STREETVIEW_DIR.iterdir() if p.is_dir()), key=_point_id):
        images = sorted(point_dir.glob("heading_*.jpg"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)))
        if images:
            records.append({"point": point_dir.name, "point_id": _point_id(point_dir), "images": images})
    return records


@st.cache_data(ttl=600)
def load_point_table():
    if not DATA_FILES["points"].exists():
        return pd.DataFrame(columns=["ID", "Lng", "Lat"])
    return pd.read_excel(DATA_FILES["points"])


streetview_records = load_streetview_index()
point_table = load_point_table()
point_lookup = {
    int(row["ID"]): {"lng": row["Lng"], "lat": row["Lat"]}
    for _, row in point_table.iterrows()
    if "ID" in point_table.columns
}
image_count = sum(len(item["images"]) for item in streetview_records)

render_page_banner(
    title="现场调研街景样本库",
    description="直接读取 data/streetview 文件夹中的街景采样图片，按调研点和拍摄方向组织现场记录。",
    eyebrow="Stage 03",
    tags=["现场调研", "街景采样", "四向照片", "问题点位复核"],
    metrics=[
        {"value": len(streetview_records), "label": "调研点", "meta": "streetview 子文件夹"},
        {"value": image_count, "label": "街景图", "meta": "heading_*.jpg"},
        {"value": "4 向", "label": "采样方向", "meta": "0 / 90 / 180 / 270"},
        {"value": "本地", "label": "数据来源", "meta": "data/streetview"},
    ],
)

render_summary_cards(
    [
        {"value": "街景", "title": "界面记录", "desc": "用于核对建筑界面、道路断面和沿街经营状态。"},
        {"value": "点位", "title": "空间索引", "desc": "每个 Point 对应一组经纬度和四向照片。"},
        {"value": "问题", "title": "后续标注", "desc": "可继续扩展为消极空间、慢行断点和风貌冲突标注。"},
    ]
)

if not streetview_records:
    st.warning("未找到 data/streetview 下的街景图片。")
    st.stop()

render_section_intro("调研点查看", "选择一个 Point 后查看四个方向的现场街景图。", eyebrow="Streetview")

point_labels = [
    f"{item['point']}（{len(item['images'])} 张）"
    for item in streetview_records
]
selected_label = st.selectbox("调研点", point_labels, index=0)
selected_idx = point_labels.index(selected_label)
selected = streetview_records[selected_idx]
point_meta = point_lookup.get(selected["point_id"])

if point_meta:
    render_summary_cards(
        [
            {"value": selected["point"], "title": "点位编号", "desc": "来自 streetview 文件夹名。"},
            {"value": f"{point_meta['lng']:.6f}", "title": "经度", "desc": "来自 Changchun_Precise_Points.xlsx。"},
            {"value": f"{point_meta['lat']:.6f}", "title": "纬度", "desc": "来自 Changchun_Precise_Points.xlsx。"},
        ]
    )
else:
    st.caption(f"{selected['point']} 暂未在点位表中匹配到经纬度。")

cols = st.columns(2)
for idx, image_path in enumerate(selected["images"]):
    heading_match = re.search(r"heading_(\d+)", image_path.stem)
    heading = heading_match.group(1) if heading_match else image_path.stem
    with cols[idx % 2]:
        st.image(str(image_path), caption=f"{selected['point']} / heading {heading}", use_container_width=True)

with st.expander("街景文件索引", expanded=False):
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "调研点": item["point"],
                    "图片数": len(item["images"]),
                    "本地路径": str(item["images"][0].parent),
                }
                for item in streetview_records
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
