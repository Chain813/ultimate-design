# UltimateDESIGN 项目超详细说明（公式与处理流程）

> 本文档按“数据 -> 模型 -> 可视化 -> 决策”全链路说明系统，覆盖核心公式、变量定义、处理流程、输入输出与异常路径。

## 1. 系统定位与总流程

本系统是一个基于 Streamlit 的多页面城市微更新决策平台，核心能力为：

1. 多源数据底座管理（POI、交通、街景、舆情）
2. 数字孪生可视化诊断（2D/3D）
3. AIGC 方案推演（Stable Diffusion + ControlNet）
4. LLM 多主体协商（Ollama 本地模型）

### 1.1 全局流程图（逻辑）

1) 数据进入  
`data/*.csv`、`data/shp/*.json/geojson`、`data/streetview/*`

2) 指标计算  
MPI（多维潜力）、GVI/SVF/围合/杂乱、情感分值、词频

3) 多模态输出  
表格、散点、热力、柱状图、地图图层、AIGC 对比图、协商报告

4) 决策闭环  
专家权重调参 -> 指标重算 -> 方案推演 -> 多方协商

---

## 2. 目录与模块职责

- `app.py`：主页、导航、主视觉、项目级总览
- `pages/1_数据底座与规划策略.py`：MPI/AHP、文档语义萃取、数据管理
- `pages/2_数字孪生与全息诊断.py`：3D/2D地图、交通活力、舆情分布
- `pages/3_AIGC设计推演.py`：ControlNet 参数化图像生成
- `pages/4_LLM博弈决策.py`：多角色协商和总结
- `src/engines/core_engine.py`：核心引擎（配置、NLP、RAG、AIGC、LLM）
- `src/engines/cv_semantic_engine.py`：语义分割与城市空间指数计算
- `src/engines/spider_engine.py`：微博/小红书/抖音采集
- `src/config/runtime.py` 与 `src/config/paths.py`：统一路径解析与常量

---

## 3. 数学模型与公式（逐项）

## 3.1 MPI 多维更新潜力指数（页面 1、页面 2）

### 公式

\[
MPI_i = \frac{w_{space}\cdot S_i + w_{social}\cdot D_i + w_{env}\cdot(1-E_i)}{w_{space}+w_{social}+w_{env}+\epsilon}\times 100
\]

其中 \(\epsilon=0.001\)（代码中用于防止除零）。

### 变量定义

- \(S_i\)：地块空间潜力原分（`空间潜力原分`）
- \(D_i\)：社会需求原分（`社会需求原分`）
- \(E_i\)：环境现状评分（`环境现状评分`）
- \(1-E_i\)：环境干预紧迫度（反向处理）
- \(w_{space}, w_{social}, w_{env}\)：专家权重（滑块输入）

### 处理流程

1. 读取地块数据（来自 `Key_Plots_District.json` 或 fallback）
2. 用户调节三项权重
3. 实时计算每个地块 `MPI 得分`
4. 应用阈值筛选
5. 输出排行榜、散点图和 CSV 报告

---

## 3.2 AHP 判断矩阵（页面 1）

### 权重归一化

\[
\mathbf{w}' = \frac{[w_{space}, w_{social}, w_{env}]}{w_{space}+w_{social}+w_{env}+\epsilon}
\]

### 判断矩阵构造（3x3）

\[
A_{ij} = \frac{w'_i}{w'_j+\epsilon}
\]

主对角线固定为 1，形成当前权重对应的相对重要性矩阵展示。

---

## 3.3 动态颜色映射（页面 2 与 core_engine）

对指标值 \(v\) 做归一化：

\[
n = \frac{v-v_{min}}{v_{max}-v_{min}}
\]

映射到 RGBA（示意）：

\[
R=255(1-n),\quad G=200\sin(\pi n),\quad B=255n,\quad A\in\{210,255\}
\]

用于 3D 柱体与点位着色。

---

## 3.4 CV 空间指数（`cv_semantic_engine.py`）

语义分割后，像素总数为 \(P\)，各类别像素计数如下：

- \(P_{veg}\)：Vegetation
- \(P_{sky}\)：Sky
- \(P_{building}\)：Building
- \(P_{wall}\)：Wall
- \(P_{fence}\)：Fence
- \(P_{pole}\)：Pole
- \(P_{sign}\)：TrafficSign
- \(P_{light}\)：TrafficLight

### 绿视率（GVI）

\[
GVI = \frac{P_{veg}}{P}\times 100
\]

### 天空开敞度（SVF）

\[
SVF = \frac{P_{sky}}{P}\times 100
\]

### 围合度（Enclosure）

\[
Enclosure = \frac{P_{building}+P_{wall}+P_{veg}}{P}\times 100
\]

### 视觉杂乱度（Clutter）

\[
Clutter = \frac{P_{pole}+P_{sign}+P_{light}+P_{fence}}{P}\times 100
\]

---

## 3.5 LLM 检索打分（`core_engine.py` 中 RAG）

对用户 prompt 分词后得到词集合 \(W\)，对每个知识片段内容 \(C_k\)：

\[
score_k = \sum_{w\in W}\mathbf{1}(w\in C_k)
\]

按 `score_k` 逆序，取 Top-3 拼接到系统提示词，作为上下文增强。

---

## 3.6 情感分值映射（`classify_sentiment`）

模型输出标签 `positive/negative/neutral` 与概率 \(p\) 后映射：

\[
score=
\begin{cases}
p,&label=positive\\
0,&label=neutral\\
-p,&label=negative
\end{cases}
\]

并四舍五入到 3 位小数。

---

## 4. 页面级处理流程（逐页面）

## 4.1 页面 1：数据底座与策略实验室

### 子模块 A：资产综合评估

1. 读取地块 GeoJSON
2. 提取 `Shape_Area` + 属性
3. 构造基础分（含稳定伪随机）
4. 用户调权重、阈值
5. 计算 MPI、排序、过滤
6. 可视化输出与 CSV 导出

### 子模块 B：策略语义萃取

1. 上传文档（PDF/Word/PPT）
2. `MarkItDown().convert()` 提取文本
3. 存入 `session_state`
4. 文本预览（Markdown）

### 子模块 C：物理底座管理

1. 选择数据对象（POI/交通/CV/NLP）
2. 预览前 30 行
3. 上传覆盖目标 CSV
4. 刷新页面

---

## 4.2 页面 2：数字孪生与全息诊断

### 子模块 A：3D 空间全景

1. 读取点位 + GVI 分析结果并按 `ID` 合并
2. 选择核心指标（GVI/SVF/Enclosure/Clutter）
3. 构造柱体图层 payload 与热力图 payload
4. 注入 HTML 模板占位符
5. `components.html(...)` 输出可交互地图

### 子模块 B：交通与活力诊断

1. 读取 POI 数据
2. 构造 hex 图层参数（半径、拉伸）
3. 切换视角和图层开关
4. 渲染交通/POI/建筑叠加

### 子模块 C：评价数据与社会感知

1. 读取 NLP 数据（utf-8-sig -> gbk 回退）
2. 平台过滤（微博/小红书/抖音）
3. 若无 `Score`，调用情感模型补算
4. 输出文本表与情感直方图

---

## 4.3 页面 3：AIGC 设计推演

### 输入

- 实测街景图
- ControlNet 模式、权重
- 采样器、steps、CFG、seed
- 规划算子（绿化、历史、现代、电影感）

### 流程

1. 图像几何预处理（旋转、裁剪）
2. 组合提示词（模板 + 动态权重项）
3. 映射 ControlNet 预处理器与模型名
4. 组装 SD `img2img` payload
5. 请求本地 SD API
6. 返回图像并做 before/after 滑块对比

### 输出

- 渲染结果图
- 对比滑块
- JPG 下载

---

## 4.4 页面 4：LLM 多方博弈决策

### 角色

- 居民代表（民生/安置/环境）
- 开发商（收益/密度/业态）
- 规划师（法规/文脉/公共性）

### 流程

1. 输入提案文本
2. 对每个角色构建 system prompt
3. 逐角色流式调用 `call_llm_engine_stream`
4. 展示思维链与正式回复
5. 汇总三方观点，调用 LLM 生成最终政策建议
6. 导出 TXT 报告

---

## 5. 引擎级处理流程（逐引擎）

## 5.1 `core_engine.py`

- 配置加载：`config.yaml`
- RAG 加载：`data/rag_knowledge.json`
- HUD 统计：POI/NLP/GVI/边界面积
- 空间数据：点位和 GVI 合并 + 动态色彩
- 情感模型：Transformers pipeline 批推理
- AIGC：SD WebUI `img2img` 请求
- LLM：Ollama chat（普通/流式）

### 外部请求端点

- SD：`/sdapi/v1/img2img`
- Ollama：`/api/chat`

### 容错机制

- 网络超时/连接失败重试
- 文件缺失 fallback
- demo 模式短路返回占位内容

---

## 5.2 `cv_semantic_engine.py`

1. 遍历 `data/streetview/Point_*`
2. SegFormer 推理得到分割 mask
3. 计算四项指数
4. 点位级取均值
5. 追加写入 `data/GVI_Results_Analysis.csv`
6. 支持断点续跑（读取已有 ID）

---

## 5.3 `spider_engine.py`

### 总体

- Selenium + 反检测浏览器
- 三平台分模块采集
- 去重与合并写入 NLP 数据库

### 通用策略

- 随机 User-Agent
- 滚动 + 停顿 + 随机抖动
- 双阶段采集（搜索页 + 详情评论）
- 文本去重（按 `Text`）

---

## 6. 数据输入输出清单

## 6.1 输入（关键）

- `data/shp/Key_Plots_District.json`
- `data/shp/Boundary_Scope.geojson`
- `data/Changchun_POI_Real.csv`
- `data/Changchun_Traffic_Real.csv`
- `data/CV_NLP_RawData.csv`
- `data/Changchun_Precise_Points.xlsx`
- `data/streetview/Point_*/`

## 6.2 输出（关键）

- `data/GVI_Results_Analysis.csv`（CV 引擎）
- `Urban_Renewal_MPI_Report.csv`（页面导出）
- `consultation_report.txt`（LLM 页面导出）
- `result.jpg`（AIGC 页面导出）

---

## 7. 关键异常路径与降级策略

1. **配置缺失**：返回空配置，使用默认 URL
2. **数据缺失**：页面显示 fallback 或错误提示
3. **模型服务不可用**：LLM/SD 返回可读错误信息
4. **编码异常**：NLP CSV 从 utf-8-sig 回退 gbk
5. **推理失败**：try/except + 重试 + demo 模式回退

---

## 8. 质量保障与工程流程

- CI 并行任务：`lint` + `test` + `smoke`
- 提交前钩子：`ruff` + `pytest`
- 环境自检：`tools/check_env.py`
- 启动冒烟：`tools/startup_smoke.py`
- 密钥扫描：`tools/secret_scan.py`

---

## 9. 后续建议（面向可扩展架构）

1. 页面中的计算逻辑进一步下沉到 `src/engines/`
2. 为 MPI/AHP、RAG、AIGC payload 设计独立服务类
3. 引入 typed schema（pydantic）校验配置和输入
4. 为 CV/NLP/LLM 增加可追溯日志与实验记录
5. 建立数据版本管理（数据字典 + 元数据）
