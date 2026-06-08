"""
绘制 ultimateDESIGN 平台开源技术栈完整清单图表
横板布局，适配 16:9 PPT 幻灯片，超清可读
"""
import matplotlib.pyplot as plt
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ── 完整库清单，按类别分组 ──
data = [
    ("GIS 与空间分析", "#4f46e5", [
        ("GeoPandas",   ">=0.14",  "地理空间矢量数据读取、裁切与分析"),
        ("OSMnx",       ">=1.0",   "OpenStreetMap 路网/铁轨自动获取"),
        ("Shapely",     ">=2.0",   "几何运算（质心/缓冲区/相交）"),
        ("PyProj",      ">=3.6",   "WGS84 / UTM 坐标投影转换"),
        ("Rasterio",    ">=1.3",   "遥感与卫星栅格影像读写"),
        ("Fiona",       ">=1.9",   "GIS 多格式矢量文件驱动"),
        ("Momepy",      ">=0.6",   "城市形态指标（密度/围合度）"),
        ("Pandana",     ">=0.7",   "路网可达性与通勤时间计算"),
        ("PySAL",       ">=23.0",  "空间自相关 Moran's I / 聚类"),
    ]),
    ("Web 交互与地图可视化", "#2563eb", [
        ("Streamlit",        "==1.55.0", "17 阶段全流程交互界面主框架"),
        ("PyDeck / Deck.GL", ">=0.8",    "3D 建筑白膜/空间品质柱体渲染"),
        ("Folium",           "==0.20.0", "Leaflet 2D 交互地图展示"),
        ("Streamlit-Folium", "==0.22.1", "Folium 与 Streamlit 双向集成"),
        ("Plotly",           "==6.6.0",  "雷达图/占比饼图/折线图"),
        ("Kepler.gl",        ">=0.3",    "万级建筑斑块高密度可视化"),
    ]),
    ("文档解析与外部接口", "#0d9488", [
        ("Requests",     "==2.32.3",   "Ollama / SD WebUI / API 通信"),
        ("PyMuPDF",      "==1.24.11",  "PDF 结构化文本提取 → RAG"),
        ("Pillow",       "==11.3.0",   "A3 图框排版/图例合成/画布拼合"),
        ("PyYAML",       "==6.0.2",    "全局配置 config.yaml 加载"),
        ("python-dotenv","==1.0.1",    ".env 密钥隔离（AK/DeepSeek）"),
        ("Mammoth",      "==1.8.0",    "Word docx → HTML 无损转换"),
    ]),
    ("大模型、AI 与 NLP", "#7c3aed", [
        ("PyTorch",      ">=2.5.0",  "张量运算 / GPU 加速推理后端"),
        ("TorchVision",  ">=0.20.0", "图像预处理与视觉模型支持"),
        ("Transformers", ">=4.40.0", "HuggingFace 语义表征/NLP"),
        ("Jieba",        "==0.42.1", "中文分词 → 热词词云/情感分析"),
        ("MarkItDown",   "==0.0.1a3","微软 PDF/docx → Markdown"),
    ]),
    ("数据处理与数值计算", "#059669", [
        ("Pandas",   ">=2.0",   "DataFrame 指标/品质分值管理"),
        ("NumPy",    ">=1.24",  "矩阵运算 / 百分位归一化"),
        ("SciPy",    ">=1.10",  "AHP 特征向量 / 高维插值"),
        ("OpenPyXL", "==3.1.5", "Excel 报表读写"),
    ]),
    ("DevOps 自动化与工程", "#dc2626", [
        ("Pytest",     "==9.0.3",  "173 项单元测试全覆盖"),
        ("Ruff",       "==0.15.11","秒级代码静态分析与格式检查"),
        ("Selenium",   "==4.25.0", "浏览器自动化冒烟/集成测试"),
        ("Pre-commit", "==3.8.0",  "Git 钩子拦截代码质量问题"),
    ]),
]

# ── 将 6 个类别分为左右两栏（各 3 组）──
left_data = data[:3]   # GIS(9) + Web(6) + 文档(6) = 21
right_data = data[3:]  # AI(5) + 数据(4) + DevOps(4) = 13

def count_rows(groups):
    """类别标题行 + 库行"""
    return sum(1 + len(libs) for _, _, libs in groups)

left_rows = count_rows(left_data)
right_rows = count_rows(right_data)
max_rows = max(left_rows, right_rows)

# ── 画布（横版 16:9 超宽）──
rh = 0.52  # 行高
fig_w = 28
fig_h = max_rows * rh + 3.5
fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=200, facecolor='white')
ax.set_facecolor('white')

# ── 标题 ──
title_y = max_rows * rh + 2.2
ax.text(fig_w / 2, title_y,
        'ultimateDESIGN 平台开源技术栈完整清单（共 34 个核心依赖库）',
        fontsize=22, fontweight='bold', color='#0f172a',
        va='center', ha='center')
ax.text(fig_w / 2, title_y - 0.65,
        '数据来源：requirements.txt & requirements_gis.txt  |  ultimateDESIGN v4.6.0',
        fontsize=11, color='#94a3b8', va='center', ha='center', style='italic')

# ── 表头 ──
header_y = title_y - 1.6
left_x0 = 0.2
right_x0 = fig_w / 2 + 0.3
col_w = fig_w / 2 - 0.5  # 每栏宽度

for x0 in [left_x0, right_x0]:
    ax.fill_between([x0, x0 + col_w], header_y, header_y + rh,
                    color='#0f172a', zorder=2)
    ax.text(x0 + 0.3,  header_y + rh/2, "序号", fontsize=12, fontweight='bold',
            color='white', va='center', ha='left', zorder=3)
    ax.text(x0 + 1.2,  header_y + rh/2, "开源库名称", fontsize=12, fontweight='bold',
            color='white', va='center', ha='left', zorder=3)
    ax.text(x0 + 5.0,  header_y + rh/2, "版本", fontsize=12, fontweight='bold',
            color='white', va='center', ha='left', zorder=3)
    ax.text(x0 + 7.2,  header_y + rh/2, "在本项目中的核心应用", fontsize=12, fontweight='bold',
            color='white', va='center', ha='left', zorder=3)

# ── 绘制函数 ──
def draw_column(groups, x0, col_w, start_y, start_idx):
    y = start_y
    idx = start_idx
    for cat_name, cat_color, libs in groups:
        # 类别标题行
        ax.fill_between([x0, x0 + col_w], y - rh, y, color=cat_color, alpha=0.10, zorder=1)
        ax.plot([x0, x0 + col_w], [y, y], color=cat_color, linewidth=1.5, alpha=0.6, zorder=2)
        ax.text(x0 + 0.3, y - rh/2, f"▎{cat_name}（{len(libs)} 个）",
                fontsize=13, fontweight='bold', color=cat_color, va='center', ha='left', zorder=3)
        y -= rh

        for lib_name, lib_ver, lib_desc in libs:
            idx += 1
            # 斑马纹
            if idx % 2 == 0:
                ax.fill_between([x0, x0 + col_w], y - rh, y, color='#f1f5f9', zorder=0)
            # 底部线
            ax.plot([x0, x0 + col_w], [y - rh, y - rh], color='#e2e8f0', linewidth=0.5, zorder=1)

            ax.text(x0 + 0.5,  y - rh/2, f"{idx:02d}", fontsize=11, color='#94a3b8',
                    va='center', ha='center', fontfamily='monospace', zorder=3)
            ax.text(x0 + 1.2,  y - rh/2, lib_name, fontsize=12.5, fontweight='bold',
                    color='#1e293b', va='center', ha='left', zorder=3)
            ax.text(x0 + 5.0,  y - rh/2, lib_ver, fontsize=10.5, color='#64748b',
                    va='center', ha='left', fontfamily='monospace', zorder=3)
            ax.text(x0 + 7.2,  y - rh/2, lib_desc, fontsize=11.5, color='#334155',
                    va='center', ha='left', zorder=3)
            y -= rh
    return idx

# ── 绘制左栏和右栏 ──
start_y = header_y
end_idx = draw_column(left_data,  left_x0,  col_w, start_y, 0)
draw_column(right_data, right_x0, col_w, start_y, end_idx)

# ── 中间分隔线 ──
sep_x = fig_w / 2 + 0.05
ax.plot([sep_x, sep_x], [start_y - max_rows * rh - 0.5, start_y + rh],
        color='#cbd5e1', linewidth=1.2, linestyle='-', alpha=0.6, zorder=1)

# ── 隐藏坐标轴 ──
ax.set_xlim(0, fig_w)
ax.set_ylim(start_y - max_rows * rh - 1.0, title_y + 0.8)
ax.axis('off')

plt.tight_layout(pad=0.5)

save_path = os.path.join("static", "libs_distribution_chart.png")
plt.savefig(save_path, bbox_inches='tight', facecolor='white', dpi=200)
print(f"Success: Chart saved at {save_path}")
