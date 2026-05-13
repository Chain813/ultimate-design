[**English**](./README_EN.md) · [**简体中文**](./README.md)

---

# 核心术语库 (Glossary)

本文件梳理了系统内的特定专业缩写、指标名词与底层概念。

---

## 空间度量与指标

| 术语 | 全称 | 说明 |
|---|---|---|
| **MPI** | Micro-renewal Potential Index | 微更新潜力指数。融合建筑破损度、设施匮乏度、街景杂乱度等多因子，量化各地块更新迫切性 |
| **GVI** | Green View Index | 绿视率。通过语义分割计算街景照片中绿色植被像素占比 |
| **SVF** | Sky View Factor | 天空开敞度。衡量观测点天空未被建筑遮挡的立体角比例 |
| **AHP** | Analytic Hierarchy Process | 层次分析法。用于确定 MPI 各因子的权重系数 |

---

## AI 与算力引擎

| 术语 | 说明 |
|---|---|
| **AIGC** | AI-Generated Content。本项目聚焦于生成总平面图、轴测图、改造效果图等专业规划图纸 |
| **ControlNet** | SD 生态插件，通过 Canny 边缘 / 深度图 / 语义分割等条件对 AI 绘画进行精准空间约束 |
| **Canny** | ControlNet 预处理器之一，提取图像边缘线。本项目用于锁定路网骨架结构 |
| **Segmentation** | ControlNet 预处理器之一，识别图像语义区域。本项目用于锁定用地分区布局 |
| **SDPipeline** | 平台内置的 SD 统一渲染引擎，支持 txt2img / img2img / inpainting / upscale / 多 ControlNet 叠加 |
| **DrawingPipeline** | 端到端图纸编排器，串联提示词构建 → SD 渲染 → 质量评估 → 版本归档 |
| **QualityAssessor** | 双重质量评估：Gemma 视觉评估图面完整性 + DeepSeek 内容评估专业准确性 |
| **DeepSeek** | 云端大语言模型 API，用于案例推演、多主体博弈、学术文本生成等重负荷 NLP 任务 |
| **Ollama / Gemma** | 本地大语言模型运行框架 / 轻量级模型，用于离线推理与视觉评估 |
| **RAG** | Retrieval-Augmented Generation。通过向量检索自动引用政策法规，增强导则生成的专业性 |

---

## GIS 数据管线

| 术语 | 说明 |
|---|---|
| **矢量光栅化** | 将 GeoJSON 矢量数据渲染为像素图像（PNG），供 ControlNet 作为空间约束输入 |
| **空间对齐** | 确保 AI 生成的图纸内容与真实地理坐标系 (WGS-84 / EPSG:3857) 像素级对齐 |
| **GCJ-02** | 火星坐标系，中国国内地图服务常用。需转换为 WGS-84 后方可与国际数据叠合 |
| **BD-09** | 百度坐标系，在 GCJ-02 基础上二次加偏。POI 数据需经 `bd09_to_wgs84()` 转换 |
| **国标用地色值** | 遵循中国城乡用地分类标准 (GB 50137-2011) 的 RGB 配色方案 |

---

## 软件工程架构

| 术语 | 说明 |
|---|---|
| **Stage Data Bus** | 跨阶段数据总线 (`st.session_state["stage_bus"]`)，打破页面间数据孤岛 |
| **`@st.fragment`** | Streamlit 局部重绘装饰器，避免地图交互时全页刷新 |
| **`@st.cache_data`** | Streamlit 内存级缓存，用于空间数据 I/O 与高频计算的性能优化 |
| **Deck.GL** | Uber 开源 WebGL 框架，承载 150 公顷尺度的建筑底座 3D 渲染 |
| **VersionStore** | 版本持久化存储（PNG + JSON 元数据），支持全历史回溯与版本对比 |
| **BatchExporter** | 图册级批量导出，支持一键生成 70+ 张专业图纸 |
| **HyperFrames** | HeyGen 开源视频框架，用于生成 ~9 分钟的答辩汇报视频 |
