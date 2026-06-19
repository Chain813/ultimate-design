# 🛠️ UltimateDESIGN Platform Tools Directory (工具箱手册)

本目录包含了项目在前期数据获取、空间分析、图纸自动化渲染、AIGC 排版设计以及成果输出（Word/PPT 编译）全流程中所使用的全部自动化脚本与小工具。

为了方便开发与使用，以下对本目录中的核心脚本按功能模块进行归类与说明。

---

## 📂 目录结构与子文件夹
- [**`drawings/`**](file:///e:/AI-based-project/urban-platform/tools/drawings): 包含具体图纸编号（如 `dr_004.py`, `dr_017.py` 等）的程序化绘制与数据映射渲染规则。
- [**`realesrgan-ncnn-vulkan/`**](file:///e:/AI-based-project/urban-platform/tools/realesrgan-ncnn-vulkan): 基于 Vulkan 接口的 Real-ESRGAN 超分辨率重建本地引擎，用于将低像素图纸超分放大 4 倍。
- [**`video_generator/`**](file:///e:/AI-based-project/urban-platform/tools/video_generator): 包含生成大屏幕演示与三维场景展示视频的录制/自动渲染工具。
- [**`archive/`**](file:///e:/AI-based-project/urban-platform/tools/archive): 存放已经废弃或陈旧的临时性、过渡性脚本。

---

## 🎯 工具脚本功能分类

### 1. 🌐 地理空间数据清洗与准备管线 (GIS Data Processing)
用于从外部原始 GIS 数据到 3D 数字孪生底座所需轻量化数据的清洗与配准：

| 脚本名称 | 功能描述 |
| :--- | :--- |
| [**`process_site_data.py`**](file:///e:/AI-based-project/urban-platform/tools/process_site_data.py) | **一键式核心数据管道**：自动归一化表格列名（中英文大小写映射），按 GeoJSON 范围边界缓冲裁剪要素，利用 Centroid 空间相交（`sjoin`）将建筑轮廓与用地现状关联并绑定 `prop_style` 控制样式（内置 `.buffer(0)` 拓扑修复），自动截断 6 位精度压缩导出并触发质量体检。 |
| [**`data_quality_check.py`**](file:///e:/AI-based-project/urban-platform/tools/data_quality_check.py) | 数据质量自检工具，在数据清洗后运行，对各图层完整性、稳定标识字段、必需属性缺失进行体检，输出诊断报告。 |
| [**`clip_buildings.py`**](file:///e:/AI-based-project/urban-platform/tools/clip_buildings.py) | 依研究范围边界裁剪建筑轮廓矢量 GeoJSON。 |
| [**`crop_scope.py`**](file:///e:/AI-based-project/urban-platform/tools/crop_scope.py) | 自动读取并裁剪研究范围 GeoJSON 的地理边界包络线（bbox）。 |
| [**`fill_missing_landuse.py`**](file:///e:/AI-based-project/urban-platform/tools/fill_missing_landuse.py) | 针对用地现状数据中空白缝隙、未标记字段及重叠部分进行拓扑修复与自动过渡填充。 |
| [**`prepare_landuse.py`**](file:///e:/AI-based-project/urban-platform/tools/prepare_landuse.py) | 规划用地现状的前期清洗与格式规范化配准。 |
| [**`sync_building_landuse.py`**](file:///e:/AI-based-project/urban-platform/tools/sync_building_landuse.py) | 同步校准建筑底面与底层用地利用类型的空间重叠属性。 |
| [**`compress_geojson.py`**](file:///e:/AI-based-project/urban-platform/tools/compress_geojson.py) | 剔除 GeoJSON 中的冗余元数据属性，并将坐标精度截断至小数点后 6 位，极限轻量化以保证 Deck.GL 三维渲染高帧率。 |
| [**`generate_building_shadows.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_building_shadows.py) | 根据建筑层高/绝对高度和设定的太阳入射角，计算并生成现状建筑群的投影阴影多边形。 |
| [**`get_streetview.py`**](file:///e:/AI-based-project/urban-platform/tools/get_streetview.py) | 街景采样点照片抓取脚本，基于道路线点位自动调用接口获取现状街区全景图。 |

---

### 2. 🗺️ 图纸绘制与 Landmark 自适应适配 (Map Rendering)
用于在 2D 绘图及图纸整页拼装中实现对当前配置地块的智能自适应：

| 脚本名称 | 功能描述 |
| :--- | :--- |
| [**`draw_scope_map.py`**](file:///e:/AI-based-project/urban-platform/tools/draw_scope_map.py) | 核心 2D 地图绘图驱动。读取 site 配置，自适应标注关键 Landmark 坐标，并内建多系统（Windows/Linux/macOS）中文字体 Fallback 链保护，彻底防止绘图时出现文字“豆腐块”乱码或崩溃。 |
| [**`add_wind_rose.py`**](file:///e:/AI-based-project/urban-platform/tools/add_wind_rose.py) | 程序化绘制通用的 8 方向精美矢量风玫瑰（指北针），并批量叠加至目标图纸右上角。 |
| [**`add_real_wind_rose.py`**](file:///e:/AI-based-project/urban-platform/tools/add_real_wind_rose.py) | 读取本地实测风玫瑰图片并拼贴至全套图纸的指定地图版面中。 |
| [**`redraw_dr054_atlas_layout.py`**](file:///e:/AI-based-project/urban-platform/tools/redraw_dr054_atlas_layout.py) | 专项重绘排水与竖向网络分析图，修复图层相互遮挡与标签字号重叠。 |
| [**`render_analysis_single_sheets.py`**](file:///e:/AI-based-project/urban-platform/tools/render_analysis_single_sheets.py) | 自动读取渲染成果图，拼装符合图则图签规范的单页 A3 纸张。 |

---

### 3. 🎨 架构图、技术参数图与决策工作流生成 (Diagrams & Flowcharts)
用于自动生成高质量的 Apple HIG/Cyberpunk 风格系统架构图、多主体博弈和技术图表：

| 脚本名称 | 功能描述 |
| :--- | :--- |
| [**`generate_all_diagrams.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_all_diagrams.py) | 一键生成并导出全套技术图表（博弈沙盘决策流、RAG 法规审查流、SD 局部推演架构等）。 |
| [**`generate_architecture_diagrams.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_architecture_diagrams.py) | 自动绘制并导出本平台基于多 Agent 协同（协商代理、评估代理、规划代理）的底层运行架构图。 |
| [**`generate_technical_route.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_technical_route.py) | 绘制导出本系统完整的技术实现路线与数据处理链条大图。 |
| [**`generate_technology_parameters_graph.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_technology_parameters_graph.py) | 自动生成包含本系统各功能模块 AI 模型（DeepSeek/ControlNet 等）输入输出参数映射关系的知识图谱。 |
| [**`generate_workflow_flowchart.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_workflow_flowchart.py) | 绘制导出微更新设计全阶段决策工作流图。 |
| [**`draw_libs_chart.py`**](file:///e:/AI-based-project/urban-platform/tools/draw_libs_chart.py) | 绘制并导出系统所用第三方核心技术栈（Matplotlib, Shapely, Streamlit 等）的技术树对比图表。 |
| [**`codegraph_tool.py`**](file:///e:/AI-based-project/urban-platform/tools/codegraph_tool.py) | 项目代码依赖解析树生成工具，自动扫描 Python 代码中的类与函数并输出相互调用关系拓扑。 |

---

### 4. 📊 规划图册大板、指标雷达图与排版设计 (AIGC & Board Materials)
用于从设计成果（指标、排版、大图）到图册大板和超分辨率重构：

| 脚本名称 | 功能描述 |
| :--- | :--- |
| [**`generate_indicator_images.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_indicator_images.py) | 读取各重点地段指标控制大表，计算并生成可视化多维分析雷达图与柱状对比图。 |
| [**`generate_design_creed_sheets.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_design_creed_sheets.py) | 自动生成高对比度、排版精美的“设计原则与理念”中英文字排海报。 |
| [**`generate_list_diagrams.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_list_diagrams.py) | 生成一系列带序号标签、渐变底色和 Apple 设计规范的列表说明看板插图。 |
| [**`generate_exhibition_board_tiles.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_exhibition_board_tiles.py) | 自动拼装生成规划答辩墙大板（展板分块拼贴效果图）。 |
| [**`generate_urban_analysis_board.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_urban_analysis_board.py) | 绘制生成区域宏观区位分析大板。 |
| [**`generate_urban_rural_planning.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_urban_rural_planning.py) | 绘制生成中国城乡规划规范合规检测对比表。 |
| [**`generate_unified_landscape.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_unified_landscape.py) | 绘制生成多尺度协同景观设计空间导图。 |
| [**`render_exhibition_board_previews.py`**](file:///e:/AI-based-project/urban-platform/tools/render_exhibition_board_previews.py) | 批量拼装、缩放与输出答辩展板的高清效果预览图。 |
| [**`super_resolve_creeds.py`**](file:///e:/AI-based-project/urban-platform/tools/super_resolve_creeds.py) | 调用本地 Real-ESRGAN 可执行文件对 AI 绘制的低分辨率概念总图进行 4 倍高清重建。 |

---

### 5. 📑 图册、PPT幻灯汇报与周志自动编译 (Report & Slide Compilation)
用于项目最终产出的排版与编译发布：

| 脚本名称 | 功能描述 |
| :--- | :--- |
| [**`generate_pptx_slides.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_pptx_slides.py) | **幻灯片自动编译**：读取大屏数据与图表，以统一的主题和转场动画一键生成答辩汇报 `.pptx` 幻灯片文件。 |
| [**`generate_atlas_crops.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_atlas_crops.py) | 生成多比例尺图册的局部细节对比图。 |
| [**`generate_atlas_sheets.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_atlas_sheets.py) | 批量生成 A3 规范成果图册。 |
| [**`generate_atlas_ppt.py`**](file:///e:/AI-based-project/urban-platform/tools/generate_atlas_ppt.py) | 将全套 A3 图册拼贴并生成演示 PPT 脑图结构。 |
| [**`rearrange_tables_landscape.py`**](file:///e:/AI-based-project/urban-platform/tools/rearrange_tables_landscape.py) | 将超宽的规划控制指标大表（Word 导出时）自动调整为竖排自适应换行，防止内容溢出边界。 |
| [**`replace_weekly_figures_v4.py`**](file:///e:/AI-based-project/urban-platform/tools/replace_weekly_figures_v4.py) | 毕设周志插图替换神器，自动通过 Word 接口将图纸按双图并排自适应插入目标位置并清理冗余行。 |
| [**`restore_atlas_images.py`**](file:///e:/AI-based-project/urban-platform/tools/restore_atlas_images.py) | 一键式批量找回丢失或损毁的原始图册缓存图纸并安全防误覆盖。 |
| [**`restore_static_sheets.py`**](file:///e:/AI-based-project/urban-platform/tools/restore_static_sheets.py) | 针对不需程序化生成的总体鸟瞰效果图图纸进行静态恢复替换。 |

---

### 6. 🛡️ 知识库、系统测试与安全扫描 (QA, Test & RAG)
用于系统维护、数据索引和质量保障：

| 脚本名称 | 功能描述 |
| :--- | :--- |
| [**`rebuild_rag.py`**](file:///e:/AI-based-project/urban-platform/tools/rebuild_rag.py) | 政策法规 RAG 数据库一键式重新构建、文本分块以及矢量检索索引的本地更新生成。 |
| [**`enhance_reference_exact_analysis.py`**](file:///e:/AI-based-project/urban-platform/tools/enhance_reference_exact_analysis.py) | 优化本地 RAG 检索的权重和关联召回匹配精度。 |
| [**`check_env.py`**](file:///e:/AI-based-project/urban-platform/tools/check_env.py) | 检测本地的 Python 版本、GDAL/Fiona/GeoPandas 依赖冲突以及硬件环境。 |
| [**`secret_scan.py`**](file:///e:/AI-based-project/urban-platform/tools/secret_scan.py) | 安全防泄漏扫描工具，确保代码和配置文件中没有硬编码泄露 API Key、Token 密码等敏感词。 |
| [**`startup_smoke.py`**](file:///e:/AI-based-project/urban-platform/tools/startup_smoke.py) | Streamlit 启动冒烟测试校验，确保各页面基本导入、服务响应正常。 |
