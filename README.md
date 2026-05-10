[**English**](./README_EN.md) · [**简体中文**](./README.md)

<div align="center">

# UltimateDESIGN

**数字孪生 · 古今共振 —— AI 赋能下的城市微更新规划设计决策支持平台**

*长春伪满皇宫周边街区 · 150 公顷 · 15 模块 · 41 张专业图纸 · 端到端循证工作流*

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/Tests-167%20passed-brightgreen?logo=pytest)](./tests/)
[![License](https://img.shields.io/badge/License-Academic-orange)]()

</div>

---

## 项目概况

UltimateDESIGN 是面向城乡规划专业毕业设计与城市设计课程的 **Streamlit 全栈决策支持平台**。项目以长春伪满皇宫周边 150 公顷街区为实证对象，将城市设计拆解为 15 个标准化阶段（数据准备 → 现状诊断 → 概念策略 → 设计深化 → 视频汇报），打通「GIS 数据采集 → LLM 循证推演 → AIGC 标准制图 → 视频答辩生成」的完整闭环。

---

## 核心亮点

| 能力 | 说明 |
|---|---|
| **15 阶段循证工作流** | 从数据准备到视频汇报，每个阶段独立封装数据面板、AI 推演与答辩图表 |
| **41 张专业图纸模板** | 基于 SD + ControlNet，自动注入空间资产生成符合规划规范的图纸 |
| **GIS → AIGC 空间对齐** | 首创「矢量→光栅→ControlNet」管线，消除 AI 制图的空间幻觉 |
| **三主体博弈推演** | LLM 驱动居民 / 开发商 / 规划师角色对抗，输出共识度雷达与策略矩阵 |
| **双重质量闭环** | Gemma 视觉 + DeepSeek 内容双评估，C/D 级图纸自动修正重生成 |
| **版本化图册导出** | `VersionStore` 全版本回溯 + `BatchExporter` 一键导出 70+ 张图册 |
| **HyperFrames 视频** | 一键生成 ~9 分钟答辩汇报视频，含 3D 分层展示与 GSAP 动画 |
| **167 项自动化测试** | Pytest 全覆盖 + CI 集成 lint / 密钥扫描 / 冒烟测试 / 数据质量检查 |

---

## 快速启动

### 1. 环境安装

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

### 2. 启动平台

```powershell
# 方式 A：双击 run.bat（自动检测端口并打开浏览器）
# 方式 B：命令行
streamlit run app.py
```

平台默认运行于 `http://localhost:8501`，通过**顶部导航栏**按 `[00]` ~ `[14]` 顺序浏览。

### 3. 健康自检

```powershell
python -m pytest                    # 167 项单元测试
python tools/check_env.py           # 15 页面完整性校验
python tools/data_quality_check.py  # 数据质量评级
python tools/secret_scan.py         # 敏感信息扫描
```

---

## 算力挂载

平台在纯 CPU 模式下即可运行全部分析功能。如需激活 AIGC 制图与 LLM 推演，请挂载以下引擎：

### LLM 引擎（DeepSeek / Ollama）

```env
# .env
DEEPSEEK_API_KEY="<your-api-key>"
```

系统自动读取环境变量，首页 HUD 面板将显示「已联机」。云端模式零显存消耗。

### 视觉渲染引擎（Stable Diffusion WebUI）

1. 启动本地 SD WebUI，启动参数需包含 `--api --listen`：
   ```bat
   set COMMANDLINE_ARGS=--api --listen --xformers
   ```
2. 确保运行于 `127.0.0.1:7860`，平台将自动检测连接状态。

### GIS 资产预渲染

将矢量 GeoJSON 光栅化为 ControlNet 引导图（路网骨架 / 用地分区 / 卫星底图）：

```powershell
python scripts/render_gis_assets.py
```

生成资产位于 `static/assets/generated_base/`，用于 AIGC 管线的空间约束输入。

---

## 数据资产

系统实现了**数据与逻辑的彻底解耦**。迁移到新地块只需替换 `data/` 目录，核心代码无需修改。

### 数据目录结构

```text
data/
├── shp/
│   ├── Boundary_Scope.geojson           # 研究范围红线 (必须)
│   ├── Building_Footprints.geojson      # 建筑基底 (含 Floor 字段)
│   ├── Key_Plots_District.json          # 5 个重点更新地块边界
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

### 自动化数据获取

```powershell
python scripts/fetch_real_estate_data.py          # 建筑年代 / 房价
python scripts/fetch_supplementary_data.py --all  # 日照 / 交通等
python scripts/clip_city_data.py                  # 裁切城市级数据至研究范围
python scripts/render_gis_assets.py               # 矢量光栅化 (AIGC 底稿)
```

---

## 工作流阶段

系统将城市设计过程拆解为三大阶段，每个阶段的输出自动流转至下游：

### 前期：现状诊断（Stage 00-05）

| 阶段 | 页面 | 核心能力 |
|---|---|---|
| 00 | 数据准备 | 16 类数据上传、质量检查、坐标同步 |
| 01 | 任务解读 | 任务书解析、红线限制提取、区位图提示词 |
| 02 | 资料收集 | 语义提取引擎、资产完整度评估 |
| 03 | 现场调研 | 街景样本库、四方向全景检索 |
| 04 | 现状分析 | WebGL 3D 建筑底座、POI 聚合、天际线、光照推演 |
| 05 | 问题诊断 | AHP-MPI 更新潜力排行、地块诊断雷达图 |

### 中期：策略推演（Stage 06-07）

| 阶段 | 页面 | 核心能力 |
|---|---|---|
| 06 | 目标定位 | LLM 案例对标（新天地 / 国王十字等）、愿景提取 |
| 07 | 设计策略 | 三主体博弈推演、共识度雷达、策略落地矩阵 |

### 后期：设计深化与交付（Stage 08-14）

| 阶段 | 页面 | 核心能力 |
|---|---|---|
| 08 | 总体城市设计 | AIGC 总平面图、ControlNet 空间对齐 |
| 09 | 专项系统设计 | 交通 / 公共空间 / 风貌 / 文化四大专项 |
| 10 | 重点地段深化 | 5 地块 Before/After 推演、高精度效果图 |
| 11 | 实施路径 | 六种更新模式、三期时序甘特图 |
| 12 | 城市设计导则 | 两步法导则生成、RAG 政策检索、控制图则 |
| 13 | 成果表达 | 41 图纸总览、学术终评报告、图册批量导出 |
| 14 | 视频生成 | HyperFrames 答辩视频（14 段落 / ~9 分钟） |

---

## 项目结构

```text
ultimateDESIGN/
├── app.py                              # 平台入口 / 首页 / 全局地图基底
├── pages/                              # 15 个阶段页面 (00 ~ 14)
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
│   │   ├── quality_assessor.py         #   双重质量评估 (Gemma + DeepSeek)
│   │   ├── version_store.py            #   版本持久化 (PNG + JSON)
│   │   ├── batch_exporter.py           #   图册级批量导出
│   │   ├── spatial_engine.py           #   GIS 解析 / MPI 测度 / 天际线
│   │   ├── guideline_prompt.py         #   导则生成 + RAG 检索
│   │   ├── rag_engine.py              #   RAG 向量检索引擎
│   │   ├── nlp_engine.py              #   NLP 文本分析
│   │   ├── site_diagnostic_engine.py  #   场地诊断引擎
│   │   └── social_media_crawler.py    #   社交媒体舆情采集
│   ├── ui/                             # Streamlit UI 组件
│   │   ├── app_shell.py               #   全局外壳 / 导航 / 布局
│   │   ├── design_system.py           #   原子设计系统
│   │   ├── chart_theme.py             #   Plotly 图表配色
│   │   ├── drawing_prompt_ui.py       #   AIGC 制图交互面板
│   │   ├── module_summary.py          #   阶段答辩小结生成器
│   │   └── output_flow_panel.py       #   成果导出面板
│   ├── utils/                          # 通用工具
│   │   ├── daemon_manager.py          #   算力守护进程管理
│   │   ├── geo_transform.py           #   坐标系转换 (GCJ-02/BD-09/WGS-84)
│   │   ├── service_check.py           #   引擎连接检测
│   │   └── document_generator.py      #   文档导出
│   └── workflow/                       # 工作流引擎
│       ├── city_design_workflow.py    #   14 阶段状态机
│       ├── stage_data_bus.py          #   跨阶段数据总线
│       ├── stage_keys.py             #   总线键名常量
│       └── template_assets.py        #   固定制图资产管理
├── scripts/                            # 自动化脚本
│   ├── setup_env.bat                  #   环境自动安装 (Windows)
│   ├── clip_city_data.py              #   城市级数据裁切至研究范围
│   ├── render_gis_assets.py           #   GIS 矢量光栅化 (AIGC 底稿)
│   ├── run_drawing_export.py          #   高精度图纸批量导出
│   ├── fetch_supplementary_data.py    #   补充数据获取
│   ├── fetch_real_estate_data.py      #   房产数据获取
│   ├── convert_gcj02_to_wgs84.py     #   坐标系批量转换
│   └── generate_video_data.py        #   视频配置数据生成
├── tools/                              # DevOps 工具链
│   ├── check_env.py                   #   环境与页面完整性校验
│   ├── data_quality_check.py          #   数据质量评级 (A/B/C/D)
│   ├── secret_scan.py                 #   敏感信息扫描
│   ├── startup_smoke.py              #   启动冒烟测试
│   └── video_generator/              #   HyperFrames 视频工具 (Node.js)
├── tests/                              # 24 个测试模块 / 167 项用例
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

## 技术架构

### AIGC 制图管线

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
       ├── 提示词构建 (41 模板)          生成专业图纸
       ├── 质量评估 (A/B/C/D)           (地理空间对齐)
       ├── 自动修正 & 重生成
       └── VersionStore 版本归档
```

### 性能优化

- **`@st.cache_data`**：空间数据 I/O 与高频计算的内存级缓存
- **`@st.fragment`**：地图组件局部重绘，避免全页刷新
- **流式 LLM**：多主体博弈与案例推演采用 Streaming 异步处理

---

## 代码托管

### 预提交检查

```powershell
python -m pytest                # 单元测试
python tools/secret_scan.py     # 密钥扫描
```

### 提交规范

遵循 **Conventional Commits**：

```powershell
git add .
git commit -m "feat(aigc): 实现 GIS-to-AIGC 空间对齐管线"
git push origin main
```

### CI/CD

推送至 `main` 后自动触发 GitHub Actions：Lint → 密钥扫描 → 单元测试 → 冒烟测试 → 数据质量检查。

---

## 相关文档

| 文档 | 说明 |
|---|---|
| [BUG_REPORT.md](./BUG_REPORT.md) | 已识别问题与修复日志 |
| [PROJECT_INSPECTION_REPORT.md](./PROJECT_INSPECTION_REPORT.md) | 系统级架构体检报告 |
| [GLOSSARY.md](./GLOSSARY.md) | 核心术语释义 (MPI / GVI / ControlNet 等) |
| [README_EN.md](./README_EN.md) | English Documentation |

---

<div align="center">
<sub>Built with Streamlit · Stable Diffusion · DeepSeek · GeoPandas · Plotly · HyperFrames</sub>
</div>
