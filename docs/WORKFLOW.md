# 🗺️ UltimateDESIGN 城市更新平台全流程工作流 (Urban Renewal Platform Workflow)

本平台的核心使命是**面向图纸、工程矢量与设计报告的全流程自动化、数字化城市设计决策支持**。
平台专属研发守则、RAG 法规库跨项目永久保留规范与前端层叠对比度安全规范详见根目录 [**`SKILLS.md`**](../SKILLS.md)。
项目现提供 **v7.0 独立 Windows 桌面可执行程序（`UltimateDESIGN.lnk` → `release/win-unpacked/UltimateDESIGN.exe` / `UltimateDESIGN-Setup-7.0.0-x64.exe`，由 [`tools/build_desktop_release.py`](file:///e:/AI-based-project/urban-platform/tools/build_desktop_release.py) 基于 `electron-builder` + `app.asar` 编译，支持高刷与无上限 FPS 解锁）** 与 **Streamlit 网页工作台（[`启动_UltimateDESIGN.bat`](file:///e:/AI-based-project/urban-platform/启动_UltimateDESIGN.bat) / [`app.py`](file:///e:/AI-based-project/urban-platform/app.py) + `pages/01~03_*.py`）** 双轨并存入口，共享底层 `src/core/runtime_adapter.py`、`src/core/spatial_engine_v2.py` 与 29 个 Python 领域引擎，承载完整的 **17 个标准化逻辑阶段 (`00`–`16`)**，实现「GIS 多源向量化空间融合 → 全路网 `rustworkx` 空间句法与 AHP-MPI 诊断 → 多主体博弈与 ControlNet 生形 → 法定导则与 AutoCAD DXF/A3/Word 交付」全链路闭环。

> [!NOTE]
> 📹 **关于视频模块**：视频与动画录制生成相关的模块（`tools/video_generator/`）属于平台研发的**附加拓展功能**，日常制图与报告编译核心工作流并不强制依赖此部分。

---

## 🛠️ 三大核心工作台与 17 阶段路由映射总览

| 工作台物理页面 | URL 路由参数 (`?sub=`) | 承载逻辑阶段 | 核心功能模块 |
|---|---|---|---|
| **总控主页** (`app.py`) | `/` | 全局枢纽 | 算力 HUD、研究范围 3D 底图、AI 吞吐监控、全新项目缓存重置 |
| **工作台 1**：[`01_全息空间诊断与数据沙盘.py`](file:///e:/AI-based-project/urban-platform/pages/01_全息空间诊断与数据沙盘.py) | `?sub=diagnosis` | Stage 04–05 | 3D 现状全息底座、DepthMapX 空间句法与 Momepy 形态测度、AHP-MPI 评估、地块雷达、AI 诊断报告、专项资源分析 |
| **工作台 1**：[`01_全息空间诊断与数据沙盘.py`](file:///e:/AI-based-project/urban-platform/pages/01_全息空间诊断与数据沙盘.py) | `?sub=assets` | Stage 00–03 | 双轨基地自主接入 (GeoJSON/OSM)、16 类数据上传与在线质量体检、MarkItDown 语义萃取、4 方向街景实景巡检 |
| **工作台 1**：[`01_全息空间诊断与数据沙盘.py`](file:///e:/AI-based-project/urban-platform/pages/01_全息空间诊断与数据沙盘.py) | `?sub=datav` | Stage 14 | `sc-datav` 全屏数据态势监控看板与轻量 3D 沙盘双模切换（含移动端响应式布局） |
| **工作台 2**：[`02_多主体博弈与空间AIGC工坊.py`](file:///e:/AI-based-project/urban-platform/pages/02_多主体博弈与空间AIGC工坊.py) | `?sub=strategy` | Stage 06–07 | Stage 06 目标定位与案例对标快捷面板、三方主体多轮博弈协商、RAG 法规合规校验、共识雷达与设计纲要 |
| **工作台 2**：[`02_多主体博弈与空间AIGC工坊.py`](file:///e:/AI-based-project/urban-platform/pages/02_多主体博弈与空间AIGC工坊.py) | `?sub=master_plan` | Stage 08 | 总体空间结构推演、用地结构交互式优化沙盘、概念总平面 AIGC 引导 |
| **工作台 2**：[`02_多主体博弈与空间AIGC工坊.py`](file:///e:/AI-based-project/urban-platform/pages/02_多主体博弈与空间AIGC工坊.py) | `?sub=aigc` | Stage 10 | 重点地段诊断雷达、控规指标反推、微观人群画像、Before/After 街景对比推演 |
| **工作台 2**：[`02_多主体博弈与空间AIGC工坊.py`](file:///e:/AI-based-project/urban-platform/pages/02_多主体博弈与空间AIGC工坊.py) | `?sub=aigc_studio` | Stage 15 | 空间 AIGC 推演工坊（ControlNet 路网/建筑/高度深度约束 + 6 类策略风格 + SD 渲染） |
| **工作台 3**：[`03_数字图则与工程交付枢纽.py`](file:///e:/AI-based-project/urban-platform/pages/03_数字图则与工程交付枢纽.py) | `?sub=delivery` | Stage 13 | Python 空间矢量绘图、A3 图框图册自动组装、AutoCAD 2000 (AC1015/ANSI_936) DXF 导出、Word 设计报告汇编 |
| **工作台 3**：[`03_数字图则与工程交付枢纽.py`](file:///e:/AI-based-project/urban-platform/pages/03_数字图则与工程交付枢纽.py) | `?sub=guideline` | Stage 12 | 9 大章节城市设计法定导则两步法生成、RAG 政策检索、Word 导则导出 |
| **工作台 3**：[`03_数字图则与工程交付枢纽.py`](file:///e:/AI-based-project/urban-platform/pages/03_数字图则与工程交付枢纽.py) | `?sub=systems` | Stage 09 | 交通 TOD / 15 分钟生活圈 / 建筑形态 / 风貌景观四大专项深度策划 |
| **工作台 3**：[`03_数字图则与工程交付枢纽.py`](file:///e:/AI-based-project/urban-platform/pages/03_数字图则与工程交付枢纽.py) | `?sub=timing` | Stage 11 | 全域+重点地块双层实施路径、六类更新模式与三期实施时序规划 |
| **工作台 3**：[`03_数字图则与工程交付枢纽.py`](file:///e:/AI-based-project/urban-platform/pages/03_数字图则与工程交付枢纽.py) | `?sub=skill` | Stage 16 | 制图与设计智能体 Skill 规范手册、A3 图纸在线编译、多主体听证会博弈仿真沙盘 |

---

## 🟢 工作台 1：全息空间诊断与数据沙盘 (`01_全息空间诊断与数据沙盘.py`)

### 1. `?sub=assets` · 多源空间资产、语义萃取与现场调研 (Stage 00–03)
- **双轨制基地自主接入**：支持专业 GIS 矢量上传（GeoJSON / Shapefile / DXF）或在线框选经纬度坐标自动抓取 OpenStreetMap 要素，无缝切换全球任意城市地块；内置一键回退基准示范工程能力。
- **16 类专项数据上传与在线质量体检**：逐项校验边界、建筑、路网、POI、交通、GVI 与街景，采用 WGS-84 全球合法坐标区间与字段完整性校验（无地域硬编码偏置）。
- **MarkItDown 规划文档语义萃取**：支持上传 PDF/Word/PPT 任务书与上位规划文件，自动解析并导出结构化 Markdown 文本存入阶段总线。
- **街景采样点 4 方向实景巡检**：基于 Apple HIG 浅色地图联动预览采样点 `0° / 90° / 180° / 270°` 四向全景实拍。

### 2. `?sub=diagnosis` · 3D 全息底座、空间句法与 AHP-MPI 潜力诊断 (Stage 04–05)
- **3D 现状全息底座 & 空间句法测度**：展示建筑体量、用地底色、POI 热力、GVI 柱体与天际线 HUD；集成 `SpatialSyntaxEngine` 一键测算 DepthMapX 拓扑整合度（Integration/Choice）与 Momepy 建筑覆盖率（BCR）、容积率（FAR）、H/W 高宽比、SVF 及微气候舒适度评级。
- **AHP-MPI 潜力评估与靶向锁定**：动态调节空间潜力、社会需求与环境紧迫度三维权重，支持在线修订候选地块指标并自由锁定任意单元作为全流程更新靶向地块。
- **地块雷达、AI 诊断报告与专项资源分析**：输出多维雷达图、定量痛点清单及文化/产业/人群需求三类专题文本。

### 3. `?sub=datav` · 全屏空间监控大屏 (Stage 14)
- **双模可视化视图**：默认渲染 `sc-datav` 全屏数据态势监控看板（含 ECharts 高度分布、用地占比、POI 实时滚动流与 3D 底座），支持一键切换轻量 3D 交互沙盘，并通过 `is_mobile_client()` 自动适配移动端高度 (`1650px`) 与桌面端 (`880px`)。

---

## 🟣 工作台 2：多主体博弈与空间 AIGC 工坊 (`02_多主体博弈与空间AIGC工坊.py`)

### 1. `?sub=strategy` · 目标定位与多主体协同博弈 (Stage 06–07)
- **Stage 06 目标定位与案例对标快捷面板**：一键生成本地化案例对标分析与全域宏观设计目标报告，打通后续设计门控依赖。
- **三主体多轮博弈与 RAG 合规审计**：模拟居民代表、开发运营商与注册规划师围绕靶向地块展开「陈述 → 交锋 → 妥协」三轮协商，自动检索 `rag_knowledge.json` 政策法规库约束，产出共识度雷达、策略矩阵与结构化《设计纲要》。

### 2. `?sub=master_plan` · 总体空间结构与用地沙盘 (Stage 08)
- **总体空间结构推演**：根据策略矩阵生成宏观空间结构方案。
- **交互式用地优化沙盘**：实时调整各类用地占比滑块并测算生态与活力指标变化。

### 3. `?sub=aigc` · 重点地段深化设计 (Stage 10)
- **微观深化与控规反推**：自动同步候选与靶向地块控规红线（FAR、限高、密度、绿地率），生成目标人群画像、深化设计方案与 Before/After 街景对比。

### 4. `?sub=aigc_studio` · 空间 AIGC 推演工坊 (Stage 15)
- **GIS 刚性约束 ControlNet 渲染**：自动将路网、建筑轮廓、高度深度图与用地语义色块转换为 ControlNet 空间约束条件，结合 6 种更新策略风格与 LLM 英文提示词润色驱动 Stable Diffusion 生成概念总平、街景透视与鸟瞰体块方案。

---

## 🟢 工作台 3：数字图则与工程交付枢纽 (`03_数字图则与工程交付枢纽.py`)

### 1. `?sub=delivery` · 工程图纸、DXF 与全案报告交付 (Stage 13)
- **Python 矢量图纸直出与 A3 图册组装**：调用 `tools/drawings/` 独立绘图模块与 `frame_generator.py` 自动化封装标准 A3 图签、图例、比例尺与设计说明。
- **AutoCAD 2000 (AC1015) 1:1 矢量 DXF 导出**：按国标 5 图层规范 (`01_BOUNDARY` ~ `05_GREEN_SPACE`) 输出米制坐标与 ANSI_936 防乱码编码的 `.dxf` 工程图纸。
- **Word 项目设计报告编译**：支持「轻量管道」与「全流程从零生成管道」，集成 `deai_processor.py` 降 AI 率处理，一键导出完整 `.docx` 报告。

### 2. `?sub=guideline` · 城市设计数字导则 (Stage 12)
- **两步法与 RAG 法规约束**：融合前序各阶段成果与局部控制参数，编制 9 大章节法定城市设计导则并支持 `.docx` 公文导出。

### 3. `?sub=systems` & `?sub=timing` · 专项系统与实施路径 (Stage 09 & Stage 11)
- **四大专项系统设计 (Stage 09)**：交通 TOD、15 分钟生活圈公共空间、建筑形态风貌与历史景观系统深化。
- **双层实施路径 (Stage 11)**：划分六类微更新模式与近期-中期-远期三期实施时序。

### 4. `?sub=skill` · 智能体 Skill 规范手册 (Stage 16)
- **技能规范查阅与交互验证**：在线浏览制图与智能体规范文档，支持 A3 图纸单张在线编译预览及自适应基地多主体听证会冲突仿真。

---

## 📹 [附加功能] 视频生成与动画制作 (Optional Video Generator)

除三大工作台网页交互外，平台在 [**`tools/video_generator/`**](file:///e:/AI-based-project/urban-platform/tools/video_generator) 中保留了可选的大屏汇报视频分镜与动画脚本辅助工具（日常核心制图与报告导出流程不强依赖此目录）。

---

## 🛡️ 架构完整性与 CI 检测规范

- **路径与数据解耦**：空间矢量数据集中于 `data/gis/`，表格数据集中于 `data/csv/`，由 `src/config/paths.py` 中的 `PAGE_ROUTES` 与 `DATA_FILES` / `GIS_FILES` 作为单一真理源统一管理。
- **本地 CI 检测（自动化）**：提交前在根目录执行 `python -m pytest` 跑通全部 **382 个自动化测试用例**（含 `tests/desktop/` 桌面端内核与 FastAPI 7 大领域路由测试），并配合 `tools/check_env.py`、`tools/startup_smoke.py`、`tools/secret_scan.py` 与 `tools/data_quality_check.py` 完成全量体检。
- **环境变量隔离**：敏感凭证严禁硬编码，统一通过本地 `.env` 或系统设置面板配置。
