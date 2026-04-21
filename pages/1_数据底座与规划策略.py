import streamlit as st
import pandas as pd
import json
import os
import numpy as np
import plotly.express as px
from markitdown import MarkItDown
from src.ui.ui_components import render_top_nav
from src.config import DATA_FILES, SHP_FILES

# ==========================================
# 💎 页面配置
# ==========================================
st.set_page_config(page_title="数据底座与策略实验室 | 01", layout="wide", initial_sidebar_state="expanded")
render_top_nav()

# ==========================================
# 🌌 逻辑切换架构 (已对齐全局胶囊样式)
# ==========================================
if 'lab01_active_sub' not in st.session_state:
    st.session_state.lab01_active_sub = "📊 资产综合评估"

selected_sub = st.radio(
    "功能选择",
    ["📊 资产综合评估", "📑 策略语义萃取", "⚙️ 物理底座管理"],
    index=["📊 资产综合评估", "📑 策略语义萃取", "⚙️ 物理底座管理"].index(st.session_state.lab01_active_sub),
    horizontal=True,
    key="lab01_switcher"
)
st.session_state.lab01_active_sub = selected_sub
st.markdown("---")

# ==========================================
# 🌌 模块 A: 资产综合评估 (专家决策模拟版)
# ==========================================
if selected_sub == "📊 资产综合评估":
    # 🧪 --- 核心 AHP 动态权重数据库 (从底层 GeoJSON 资产同步) ---
    json_path = SHP_FILES["plots"]
    if json_path.exists():
        try:
            with json_path.open("r", encoding="utf-8") as f:
                geo_data = json.load(f)
            plot_list = []
            for feat in geo_data.get("features", []):
                props = feat.get("properties", {})
                name = props.get("name", props.get("Name", f"地块_{props.get('OBJECTID', '??')}"))
                area = props.get("Shape_Area", 50000)
                # 核心修正：确保即使面积较小的地块也有基础可见分 (base score 0.5)
                # 这样在默认权重下，所有地块都会倾向于出现在排行榜中
                pot = min(0.95, 0.5 + (area / 150000) * 0.4)
                # 其余维度使用伪随机种子生成稳定的模拟值
                seed_id = props.get("OBJECTID", 0)
                np.random.seed(seed_id)
                plot_list.append({
                    "地块名称": name,
                    "空间潜力原分": round(pot, 2),
                    "社会需求原分": round(0.5 + 0.4 * np.random.rand(), 2),
                    "环境现状评分": round(0.1 + 0.6 * np.random.rand(), 2)
                })
            base_data = pd.DataFrame(plot_list)
        except Exception:
            base_data = pd.DataFrame({
                "地块名称": ["中车老厂区", "光复路历史街区", "铁北断头路节点"],
                "空间潜力原分": [0.89, 0.82, 0.74],
                "社会需求原分": [0.92, 0.95, 0.65],
                "环境现状评分": [0.35, 0.42, 0.28]
            })
    else:
        base_data = pd.DataFrame({
            "地块名称": ["数据资产缺失", "请检查 data/shp", "配置文件引用无误"],
            "空间潜力原分": [0, 0, 0], "社会需求原分": [0, 0, 0], "环境现状评分": [1, 1, 1]
        })

    with st.sidebar:
        st.markdown("### 🎚️ 专家决策模拟 (AHP)")
        st.info("💡 调节以下权重，系统将实时重排更新优先级。")
        w_poi = st.slider("🏗️ 空间潜力占比 (%)", 0, 100, 40, key="w_poi")
        w_soc = st.slider("👥 社会需求占比 (%)", 0, 100, 30, key="w_soc")
        w_env = st.slider("🌿 环境干预紧迫度 (%)", 0, 100, 30, key="w_env")
        
        # 归一化校验
        total_w = w_poi + w_soc + w_env
        st.caption(f"当前权重总计: {total_w}%")
        if total_w != 100:
            st.warning("⚠️ 建议调节权重总计为 100% 以获得准确评估。")
        
        st.markdown("---")
        st.markdown("#### 🎯 潜力筛选阈值")
        threshold = st.slider("仅展示得分高于:", 0, 100, 0, key="p1_threshold")
        
        st.markdown("---")
        st.markdown("#### 📂 成果报告输出")
        # 实时计算 MPI 函数
        def recalc_mpi(df, w1, w2, w3):
            # 将环境现状分反转为“紧迫度” (1-score)
            df['MPI 得分'] = (df['空间潜力原分'] * w1 + df['社会需求原分'] * w2 + (1 - df['环境现状评分']) * w3) / (w1 + w2 + w3 + 0.001) * 100
            return df

        df_calculated = recalc_mpi(base_data.copy(), w_poi, w_soc, w_env)
        df_filtered = df_calculated[df_calculated['MPI 得分'] >= threshold].sort_values("MPI 得分", ascending=False)
        
        csv_report = df_filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📤 导出评估排行榜 (CSV)",
            data=csv_report,
            file_name='Urban_Renewal_MPI_Report.csv',
            mime='text/csv',
            use_container_width=True
        )

    # --- MPI 计算公式与 AHP 权重矩阵 (常驻显示 + 融合面板) ---
    st.markdown("""
    <style>
    .mpi-card {
        background: rgba(99, 102, 241, 0.06);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .mpi-header {
        color: #a5b4fc;
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .mpi-desc-inline {
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 15px;
        border-top: 1px solid rgba(148, 163, 184, 0.1);
        padding-top: 12px;
        line-height: 1.6;
    }
    </style>
    <div class="mpi-card">
        <div class="mpi-header">🧪 多维更新潜力指数 (MPI) 测度模型</div>
    """, unsafe_allow_html=True)
    
    st.latex(r"\color{#a5b4fc} MPI_i = \frac{w_{space} \cdot S_i + w_{social} \cdot D_i + w_{env} \cdot (1 - E_i)}{w_{space} + w_{social} + w_{env}} \times 100")
    
    st.markdown("""
        <div class="mpi-desc-inline">
            <b>指标项:</b> $S_i$ 空间潜力 | $D_i$ 社会需求 | $E_i$ 环境现状评分<br>
            <b>权重项:</b> $w$ AHP 层次分析法专家权重系数
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- AHP 判断矩阵 ---
    st.markdown("#### AHP 判断矩阵 (当前权重配置)")
    w_arr = np.array([w_poi, w_soc, w_env], dtype=float)
    w_norm = w_arr / (w_arr.sum() + 0.001)
    ahp_matrix = pd.DataFrame(
        [[1, round(w_norm[0]/(w_norm[1]+0.001), 2), round(w_norm[0]/(w_norm[2]+0.001), 2)],
         [round(w_norm[1]/(w_norm[0]+0.001), 2), 1, round(w_norm[1]/(w_norm[2]+0.001), 2)],
         [round(w_norm[2]/(w_norm[0]+0.001), 2), round(w_norm[2]/(w_norm[1]+0.001), 2), 1]],
        columns=["空间潜力", "社会需求", "环境紧迫"],
        index=["空间潜力", "社会需求", "环境紧迫"]
    )
    st.dataframe(ahp_matrix, use_container_width=True)
    st.caption(f"归一化权重向量: [{w_norm[0]:.3f}, {w_norm[1]:.3f}, {w_norm[2]:.3f}]")

    # --- 主视图：动态排行榜 ---
    st.markdown("### 🏆 更新优先级排行榜 (实时计算结果)")
    st.markdown(f"根据当前专家权重分配，共识别出 **{len(df_filtered)}** 个重点更新候选单元。")
    
    st.dataframe(
        df_filtered[["地块名称", "MPI 得分"]],
        column_config={
            "MPI 得分": st.column_config.ProgressColumn(
                "MPI 综合潜力分",
                help="基于 AHP 权重动态计算所得",
                format="%.1f",
                min_value=0,
                max_value=100,
            )
        },
        use_container_width=True,
        hide_index=True
    )
    
    # --- 指标可视化 ---
    st.markdown("#### 🧬 方案分布散点对撞")
    st.plotly_chart(px.scatter(df_filtered, x="空间潜力原分", y="社会需求原分", size="MPI 得分", color="地块名称", 
                               template="plotly_dark", title="空间潜力与社会需求耦合分布"), use_container_width=True)

# ==========================================
# 🌌 模块 B: 策略语义萃取 (MarkItDown 引擎)
# ==========================================
elif selected_sub == "📑 策略语义萃取":
    with st.sidebar:
        st.markdown("### 📑 02-MarkItDown 引擎")
        p_on = st.toggle("启用第三方插件 (Excel/PPT)", value=False, key="p2_plugins_on")
        ocr_on = st.toggle("LLM 辅助图片描述", value=False, key="p2_ocr_on")
        st.markdown("---")
        st.markdown("#### 🛠️ 导出预设")
        suffix_val = st.text_input("文件名后缀", value="_extracted", key="p2_suffix_val")

    st.markdown("### 📑 MarkItDown 跨模态语义萃取引擎")
    up_files = st.file_uploader("批处理上传规划文档 (PDF/Word/PPT)", accept_multiple_files=True)
    if up_files:
        if st.button("🚀 启动算法萃取", type="primary", use_container_width=True):
            res_list = []
            progress = st.progress(0)
            md_engine = MarkItDown()
            for i, f in enumerate(up_files):
                with open(f"temp_{f.name}", "wb") as t_f:
                    t_f.write(f.getbuffer())
                try:
                    res = md_engine.convert(f"temp_{f.name}")
                    res_list.append({"file": f.name, "text": res.text_content})
                except Exception as e:
                    res_list.append({"file": f.name, "text": f"Error: {e}"})
                finally:
                    if os.path.exists(f"temp_{f.name}"): os.remove(f"temp_{f.name}")
                progress.progress((i+1)/len(up_files))
            st.session_state['lab01_extraction_res'] = res_list
            st.success("✅ 全量算法萃取完成！")

    if 'lab01_extraction_res' in st.session_state:
        results = st.session_state['lab01_extraction_res']
        sel_file = st.selectbox("选择预览结果", [r['file'] for r in results])
        txt = next(r['text'] for r in results if r['file'] == sel_file)
        st.text_area("Markdown 预览窗口", value=txt, height=400)

# ==========================================
# 🌌 模块 C: 物理底座管理 (后台文件访问)
# ==========================================
elif selected_sub == "⚙️ 物理底座管理":
    with st.sidebar:
        st.markdown("### ⚙️ 07-数据底层维护")
        obj_sel = st.selectbox("选择管理对象:", ["🏪 POI数据", "🚥 交通数据", "📊 CV分析结果", "💬 情感分析数据"], key="p7_mgr_sel")
        st.info("💡 文件副本将实时同步至 data/ 目录。")

    st.markdown("### ⚙️ 后台地理数据资产管理")
    f_map = {
        "🏪 POI数据": "Changchun_POI_Real.csv", 
        "🚥 交通数据": "Changchun_Traffic_Real.csv", 
        "📊 CV分析结果": "GVI_Results_Analysis.csv",
        "💬 情感分析数据": "CV_NLP_RawData.csv"
    }
    file_key_map = {
        "🏪 POI数据": "poi",
        "🚥 交通数据": "traffic",
        "📊 CV分析结果": "gvi",
        "💬 情感分析数据": "nlp",
    }
    target_csv = DATA_FILES[file_key_map[obj_sel]]
    if target_csv.exists():
        st.dataframe(pd.read_csv(target_csv).head(30), use_container_width=True)
        uploaded_csv = st.file_uploader("覆盖上传最新的物理副本", key="p7_csv_up")
        if uploaded_csv is not None:
            with target_csv.open("wb") as f:
                f.write(uploaded_csv.getbuffer())
            st.success(f"文件已覆盖写入: {target_csv.as_posix()}")
            st.rerun()
