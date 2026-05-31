import matplotlib.pyplot as plt
import numpy as np
import os

# Configure matplotlib for clean look and Chinese support
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300

# Categories and count of libraries
categories = [
    "GIS与空间分析\n(OSMnx, Geopandas, Shapely, PyProj...)",
    "Web与地图可视化\n(Streamlit, Pydeck, Folium, Plotly...)",
    "文档分析与接口\n(Requests, PyMuPDF, Pillow, PyYAML...)",
    "大模型、AI与NLP\n(PyTorch, Transformers, Solaris, Jieba...)",
    "数据处理与计算\n(Pandas, NumPy, SciPy, OpenPyXL)",
    "自动化与工程检查\n(Pytest, Ruff, Selenium, Pre-commit)"
]
counts = [9, 6, 6, 5, 4, 4]
colors = ['#4f46e5', '#2563eb', '#0d9488', '#059669', '#d97706', '#dc2626']

fig, ax = plt.subplots(figsize=(10, 5.5), facecolor='white')
ax.set_facecolor('#f8fafc')

y_pos = np.arange(len(categories))
bars = ax.barh(y_pos, counts, color=colors, height=0.55, edgecolor='none', alpha=0.9)

ax.set_yticks(y_pos)
ax.set_yticklabels(categories, fontsize=10, fontweight='bold', color='#1e293b')
ax.invert_yaxis()
ax.set_xlabel('依赖库数量 (个)', fontsize=11, fontweight='bold', color='#1e293b', labelpad=10)
ax.set_title('ultimateDESIGN 平台开源技术栈分布图', fontsize=14, fontweight='bold', color='#0f172a', pad=20)

ax.grid(axis='x', linestyle='--', alpha=0.5, color='#cbd5e1')
ax.set_axisbelow(True)

for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.15, bar.get_y() + bar.get_height()/2, f'{int(width)} 个',
            va='center', ha='left', fontsize=10, fontweight='bold', color='#334155')

ax.set_xlim(0, 11)

for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_visible(False)

plt.tight_layout()

# Save image directly to static/ folder
save_path = os.path.join("static", "libs_distribution_chart.png")
plt.savefig(save_path, bbox_inches='tight', facecolor='white')
print(f"Success: Chart saved at {save_path}")
