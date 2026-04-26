# 项目结构与维护说明

本文档记录当前重构后的目录职责，避免后续开发时把页面、引擎、样式和本地资料混在一起。

## 顶层目录

```text
ultimateDESIGN/
├── app.py
├── pages/
├── src/
├── assets/
├── data/
├── static/
├── tools/
├── tests/
├── docs/
└── .github/
```

## 目录职责

| 路径 | 职责 | 维护规则 |
| --- | --- | --- |
| `app.py` | Streamlit 首页和总入口 | 只放首页级展示、导航和平台状态 |
| `pages/` | Streamlit 业务页面 | 文件名会影响页面路由，非必要不要改名或移动 |
| `src/config/` | 数据路径、配置加载、运行配置 | 新增数据资产时优先在这里登记路径 |
| `src/engines/` | 空间分析、AIGC、RAG、LLM、诊断等业务引擎 | 保持与 UI 分离，避免直接写 Streamlit 展示逻辑 |
| `src/ui/design_system.py` | 页面 Banner、分段标题、摘要卡 | 新增通用布局组件放这里 |
| `src/ui/chart_theme.py` | Plotly 色板和主题 | 新增图表样式放这里，页面不要手写重复主题 |
| `src/ui/ui_components.py` | 顶部导航、引擎状态、兼容导出 | 保留旧导入兼容，新 UI 组件优先放入拆分后的模块 |
| `src/utils/` | 文档生成、服务探活、坐标转换、守护进程管理 | 放跨页面复用的非 UI 工具 |
| `assets/` | CSS、HTML、展示图片 | `style.css` 是全局 UI 样式入口 |
| `data/` | 脱敏表格、GeoJSON、元数据文本 | 原始影像和敏感数据不要提交 |
| `static/` | Streamlit 静态文件服务目录 | 大体积 GeoJSON 放这里前先确认 GitHub 限制 |
| `tools/` | 数据处理、质量检查、启动检查 | 脚本应可从项目根目录运行 |
| `tests/` | 单元测试 | 引擎和工具修改后补对应测试 |
| `docs/` | 本地 PDF、任务书、开题报告和规划资料 | 默认被 `.gitignore` 忽略，不作为公开仓库内容 |
| `.github/` | CI 和 GitHub 协作文件 | 修改 CI 后本地先跑关键命令 |

## UI 层约定

页面结构统一为：

```text
render_top_nav()
render_page_banner(...)
render_summary_cards(...)
render_section_intro(...)
业务控件 / 数据表 / 图表 / 结果区
```

导入约定：

```python
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.chart_theme import apply_plotly_theme, apply_plotly_polar_theme, get_chart_palette
from src.ui.ui_components import render_top_nav, render_engine_status_alert
```

不要在页面里重复定义摘要卡、Banner 或 Plotly 主题。若某个样式会跨页面使用，应沉淀到 `src/ui/` 或 `assets/style.css`。

## 数据路径约定

新增数据文件时，优先在 `src/config/paths.py` 中登记，再由页面或引擎引用。这样页面不会散落硬编码路径。

当前关键路径：

| 配置 | 含义 |
| --- | --- |
| `DATA_DIR` | 数据根目录 |
| `DOCS_DIR` | 本地任务书、开题报告、规划 PDF |
| `META_DIR` | 文本元数据和语义萃取结果 |
| `ASSETS_DIR` | CSS、HTML、图片素材 |
| `STATIC_DIR` | Streamlit 静态文件 |
| `SHP_FILES` | 边界、地块、建筑等 GeoJSON |
| `DATA_FILES` | POI、交通、街景、情绪等表格 |

## GitHub 清理规则

提交前重点确认：

```powershell
git status --short
```

不应提交：

- `.runtime-packages/`
- `.venv/`
- `*.log`
- `*.err`
- `docs/`
- `*.pdf`
- `data/streetview/`
- `data/raw_images/`

## 推荐验证

```powershell
python -m py_compile app.py pages/1_数据底座与规划策略.py pages/2_现状空间全景诊断.py pages/3_AIGC设计推演.py pages/4_LLM博弈决策.py pages/5_更新设计成果展示.py
python -m py_compile src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
python -m pytest tests/ -q
```
