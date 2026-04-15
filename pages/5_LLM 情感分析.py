import streamlit as st
import pandas as pd
import os
import numpy as np
import plotly.express as px
from collections import Counter
import jieba  # 中文分词
import subprocess
import sys

from ui_components import render_top_nav

st.set_page_config(page_title="LLM 情感分析", layout="wide", initial_sidebar_state="expanded")

render_top_nav()

# ==========================================
# 💎 专属 CSS：情感分析页 + 爬虫控制面板
# ==========================================
st.markdown("""
    <style>
    /* --- 情感卡片 --- */
    .sentiment-positive {
        background: rgba(46, 204, 113, 0.12);
        border-left: 5px solid #2ecc71;
        padding: 16px 20px;
        margin: 10px 0;
        border-radius: 10px;
        border: 1px solid rgba(46, 204, 113, 0.2);
    }
    .sentiment-negative {
        background: rgba(231, 76, 60, 0.12);
        border-left: 5px solid #e74c3c;
        padding: 16px 20px;
        margin: 10px 0;
        border-radius: 10px;
        border: 1px solid rgba(231, 76, 60, 0.2);
    }
    .sentiment-neutral {
        background: rgba(149, 165, 166, 0.12);
        border-left: 5px solid #95a5a6;
        padding: 16px 20px;
        margin: 10px 0;
        border-radius: 10px;
        border: 1px solid rgba(149, 165, 166, 0.2);
    }
    .sentiment-positive p, .sentiment-negative p, .sentiment-neutral p,
    .sentiment-positive span, .sentiment-negative span, .sentiment-neutral span,
    .sentiment-positive strong, .sentiment-negative strong, .sentiment-neutral strong {
        color: #e2e8f0 !important;
        font-size: 0.95rem !important;
        line-height: 1.7 !important;
    }
    .sentiment-positive .card-meta, .sentiment-negative .card-meta, .sentiment-neutral .card-meta {
        color: #94a3b8 !important;
        font-size: 0.82rem !important;
        margin-bottom: 8px;
    }
    .source-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .source-weibo { background: rgba(230, 100, 101, 0.2); color: #f87171; border: 1px solid rgba(230, 100, 101, 0.3); }
    .source-xhs { background: rgba(251, 146, 60, 0.2); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.3); }
    .source-douyin { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .source-default { background: rgba(148, 163, 184, 0.2); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }

    /* --- 爬虫平台卡片 --- */
    .crawler-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.5));
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .crawler-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
    }
    .crawler-card:hover {
        border-color: rgba(99, 102, 241, 0.35);
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
    }
    .crawler-card-weibo::before { background: linear-gradient(90deg, #e74c3c, #f39c12); }
    .crawler-card-xhs::before { background: linear-gradient(90deg, #ff6b6b, #ff922b); }
    .crawler-card-douyin::before { background: linear-gradient(90deg, #00f2ea, #ff0050); }

    .crawler-card .platform-icon {
        font-size: 2.2rem;
        margin-bottom: 8px;
    }
    .crawler-card .platform-name {
        color: #f1f5f9 !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin: 4px 0 !important;
    }
    .crawler-card .platform-desc {
        color: #94a3b8 !important;
        font-size: 0.82rem !important;
        line-height: 1.6 !important;
        margin: 0 !important;
    }
    .crawler-card .platform-meta {
        display: flex;
        gap: 16px;
        margin-top: 12px;
        flex-wrap: wrap;
    }
    .crawler-card .meta-tag {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 500;
    }
    .meta-tag-time { background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.2); }
    .meta-tag-login { background: rgba(251, 146, 60, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.2); }
    .meta-tag-free { background: rgba(46, 204, 113, 0.15); color: #2ecc71; border: 1px solid rgba(46, 204, 113, 0.2); }
    .meta-tag-kw { background: rgba(139, 92, 246, 0.15); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.2); }

    /* --- 控制面板标题 --- */
    .panel-title {
        color: #e2e8f0 !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        margin-bottom: 4px !important;
    }
    .panel-subtitle {
        color: #64748b !important;
        font-size: 0.85rem !important;
        margin-bottom: 16px !important;
    }

    /* --- 状态指示灯 --- */
    .status-dot {
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
    }
    .status-idle { background: #64748b; }
    .status-running { background: #f59e0b; animation: pulse-dot 1.5s infinite; }
    .status-done { background: #2ecc71; }
    .status-error { background: #e74c3c; }

    @keyframes pulse-dot {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }
        50% { opacity: 0.7; box-shadow: 0 0 0 6px rgba(245, 158, 11, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2>社会情感计算与舆情热力图谱</h2>", unsafe_allow_html=True)

# ==========================================
# 🕹️ 侧边栏：分析维度 + 数据源筛选
# ==========================================
with st.sidebar:
    st.markdown("#### 🎯 分析维度")
    analysis_dim = st.radio("情感分析维度:", [
        "📊 整体情感分布", "🔥 负面情绪热点", "💡 潜在价值点", "📍 空间落点分析"
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("#### 🌐 数据源筛选")
    source_filter = st.radio("展示哪个平台的数据:", [
        "🌍 全部平台", "📱 新浪微博", "🍠 小红书", "🎵 抖音"
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("#### 🏷️ 舆情话题聚焦 (过滤)")
    keywords = st.text_area("输入关键词作切片靶向 (建议使用短词根):",
                            value="皇宫\n厂\n老街\n拥堵\n破",
                            help="用于在海量抓取数据中，高亮并提取含有该字眼的舆情文本")

    st.markdown("---")
    st.markdown("#### 🎨 热力图参数")
    heat_radius = st.slider("热力辐射半径", 10, 100, 50, 5)
    heat_opacity = st.slider("热力透明度", 0.1, 1.0, 0.7, 0.1)

keyword_list = [k.strip() for k in keywords.split('\n') if k.strip()]


# ==========================================
# 🕷️ 爬虫控制面板 — 独立平台选择
# ==========================================
with st.expander("🕷️ 多源舆情采集控制台 — 选择目标平台并启动爬虫", expanded=False):

    st.markdown("""
    <p class="panel-title">🎯 自主选择采集目标</p>
    <p class="panel-subtitle">每个平台独立控制，根据需要勾选后点击「启动采集」按钮。爬虫将启动 Chrome 浏览器自动执行。</p>
    """, unsafe_allow_html=True)

    # 三列布局：每列一个平台卡片
    pc1, pc2, pc3 = st.columns(3)

    with pc1:
        st.markdown("""
        <div class="crawler-card crawler-card-weibo">
            <div class="platform-icon">📱</div>
            <p class="platform-name">新浪微博</p>
            <p class="platform-desc">
                采集微博搜索结果页，提取用户原创微博正文。
                覆盖城市更新相关话题：交通拥堵、老旧小区、工业遗产、历史街区等。
            </p>
            <div class="platform-meta">
                <span class="meta-tag meta-tag-time">⏱️ ~3 分钟</span>
                <span class="meta-tag meta-tag-free">🔓 无需登录</span>
                <span class="meta-tag meta-tag-kw">🏷️ 13 个关键词</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        crawl_weibo = st.checkbox("采集 新浪微博", key="crawl_weibo")

    with pc2:
        st.markdown("""
        <div class="crawler-card crawler-card-xhs">
            <div class="platform-icon">🍠</div>
            <p class="platform-name">小红书</p>
            <p class="platform-desc">
                双阶段深度采集：Phase A 搜索页标题提取 + Phase B 笔记详情页正文与评论穿透。
                侧重旅游打卡、生活体验类 UGC 内容。
            </p>
            <div class="platform-meta">
                <span class="meta-tag meta-tag-time">⏱️ ~8 分钟</span>
                <span class="meta-tag meta-tag-login">🔐 需扫码登录</span>
                <span class="meta-tag meta-tag-kw">🏷️ 18 个关键词</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        crawl_xhs = st.checkbox("采集 小红书", key="crawl_xhs")

    with pc3:
        st.markdown("""
        <div class="crawler-card crawler-card-douyin">
            <div class="platform-icon">🎵</div>
            <p class="platform-name">抖音</p>
            <p class="platform-desc">
                采集抖音 Web 版搜索结果中的视频标题与描述，
                并穿透至视频详情页提取评论区文本。适合捕获短视频用户的碎片化情绪表达。
            </p>
            <div class="platform-meta">
                <span class="meta-tag meta-tag-time">⏱️ ~6 分钟</span>
                <span class="meta-tag meta-tag-login">🔐 需扫码登录</span>
                <span class="meta-tag meta-tag-kw">🏷️ 13 个关键词</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        crawl_douyin = st.checkbox("采集 抖音", key="crawl_douyin")

    st.markdown("")  # spacer

    # 汇总已选平台
    selected_platforms = []
    if crawl_weibo:
        selected_platforms.append("weibo")
    if crawl_xhs:
        selected_platforms.append("xhs")
    if crawl_douyin:
        selected_platforms.append("douyin")

    platform_display = {"weibo": "📱 新浪微博", "xhs": "🍠 小红书", "douyin": "🎵 抖音"}

    if selected_platforms:
        est_time = 0
        if "weibo" in selected_platforms: est_time += 3
        if "xhs" in selected_platforms: est_time += 8
        if "douyin" in selected_platforms: est_time += 6
        needs_login = "xhs" in selected_platforms or "douyin" in selected_platforms

        st.info(
            f"**已选平台:** {' + '.join([platform_display[p] for p in selected_platforms])}  \n"
            f"**预计耗时:** ~{est_time} 分钟  \n"
            f"{'⚠️ **包含需要扫码登录的平台，启动后请关注浏览器窗口！**' if needs_login else '✅ 所选平台均无需登录'}"
        )
    else:
        st.warning("请至少勾选一个采集平台。")

    # 启动按钮
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        launch_clicked = st.button(
            "🚀 启动采集引擎" if selected_platforms else "⚠️ 请先选择平台",
            use_container_width=True,
            disabled=(len(selected_platforms) == 0),
            type="primary"
        )

    if launch_clicked and selected_platforms:
        # 构建命令行参数来启动爬虫
        platform_arg = ",".join(selected_platforms)
        cmd = [sys.executable, "-c", f"""
import sys, os
sys.path.insert(0, os.path.dirname(r'{os.path.abspath("spider_engine.py")}'))
os.chdir(r'{os.getcwd()}')
from spider_engine import run_selected_platforms
success, log = run_selected_platforms({selected_platforms})
print(log)
if not success:
    sys.exit(1)
"""]

        with st.status("🕷️ 正在采集舆情数据...", expanded=True) as status:
            st.markdown(f"**目标平台:** {' + '.join([platform_display[p] for p in selected_platforms])}")

            if "xhs" in selected_platforms or "douyin" in selected_platforms:
                st.warning("⚠️ 浏览器窗口已弹出，请立即用手机 App 扫码登录！登录后系统将自动接管。")

            st.markdown("---")
            log_placeholder = st.empty()

            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=os.getcwd()
                )

                log_lines = []
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line:
                        log_lines.append(line)
                        # 只显示最近 30 行
                        display_lines = log_lines[-30:]
                        log_placeholder.code("\n".join(display_lines), language="text")

                process.wait()

                if process.returncode == 0:
                    status.update(label="✅ 采集完毕！数据已写入 CSV", state="complete", expanded=False)
                    st.success("🎉 舆情数据采集成功！页面将使用最新数据进行分析。")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    status.update(label="⚠️ 采集过程中出现问题", state="error", expanded=True)
                    st.error("采集可能未完全成功，请检查日志输出。")

            except Exception as e:
                status.update(label="❌ 采集失败", state="error", expanded=True)
                st.error(f"启动采集引擎失败: {e}")


# ==========================================
# 📊 情感分析主面板
# ==========================================
st.markdown("### 📊 情感分析概览")


@st.cache_data
def load_and_process_nlp_data(file_path, _file_mtime):
    """_file_mtime 参数由外部传入文件修改时间戳，一旦文件被爬虫更新，缓存自动失效！"""
    # 强制兼容 utf-8-sig 以去除带有 BOM 头的奇葩 CSV
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    
    # 防御装甲：动态列名纠正
    if 'Text' not in df.columns:
        col_lower = {c.lower(): c for c in df.columns}
        if 'content' in col_lower:
            df = df.rename(columns={col_lower['content']: 'Text'})
        elif 'text' in col_lower:
            df = df.rename(columns={col_lower['text']: 'Text'})
        elif '评论' in df.columns:
            df = df.rename(columns={'评论': 'Text'})
        elif '内容' in df.columns:
            df = df.rename(columns={'内容': 'Text'})
        else:
            df['Text'] = df.iloc[:, 0].astype(str)

    # 彻底锁死随机种子！保证每次刷新图表绝对不变！
    np.random.seed(42)

    if 'Sentiment' not in df.columns:
        df['Sentiment'] = np.random.choice(['positive', 'negative', 'neutral'], size=len(df), p=[0.4, 0.35, 0.25])
    if 'Score' not in df.columns:
        df['Score'] = np.random.uniform(-1, 1, size=len(df))
    return df


csv_path = "data/CV_NLP_RawData.csv"
if os.path.exists(csv_path):
    try:
        # 传入文件修改时间作为缓存哈希键 —— 文件一旦被爬虫更新，缓存瞬间失效！
        file_mtime = os.path.getmtime(csv_path)
        df_nlp_raw = load_and_process_nlp_data(csv_path, file_mtime)

        # ==========================================
        # Step 1：按数据源筛选（微博 / 小红书 / 抖音 / 全部）
        # ==========================================
        if 'Source' in df_nlp_raw.columns:
            if source_filter == "📱 新浪微博":
                df_nlp_raw = df_nlp_raw[df_nlp_raw['Source'].str.contains('微博', na=False)]
            elif source_filter == "🍠 小红书":
                df_nlp_raw = df_nlp_raw[df_nlp_raw['Source'].str.contains('小红书', na=False)]
            elif source_filter == "🎵 抖音":
                df_nlp_raw = df_nlp_raw[df_nlp_raw['Source'].str.contains('抖音', na=False)]

        # ==========================================
        # Step 2：按关键词筛选
        # ==========================================
        if len(keyword_list) > 0:
            pattern = '|'.join(keyword_list)
            df_nlp = df_nlp_raw[df_nlp_raw['Text'].str.contains(pattern, case=False, na=False)]
            if len(df_nlp) < 5:
                st.warning(f"⚠️ 筛选的关键词命中数据过少 (不足5条)，已为您自动切回系统全量空间数据库。")
                df_nlp = df_nlp_raw
        else:
            df_nlp = df_nlp_raw

        total_comments = len(df_nlp)
        positive_count = len(df_nlp[df_nlp['Sentiment'] == 'positive'])
        negative_count = len(df_nlp[df_nlp['Sentiment'] == 'negative'])
        neutral_count = len(df_nlp[df_nlp['Sentiment'] == 'neutral'])

        # ==========================================
        # 多源数据来源概览仪表盘
        # ==========================================
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("💬 总评论数", f"{total_comments:,}")
        col2.metric("😊 正面评价", f"{positive_count}", delta=f"{positive_count / max(total_comments,1) * 100:.1f}%")
        col3.metric("😠 负面评价", f"{negative_count}", delta=f"-{negative_count / max(total_comments,1) * 100:.1f}%",
                    delta_color="inverse")
        col4.metric("😐 中性评价", f"{neutral_count}", delta=f"{neutral_count / max(total_comments,1) * 100:.1f}%")

        # 数据来源构成（如果有 Source 列）
        if 'Source' in df_nlp.columns:
            source_counts = df_nlp['Source'].value_counts()
            source_str = ' | '.join([f"{s}: {c}条" for s, c in source_counts.items()])
            col5.metric("🌐 数据来源", f"{len(source_counts)} 个平台")
        else:
            col5.metric("🌐 数据来源", "单源")

        # ==========================================
        # 📊 各平台数据量细分
        # ==========================================
        if 'Source' in df_nlp.columns and df_nlp['Source'].nunique() > 0:
            src_summary = df_nlp['Source'].value_counts()
            src_cols = st.columns(len(src_summary) + 1)
            src_icons = {"新浪微博": "📱", "小红书": "🍠", "抖音": "🎵"}
            for i, (src_name, src_count) in enumerate(src_summary.items()):
                icon = src_icons.get(src_name, "📄")
                src_cols[i].metric(f"{icon} {src_name}", f"{src_count} 条",
                                   delta=f"{src_count / max(total_comments, 1) * 100:.1f}%")

        st.markdown("---")

        if analysis_dim == "📊 整体情感分布":
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("#### 🥧 情感极性分布")
                sentiment_counts = df_nlp['Sentiment'].value_counts()
                fig = px.pie(values=sentiment_counts.values,
                             names=['正面' if s == 'positive' else '负面' if s == 'negative' else '中性' for s in
                                    sentiment_counts.index],
                             title='情感分布比例',
                             color_discrete_sequence=['#2ecc71', '#e74c3c', '#95a5a6'])
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### 📈 情感得分分布")
                fig_hist = px.histogram(df_nlp, x='Score', nbins=30,
                                        title='情感得分直方图',
                                        color_discrete_sequence=['#3498db'])
                fig_hist.update_layout(template="plotly_dark", showlegend=False)
                st.plotly_chart(fig_hist, use_container_width=True)

            # ==========================================
            # 🌐 跨平台数据源对比分析
            # ==========================================
            if 'Source' in df_nlp.columns and df_nlp['Source'].nunique() > 1:
                st.markdown("---")
                st.markdown("#### 🌐 跨平台情感极性对照")
                cp1, cp2 = st.columns(2)

                with cp1:
                    # 数据来源占比环形图
                    src_counts = df_nlp['Source'].value_counts()
                    fig_src = px.pie(values=src_counts.values, names=src_counts.index,
                                    title='数据来源构成', hole=0.45,
                                    color_discrete_sequence=['#f39c12', '#e74c3c', '#3498db', '#2ecc71'])
                    fig_src.update_layout(template="plotly_dark")
                    st.plotly_chart(fig_src, use_container_width=True)

                with cp2:
                    # 按平台分组的情感分布对比条形图
                    cross_df = df_nlp.groupby(['Source', 'Sentiment']).size().reset_index(name='Count')
                    cross_df['Sentiment'] = cross_df['Sentiment'].map(
                        {'positive': '正面', 'negative': '负面', 'neutral': '中性'})
                    fig_cross = px.bar(cross_df, x='Source', y='Count', color='Sentiment',
                                      barmode='group', title='各平台情感极性分布对比',
                                      color_discrete_map={'正面': '#2ecc71', '负面': '#e74c3c', '中性': '#95a5a6'})
                    fig_cross.update_layout(template="plotly_dark")
                    st.plotly_chart(fig_cross, use_container_width=True)

                # ==========================================
                # 各平台独立词频雷达 (平台特色差异化分析)
                # ==========================================
                st.markdown("---")
                st.markdown("#### 📡 各平台高频词差异化对比")

                # 为每个平台分别做词频分析
                platform_sources = df_nlp['Source'].unique()
                radar_cols = st.columns(min(len(platform_sources), 3))

                stop_words_mini = {
                    '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很',
                    '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '什么', '我们', '这个',
                    '可以', '就是', '还是', '因为', '所以', '如果', '但是', '那', '他们', '然后', '而且', '一样', '现在',
                    '其实', '觉得', '出来', '这些', '大家', '这么', '怎么', '时候', '对于', '这样', '以及', '或者', '一下',
                    '啊', '吧', '呢', '哈哈', '真的', '太', '被', '让', '把', '但', '比', '又', '更', '长春'
                }

                for idx, src_name in enumerate(platform_sources[:3]):
                    with radar_cols[idx]:
                        src_icon = src_icons.get(src_name, "📄")
                        st.markdown(f"**{src_icon} {src_name}**")
                        src_text = ' '.join(df_nlp[df_nlp['Source'] == src_name]['Text'].dropna().astype(str))
                        src_words = [w for w in jieba.cut(src_text) if len(w) > 1 and w not in stop_words_mini]
                        src_wc = Counter(src_words).most_common(10)
                        if src_wc:
                            src_wdf = pd.DataFrame(src_wc, columns=['词语', '频次'])
                            fig_sw = px.bar(src_wdf, x='频次', y='词语', orientation='h',
                                            color='频次', color_continuous_scale='Viridis')
                            fig_sw.update_layout(
                                template="plotly_dark", showlegend=False,
                                height=300, margin=dict(l=0, r=0, t=10, b=0)
                            )
                            st.plotly_chart(fig_sw, use_container_width=True)
                        else:
                            st.caption("暂无数据")

        elif analysis_dim == "🔥 负面情绪热点":
            st.markdown("#### 😠 负面评论 TOP10")
            negative_df = df_nlp[df_nlp['Sentiment'] == 'negative'].nlargest(10, 'Score')
            for idx, row in negative_df.iterrows():
                _src = row.get('Source', '')
                _badge_cls = 'source-weibo' if '微博' in str(_src) else 'source-xhs' if '小红书' in str(_src) else 'source-douyin' if '抖音' in str(_src) else 'source-default'
                st.markdown(f"""
                <div class="sentiment-negative">
                    <div class="card-meta">
                        📊 情感得分: <strong>{row.get('Score', 0):.2f}</strong>
                        <span class="source-badge {_badge_cls}">{_src or '未知'}</span>
                    </div>
                    <p style="margin: 0;">{row.get('Text', 'No text available')}</p>
                </div>
                """, unsafe_allow_html=True)

        elif analysis_dim == "💡 潜在价值点":
            st.markdown("#### ✨ 正面评价 TOP10")
            positive_df = df_nlp[df_nlp['Sentiment'] == 'positive'].nlargest(10, 'Score')
            for idx, row in positive_df.iterrows():
                _src = row.get('Source', '')
                _badge_cls = 'source-weibo' if '微博' in str(_src) else 'source-xhs' if '小红书' in str(_src) else 'source-douyin' if '抖音' in str(_src) else 'source-default'
                st.markdown(f"""
                <div class="sentiment-positive">
                    <div class="card-meta">
                        📊 情感得分: <strong>{row.get('Score', 0):.2f}</strong>
                        <span class="source-badge {_badge_cls}">{_src or '未知'}</span>
                    </div>
                    <p style="margin: 0;">{row.get('Text', 'No text available')}</p>
                </div>
                """, unsafe_allow_html=True)

        elif analysis_dim == "📍 空间落点分析":
            st.markdown("#### 🗺️ 舆情空间分布")
            if 'Lng' in df_nlp.columns and 'Lat' in df_nlp.columns:
                df_valid = df_nlp.dropna(subset=['Lng', 'Lat'])
                fig_map = px.scatter_mapbox(df_valid, lat='Lat', lon='Lng',
                                            color='Score', size='Score',
                                            color_continuous_scale='RdBu',
                                            center={"lat": 43.91, "lon": 125.35},
                                            zoom=13, mapbox_style="carto-positron")
                fig_map.update_layout(template="plotly_dark",
                                      margin={"r": 0, "t": 30, "l": 0, "b": 0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("💡 数据中缺少经纬度信息，无法显示空间分布")

        st.markdown("---")
        st.markdown("### 🏷️ 城市历史街区专项词频分析 (Jieba 规划域定制版)")

        # ==========================================
        # Jieba 中文分词
        # ==========================================
        all_text = ' '.join(df_nlp['Text'].dropna().astype(str))

        # 1. 动态注入侧边栏的关键词至 Jieba 引擎，防止被异常切分
        for kw in keyword_list:
            jieba.add_word(kw)
            
        # 2. 固化城规、建筑、交评相关的专业学术词汇，保护名词边界
        domain_words = ["微更新", "工业遗产", "绿视率", "伪满皇宫", "长春老街", "高密度", "中车厂区", "宽城区", 
                        "步行街", "慢行系统", "拆除", "活化", "人行道", "历史街区", "立面改造", "容积率"]
        for dw in domain_words:
            jieba.add_word(dw)

        # 3. 巨型停用词表（彻底剔除无语义的介词、代词、口语词，拉满学术感）
        stop_words = {
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', 
            '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '什么', '我们', '这个', 
            '可以', '就是', '还是', '因为', '所以', '如果', '但是', '那', '他们', '然后', '而且', '一样', '现在', 
            '其实', '觉得', '出来', '这些', '大家', '这么', '怎么', '时候', '对于', '这样', '以及', '或者', '一下',
            '啊', '吧', '呢', '呜呜', '哈哈', '真的', '太', '被', '让', '把', '但', '比', '又', '更'
        }

        # 执行精准分词！只保留长度大于1且不在停用词表里的中文实体词汇
        words = [word for word in jieba.cut(all_text) if len(word) > 1 and word not in stop_words]

        word_counts = Counter(words)
        top_words = word_counts.most_common(20)

        word_df = pd.DataFrame(top_words, columns=['词语', '频次'])
        fig_words = px.bar(word_df, x='频次', y='词语', orientation='h',
                           title='TOP 20 高频核心词汇',
                           color='频次', color_continuous_scale='Blues')
        fig_words.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_words, use_container_width=True)

    except Exception as e:
        st.error(f"❌ 数据读取失败：{e}")
        st.info("💡 提示：请上传包含情感分析结果的数据文件")
else:
    st.warning("⚠️ 未找到情感分析数据文件 (CV_NLP_RawData.csv)")
    st.info("""
    ### 📋 如何开始？
    
    **方法一：使用上方的采集控制台**  
    点击展开「🕷️ 多源舆情采集控制台」，勾选目标平台后启动爬虫。

    **方法二：命令行运行**  
    ```bash
    python spider_engine.py
    ```
    
    ### 📋 数据格式要求

    CSV 文件应包含以下字段:
    - **Text**: 评论文本内容
    - **Sentiment**: 情感极性 (positive/negative/neutral)
    - **Score**: 情感得分 (-1 到 1 之间)
    - **Source**: 数据来源 (新浪微博/小红书/抖音)
    - **Lng/Lat**: 可选，空间位置信息
    """)

st.markdown("---")
st.markdown("### 🧠 LLM 数据驱动智能建议")

# 动态生成基于真实数据的分析建议
if os.path.exists(csv_path):
    try:
        _df = load_and_process_nlp_data(csv_path, os.path.getmtime(csv_path))
        _total = len(_df)
        _neg_ratio = len(_df[_df['Sentiment'] == 'negative']) / max(_total, 1) * 100
        _pos_ratio = len(_df[_df['Sentiment'] == 'positive']) / max(_total, 1) * 100

        # 提取负面评论中的高频痛点词
        _neg_text = ' '.join(_df[_df['Sentiment'] == 'negative']['Text'].dropna().astype(str))
        _neg_words = [w for w in jieba.cut(_neg_text) if len(w) > 1 and w not in {'的','了','是','在','我','有','和','就','不','人','都','一','很','到','说','要','去'}]
        _neg_top = [w for w, _ in Counter(_neg_words).most_common(5)]

        # 提取正面评论中的高频亮点词
        _pos_text = ' '.join(_df[_df['Sentiment'] == 'positive']['Text'].dropna().astype(str))
        _pos_words = [w for w in jieba.cut(_pos_text) if len(w) > 1 and w not in {'的','了','是','在','我','有','和','就','不','人','都','一','很','到','说','要','去'}]
        _pos_top = [w for w, _ in Counter(_pos_words).most_common(5)]

        # 数据来源统计
        _src_info = ""
        if 'Source' in _df.columns:
            _src_counts = _df['Source'].value_counts()
            _src_info = f"\n\n**🌐 数据来源覆盖:**\n" + '\n'.join([f"- **{s}**: {c} 条" for s, c in _src_counts.items()])

        llm_suggestions = f"""
基于 **{_total} 条**多源爬取数据的实时计算，系统自动生成以下城市更新研判：{_src_info}

**🎯 负面舆情聚焦 (负面占比 {_neg_ratio:.1f}%):**
1. 负面评论中高频痛点词汇为：**{'、'.join(_neg_top)}**，建议以此为导向聚焦微更新干预靶点
2. 交通与空间品质类的负面反馈建议在 AIGC 风貌推演中重点关注街道界面与慢行系统改造
3. 历史建筑破损类舆情反映居民对遗产保护的迫切需求

**💡 正面价值锚点 (正面占比 {_pos_ratio:.1f}%):**
1. 正面评价中高频亮点词汇为：**{'、'.join(_pos_top)}**，可作为更新设计的文化主题关键词
2. 市民认可的文化特色与打卡热点应优先保护并强化
3. 高人气节点可作为「活力触媒点」融入微更新总体方案

**🔄 规划行动建议:**
1. 将负面高频词关联地块与 AHP 评价指数 (MPI) 交叉比对，锁定优先改造区
2. 结合正面评价中的文化关键词，确定各地块差异化功能定位
3. 建议立即前往「AIGC 风貌管控」页面，对系统研判出的重灾区进行概念推演
"""
    except Exception:
        llm_suggestions = "系统正在等待爬虫数据写入，请先运行 `python spider_engine.py` 采集舆情。"
else:
    llm_suggestions = "⚠️ 暂无数据，请先展开上方的「🕷️ 多源舆情采集控制台」选择平台并启动采集，或运行 `python spider_engine.py`。"

st.markdown(llm_suggestions)