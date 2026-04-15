import streamlit as st
import pandas as pd
import os
import numpy as np
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="数据管理中心", layout="wide", initial_sidebar_state="expanded")

import streamlit as st
from ui_components import render_top_nav # 引入外援

@st.cache_data
def load_data_file(file_path, modified_time):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path, encoding='utf-8')
    else:
        return pd.read_excel(file_path)

render_top_nav() # 一行代码搞定几十行的 CSS 和导航栏！

# 下面接着写你这一页的核心业务逻辑...
st.markdown("<h2>多源数据融合管理中心</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("#### 📂 数据类型")
    data_type = st.radio("选择数据类型:", [
        "🏪 POI 数据", "🚥 交通数据", "📍 精确点位", "📊 CV 分析结果", "💬 情感分析数据"
    ], label_visibility="collapsed")

st.markdown("### 📊 数据概览")

data_files = {
    "🏪 POI 数据": "data/Changchun_POI_Real.csv",
    "🚥 交通数据": "data/Changchun_Traffic_Real.csv",
    "📍 精确点位": "data/Changchun_Precise_Points.xlsx",
    "📊 CV 分析结果": "data/GVI_Results_Analysis.csv",
    "💬 情感分析数据": "data/CV_NLP_RawData.csv"
}

selected_file = data_files[data_type]

if os.path.exists(selected_file):
    try:
        mt = os.path.getmtime(selected_file)
        df = load_data_file(selected_file, mt)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📊 总记录数", f"{len(df):,}")
        col2.metric("📐 字段数量", f"{len(df.columns)}")
        col3.metric("💾 文件大小", f"{os.path.getsize(selected_file) / 1024:.1f} KB")
        col4.metric("✅ 数据状态", "正常")
        
        st.markdown("---")
        st.markdown("### 📋 数据预览")
        st.dataframe(df.head(10), use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📊 数据质量分析")
        missing_data = df.isnull().sum()
        missing_percent = (missing_data / len(df) * 100).round(2)
        quality_df = pd.DataFrame({
            '字段': missing_data.index,
            '缺失值': missing_data.values,
            '缺失率 (%)': missing_percent.values
        })
        st.dataframe(quality_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"❌ 数据读取失败：{e}")
else:
    st.warning(f"⚠️ 文件不存在：{selected_file}")

st.markdown("---")
st.markdown("### 📤 数据上传与更新")

upload_col1, upload_col2 = st.columns(2)
with upload_col1:
    st.markdown("#### 🆕 上传新数据")
    uploaded_file = st.file_uploader("选择文件上传", type=['csv', 'xlsx'], key="upload")
    if uploaded_file is not None:
        save_name = st.text_input("保存文件名:", value=uploaded_file.name)
        if st.button("💾 保存数据"):
            with open(save_name, 'wb') as f:
                f.write(uploaded_file.getvalue())
            st.success(f"✅ 数据已保存至 {save_name}")

with upload_col2:
    st.markdown("#### 🗑️ 数据管理")
    if st.button("🗑️ 删除选定数据文件"):
        if os.path.exists(selected_file):
            os.remove(selected_file)
            st.success(f"✅ 已删除 {selected_file}")
        else:
            st.warning("⚠️ 文件不存在")

st.markdown("---")
st.markdown("### 📈 数据可视化分析")

if os.path.exists(selected_file):
    try:
        mt = os.path.getmtime(selected_file)
        df = load_data_file(selected_file, mt)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) > 0:
            viz_type = st.selectbox("选择图表类型:", ["📊 柱状图", "📈 折线图", "🔵 散点图", "🥧 饼图"])
            
            x_col = st.selectbox("X 轴:", df.columns, key="x")
            y_col = st.selectbox("Y 轴:", numeric_cols, key="y")
            
            if viz_type == "📊 柱状图":
                fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            elif viz_type == "📈 折线图":
                fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            elif viz_type == "🔵 散点图":
                if len(numeric_cols) > 1:
                    color_col = st.selectbox("颜色:", numeric_cols, key="color")
                    fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=f"{y_col} vs {x_col}")
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
            elif viz_type == "🥧 饼图":
                fig = px.pie(df, names=x_col, values=y_col, title=f"{y_col} Distribution")
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ 可视化失败：{e}")

st.markdown("---")
st.markdown("### 🧬 数据血缘关系")

data_lineage = pd.DataFrame({
    "数据名称": ["POI 数据", "交通数据", "精确点位", "街景图片", "CV 分析结果", "情感分析数据"],
    "来源": ["OpenStreetMap", "百度地图 API", "实地勘测", "百度街景 API", "DeepLabV3+/Segformer", "微博/大众点评爬虫"],
    "用途": ["商业设施分析", "交通路网分析", "空间定位基准", "视觉感知数据", "绿视率等指标计算", "社会情感分析"],
    "更新频率": ["季度", "月度", "年度", "季度", "实时", "周度"]
})

st.dataframe(data_lineage, use_container_width=True, hide_index=True)
