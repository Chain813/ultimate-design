[**English**](./README_EN.md) · [**简体中文**](./README.md)

<div align="center">

# UltimateDESIGN

**AI 赋能下的城市设计与微更新规划决策支持平台**

*Streamlit 全栈引擎 · 数据与逻辑解耦 · 15 交互页面 · AIGC 空间对齐制图管线 · 端到端循证工作流*

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/Tests-CI%20suite-brightgreen?logo=pytest)](./tests/)
[![License](https://img.shields.io/badge/License-Academic-orange)]()

</div>

---

## 🌟 项目概况

UltimateDESIGN 是面向城乡规划与城市设计的 **Streamlit 全栈智慧决策支持平台**。平台通过**数据与逻辑的彻底解耦**设计，支持导入任意城市的规划地块（自带长春伪满皇宫周边 170.2 公顷街区作为验证与实证案例）。它将城市更新设计拆解为 16 个标准化阶段（从数据准备、现状诊断、博弈策略推演，到总体与专项深化设计、导则生成，再到 AIGC 意向推演与智能体技能手册），打通「GIS 数据采集 → LLM 循证推演 → 矢量/光栅图纸绘制 → AIGC 意向重绘 → 智能化交付与图则」的完整数字孪生工作流。

---

## ✨ 核心亮点

| 能力 | 说明 |
|---|---|
| **15 页面精简工作流** | 包含主入口 app.py 及 14 个功能页面（其中 3 组页面合并），聚焦核心设计流程 |
| **专业图纸模板与多版式图册** | 基于 Python 空间矢量绘图、PIL 图框封装与多版式排版引擎，高精度生成符合国标与工程规范的 A3 图册 |
| **动态重点更新单元** | 从 `Key_Plots_District.json` / GeoJSON 当前记录读取 N 个重点地块，自动展开图纸目录、诊断卡片与深化提示词 |
| **内置 GIS 处理管线** | `scripts/process_key_plots.py` 支持重点地块清洗、拓扑修复、边界裁切、面积测算和 WGS84 GeoJSON 输出 |
| **GIS → AIGC 空间对齐** | 首创「矢量→光栅→ControlNet」管线，消除 AI 制图的空间幻觉 |
| **DesignContext 设计纲要** | 统一提取 19 个阶段 AI 文本输出，LLM 合成结构化设计纲要，驱动图纸生产 |
| **策略驱动 AIGC 渲染** | 6 种设计策略风格（历史保护/微更新/功能置换/TOD/生态/文创）自动匹配渲染参数 |
| **三主体博弈推演** | LLM 驱动居民 / 开发商 / 规划师角色对抗，输出共识度雷达与策略矩阵 |
| **双重质量闭环** | Gemma 视觉 + DeepSeek 内容双评估，C/D 级图纸自动修正重生成 |
| **后台缓存预加载** | daemon 线程静默预热 37MB GeoJSON、RAG 模型等，页面切换秒开 |
| **引擎懒加载** | `__getattr__` 模式延迟加载 pandas/numpy/PIL，启动速度提升 |
| **录屏自动滑动组件** | 页面右下角常驻防穿帮录屏控制器，支持帧率级平滑像素滚动与快捷键交互 |
| **CI 自动化测试套件** | Pytest 全覆盖 + CI 集成 lint / 密钥扫描 / 冒烟测试 / 数据质量检查 |

---

## 🧩 核心功能模块详解

### 1. 🎨 GIS-to-AIGC 空间对齐与制图管线 (Spatial Alignment & Mapping Pipeline)
这是本平台首创的**“矢量→光栅→ControlNet”**端到端制图管线，彻底消除了生成式 AI 在规划制图中的“空间幻觉”。
* **空间控制原件渲染**：通过 `scripts/render_gis_assets.py` 读取研究范围内的 GeoJSON 矢量图层，自动渲染为黑白二值化的路网骨架（用于 Canny 边缘检测）、彩色用地分区（用于语义 Seg 分割）及建筑轮廓深度图（Depth）。
* **端到端编排管线**：`DrawingPipeline` 负责全流程的管理调度。首先利用大语言模型（LLM）根据图纸模板要求生成最贴合的专业英文 Prompts，然后将其与光栅化的 GIS 图像一同送入 Stable Diffusion 渲染引擎。
* **双重质量闭环评估**：图纸生成后，系统调用 `Gemma` 视觉大模型评估图纸图像质量，结合 `DeepSeek` 进行文本内容审查，综合评定为 A/B/C/D 四个级别。评级为 C/D 的图纸将被拦截并自动优化提示词参数发起重绘，确保最终产出百分之百符合工程绘图规范。

### 2. 🤝 多主体决策博弈推演系统 (Multi-Agent Negotiation System)
系统模拟城市微更新过程中的多方利益交涉，将传统的静态规划升级为“三角色循环博弈模式”。
* **博弈闭环机制**：在 Stage 07 中，系统启动多 Agent 循环，分别模拟**居民（诉求生活品质与补偿）**、**开发商（诉求商业盈利与容积率）**与**规划师（诉求合规性与公共利益）**。三方围绕特定更新议题进行“Statement（立场陈述）→ Rebuttal（论点反驳）→ Compromise（妥协折中）”三轮博弈谈判。
* **RAG 政策法规约束**：在协商中，系统自动调用 `rag_engine.py` 检索本地 `rag_knowledge.json` 政策法规库（包括历史风貌保护红线、限高控制、海绵城市规范等），对角色的立场进行合规性实时干预和审核。
* **利益共识量化**：最终根据三方的发言态度和利益让步，实时渲染生成**三角色动态共识雷达图**并归纳为“问题-目标-策略”的利益平衡矩阵，作为最终规划文本的制定基础。

### 3. 📊 数据-逻辑分离与 MPI/GVI 循证诊断系统 (Evidence-Based Assessment System)
本系统遵循现代软件工程规范，实现了“空间数据与分析逻辑的彻底解耦”。
* **多维指标融合诊断**：通过动态层次分析法（AHP）与更新潜力模型（MPI），将 GVI（街景绿视率）、SVF（天空可视率）、POI 商业活力指数与社交媒体舆情（NLP 情感分析得分）有机叠合，为每个重点更新单元出具全方位的“诊断报告”。
* **动态重点更新单元**：`KeyPlotEngine` 从重点地块 GeoJSON 中读取当前记录数，不再假设固定 5 个地块；Stage 10、Stage 13、提示词模板和图册目录都会按 N 个地块动态展开。
* **内置空间处理脚本**：`scripts/process_key_plots.py` 对原始重点地块边界执行拓扑修复、研究范围裁切、投影面积测算、字段归一和 WGS84 GeoJSON 输出，保证上传数据可直接进入诊断与制图链路。
* **一键跨城市迁移**：当需要将平台应用到全新的地块时，用户无需修改任何前端界面或分析逻辑代码，只需按照 `data/` 目录规范替换 GeoJSON 矢量文件和相关的 CSV 指标数据。系统在启动时会自动读取并刷新 3D 数字孪生底座及各阶段的分析表单，实现极低成本的平台复用与业务拓展。

---

## 🚀 快速启动

### 📦 1. 环境安装

```powershell
git clone https://github.com/Chain813/ultimate-design.git
cd ultimate-design

# 方式 A：自动化脚本（Windows 推荐）
.\scripts\setup_env.bat

# 方式 B：手动安装
conda create -n gis_ai python=3.12 -y
conda activate gis_ai
pip install -r requirements.txt
```

### ▶️ 2. 启动平台

```powershell
# 方式 A：双击 run.bat（自动检测端口并打开浏览器）
# 方式 B：命令行
streamlit run app.py
```

平台默认运行于 `http://localhost:8501`，通过**顶部导航栏**按前期/中期/后期及大屏展示浏览 15 个页面（包含主入口 app.py 及 14 个功能页面）。

### 🩺 3. 健康自检

```powershell
python -m pytest                    # 全量单元测试
python tools/check_env.py           # 15 页面完整性校验
python tools/data_quality_check.py  # 数据质量评级
python tools/secret_scan.py         # 敏感信息扫描
```

---

## 🖥️ 算力挂载

平台在纯 CPU 模式下即可运行全部分析功能。如需激活 AIGC 制图与 LLM 推演，请挂载以下引擎：

### 🧠 LLM 引擎（DeepSeek / Ollama）

```env
# .env
DEEPSEEK_API_KEY="<your-api-key>"
```

系统自动读取环境变量，首页 HUD 面板将显示「已联机」。云端模式零显存消耗。

### 🎨 视觉渲染引擎（Stable Diffusion WebUI）

1. 启动本地 SD WebUI，启动参数需包含 `--api --listen`：
   ```bat
   set COMMANDLINE_ARGS=--api --listen --xformers
   ```
2. 确保运行于 `127.0.0.1:7860`，平台将自动检测连接状态。

### 🗺️ GIS 资产预渲染

将矢量 GeoJSON 光栅化为 ControlNet 引导图（路网骨架 / 用地分区 / 卫星底图）：

```powershell
python scripts/render_gis_assets.py
```

生成资产位于 `static/assets/generated_base/`，用于 AIGC 管线的空间约束输入。

---

## 🗂️ 数据资产

系统实现了**数据与逻辑的彻底解耦**。迁移到新地块只需替换 `data/` 目录，核心代码无需修改。

### 📂 数据目录结构

```text
data/
├── shp/
│   ├── Boundary_Scope.geojson           # 研究范围红线 (必须)
│   ├── Building_Footprints.geojson      # 建筑基底 (含 Floor 字段)
│   ├── Key_Plots_District.json          # N 个重点更新单元边界（由当前 GeoJSON 动态读取）
│   ├── landuse_clipped.geojson          # 裁切后的用地分类 (含国标 RGB 色值)
│   ├── road_network_clipped.geojson     # 裁切后的三级道路网络
│   └── rail_network_clipped.geojson     # 裁切后的轨道交通网络
├── streetview/                          # 街景调研照片 (458 点 × 4 方向)
├── Changchun_POI_Real.csv               # POI 兴趣点 (Name, Lat, Lng)
├── Changchun_Traffic_Real.csv           # 交通设施 (Name, Type, Lat, Lng)
├── CV_NLP_RawData.csv                   # 社交媒体舆情原始数据
├── GVI_Results_Analysis.csv             # 街景绿视率指标
├── Building_Years.csv                   # 建筑年代 (可选)
├── House_Prices.csv                     # 房价数据 (可选)
├── Traffic_Flow.csv                     # 交通流量 (可选)
└── rag_knowledge.json                   # RAG 政策法规知识库
```

### 🤖 自动化数据获取

```powershell
python scripts/fetch_real_estate_data.py          # 建筑年代 / 房价
python scripts/fetch_supplementary_data.py --all  # 日照 / 交通等
python scripts/clip_city_data.py                  # 裁切城市级数据至研究范围
python scripts/process_key_plots.py --input data/raw/key_plots.geojson --boundary data/shp/Boundary_Scope.geojson --output data/shp/Key_Plots_District.json
python scripts/render_gis_assets.py               # 矢量光栅化 (AIGC 底稿)
```

---

## 🔄 工作流阶段

系统将城市设计过程拆解为三大阶段，每个阶段的输出自动流转至下游：

### 🟢 前期：现状诊断（Stage 00-05）

| 阶段 | 页面 | 核心能力 |
|---|---|---|
| 00 | 数据准备 | 16 类数据上传、质量检查、坐标同步 |
| 01 | 任务解读 | 任务书解析、红线限制提取、区位图提示词 |
| 02 | 资料收集 | 语义提取引擎、资产完整度评估 |
| 03 | 现场调研 | 街景样本库、四方向全景检索 |
| 04 | 现状分析 | WebGL 3D 建筑底座、POI 聚合、天际线、光照推演 |
| 05 | 问题诊断 | AHP-MPI 更新潜力排行、地块诊断雷达图 |

### 🟡 中期：策略推演（Stage 06-07）

| 阶段 | 页面 | 核心能力 |
|---|---|---|
| 06 | 目标定位 | LLM 案例对标（新天地 / 国王十字等）、愿景提取 |
| 07 | 设计策略 | 三主体博弈推演、共识度雷达、策略落地矩阵 |

### 🔴 后期：设计深化与交付（Stage 08-13）

| 阶段 | 页面 | 核心能力 |
|---|---|---|
| 08 | 总体城市设计 | 空间结构推演、用地优化沙盘、AIGC 总平面图 |
| 09 | 专项系统设计 | 交通TOD / 15分钟生活圈 / 天际线控制 / 风貌景观四大专项深度策划 |
| 10 | 重点地段深化 | 诊断雷达图、控规指标反推、微观人群画像、地块深化方案 |
| 11 | 实施路径 | 六种更新模式、三期时序甘特图 |
| 12 | 城市设计导则 | 两步法导则生成、RAG 政策检索、控制图则 |
| 13 | 成果表达 | Python 空间底图渲染、Web LLM 重绘提示词、六类 A3 版式选择、PIL 自动图框封装 |
| 14 | 数据大屏 | 三维宏观决策大屏、规划指标统计看板、时空演化动态可视化 |

### 🟣 深化与集成：AIGC 与智能体技能（Stage 15-16）

| 阶段 | 页面 | 核心能力 |
|---|---|---|
| 15 | AIGC设计推演 | 3D意向生成、控制网精细渲染、Before/After 对比 |
| 16 | 制图与设计智能体Skill手册 | 规划绘图技能元指令定义、Skill 动态调试与手册导出 |

---

## 🏗️ 项目结构

```text
ultimateDESIGN/
├── app.py                              # 平台入口 / 首页 / 全局地图基底 (1 个页面)
├── pages/                              # 14 个功能页面 (00 ~ 16)
├── src/                                # 核心领域代码
│   ├── config/                         # 配置加载 / 路径注册 / 运行时常量
│   │   ├── loader.py                   #   YAML 配置解析
│   │   ├── paths.py                    #   全局路径注册中心
│   │   └── runtime.py                  #   运行时标志位
│   ├── data/                           # 数据类别定义
│   ├── engines/                        # 计算 / AI / AIGC 引擎 (严禁 UI 代码)
│   │   ├── llm_engine.py               #   DeepSeek / Ollama 统一接口
│   │   ├── stable_diffusion_engine.py  #   SDPipeline (txt2img / img2img / ControlNet)
│   │   ├── drawing_pipeline.py         #   DrawingPipeline 端到端编排器
│   │   ├── drawing_prompt_engine.py    #   41 图纸提示词构建器
│   │   ├── drawing_prompt_templates.py #   图纸模板元数据库
│   │   ├── drawing_layout_engine.py    #   A3 图纸多版式排版引擎
│   │   ├── frame_generator.py          #   A3 图框图纸组装引擎
│   │   ├── key_plot_engine.py          #   动态重点更新单元读取 / 诊断 / 图纸目录
│   │   ├── urban_image_segmentation.py #   街景图像分割引擎
│   │   ├── engine_registry.py          #   AI/AIGC 引擎注册表
│   │   ├── quality_assessor.py         #   双重质量评估 (Gemma + DeepSeek)
│   │   ├── version_store.py            #   版本持久化 (PNG + JSON)
│   │   ├── batch_exporter.py           #   图册级批量导出
│   │   ├── spatial_engine.py           #   GIS 解析 / MPI 测度 / 天际线
│   │   ├── guideline_prompt.py         #   导则生成 + RAG 检索
│   │   ├── rag_engine.py              #   RAG 向量检索引擎
│   │   ├── nlp_engine.py              #   NLP 文本分析
│   │   └── site_diagnostic_engine.py  #   场地诊断引擎
│   ├── ui/                             # Streamlit UI 组件
│   │   ├── app_shell.py               #   全局外壳 /导航 / 布局
│   │   ├── design_system.py           #   原子设计系统
│   │   ├── chart_theme.py             #   Plotly 图表配色
│   │   ├── drawing_prompt_ui.py       #   AIGC 制图交互面板
│   │   ├── module_summary.py          #   阶段答辩小结生成器
│   │   └── output_flow_panel.py       #   成果导出面板
│   ├── utils/                          # 通用工具
│   │   ├── geo_transform.py           #   坐标系转换 (GCJ-02/BD-09/WGS-84)
│   │   ├── service_check.py           #   引擎连接检测
│   │   └── document_generator.py      #   文档导出
│   └── workflow/                       # 工作流引擎
│       ├── city_design_workflow.py    #   17 阶段状态机
│       ├── stage_data_bus.py          #   跨阶段数据总线
│       ├── stage_keys.py             #   总线键名常量
│       └── template_assets.py        #   固定制图资产管理
├── scripts/                            # 自动化脚本
│   ├── setup_env.bat                  #   环境自动安装 (Windows)
│   ├── clip_city_data.py              #   城市级数据裁切至研究范围
│   ├── process_key_plots.py           #   重点地块拓扑修复 / 边界裁切 / 面积测算
│   ├── render_gis_assets.py           #   GIS 矢量光栅化 (AIGC 底稿)
│   ├── run_drawing_export.py          #   高精度图纸批量导出
│   ├── fetch_supplementary_data.py    #   补充数据获取
│   ├── fetch_real_estate_data.py      #   房产数据获取
│   ├── fetch_social_sentiment.py      #   社交媒体舆情采集
│   ├── convert_gcj02_to_wgs84.py     #   坐标系批量转换
│   └── generate_video_data.py        #   视频配置数据生成
├── tools/                              # DevOps 工具链
│   ├── drawings/                      #   A3 规划图册独立绘制模块 (dr_004.py ~ dr_slow_traffic.py)
│   ├── check_env.py                   #   环境与页面完整性校验
│   ├── data_quality_check.py          #   数据质量评级 (A/B/C/D)
│   ├── secret_scan.py                 #   敏感信息扫描
│   ├── startup_smoke.py              #   启动冒烟测试
│   └── video_generator/              #   HyperFrames 视频工具 (Node.js)
├── tests/                              # Pytest 自动化测试套件
├── data/                               # 数据资产 (数据与逻辑解耦)
├── static/                             # Streamlit 静态资源代理
├── assets/                             # CSS 样式 / WebGL 模板
├── config/                             # config.yaml 运行时配置
├── output/                             # AIGC 图纸输出与版本归档
├── run.bat                             # 一键启动脚本
├── requirements.txt                    # Python 依赖
└── .github/workflows/ci.yml           # CI 流水线
```

---

## ⚙️ 技术架构

### 🎨 AIGC 制图管线

```
GeoJSON 矢量数据                     Stable Diffusion WebUI
       │                                      ▲
       ▼                                      │
  render_gis_assets.py              ┌──────────┴──────────┐
  (矢量光栅化)                       │   ControlNet 约束    │
       │                            │  • Canny (路网骨架)   │
       ├── road_guidance.png ──────▶│  • Seg (用地分区)    │
       ├── landuse_seg.png ────────▶│                      │
       └── satellite.png ─────────▶│  • Tile (色彩参考)   │
                                    └──────────┬──────────┘
  DrawingPipeline 编排                          │
       │                                       ▼
       ├── 提示词构建 (41 模板 + 版式约束) 生成专业图纸
       ├── 质量评估 (A/B/C/D)           (地理空间对齐)
       ├── 自动修正 & 重生成
       └── VersionStore 版本归档
```

### ⚡ 性能优化

- **`@st.cache_data`**：空间数据 I/O 与高频计算的内存级缓存
- **`@st.fragment`**：地图组件局部重绘，避免全页刷新
- **流式 LLM**：多主体博弈与案例推演采用 Streaming 异步处理

---

## ☁️ 代码托管

### 🛡️ 预提交检查

```powershell
python -m pytest                # 单元测试
python tools/secret_scan.py     # 密钥扫描
```

### 📝 提交规范

遵循 **Conventional Commits**：

```powershell
git add .
git commit -m "feat(aigc): 实现 GIS-to-AIGC 空间对齐管线"
git push origin main
```

### 🔄 CI/CD

推送至 `main` 后自动触发 GitHub Actions：Lint → 密钥扫描 → 单元测试 → 冒烟测试 → 数据质量检查。

---

## 📚 相关文档

| 文档 | 说明 |
|---|---|
| [BUG_REPORT.md](./BUG_REPORT.md) | 已识别问题与修复日志 |
| [PROJECT_INSPECTION_REPORT.md](./PROJECT_INSPECTION_REPORT.md) | 系统级架构体检报告 |
| [GLOSSARY.md](./GLOSSARY.md) | 核心术语释义 (MPI / GVI / ControlNet 等) |
| [docs/DYNAMIC_KEY_PLOTS_AND_LAYOUTS.md](./docs/DYNAMIC_KEY_PLOTS_AND_LAYOUTS.md) | 动态重点地块、GIS 处理脚本与多版式图纸生成说明 |
| [README_EN.md](./README_EN.md) | English Documentation |

---

<div align="center">
<sub>Built with Streamlit · Stable Diffusion · DeepSeek · GeoPandas · Plotly · HyperFrames</sub>
</div>
