<h1 align="center">长春伪满皇宫周边街区：多模态微更新决策系统</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-Framework-FF4B4B.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/DeepLabV3%2B-CV-orange.svg" alt="DeepLabV3+">
  <img src="https://img.shields.io/badge/AIGC-Stable%20Diffusion-purple.svg" alt="AIGC">
  <img src="https://img.shields.io/badge/LLM-Sentiment%20Analysis-green.svg" alt="LLM">
</p>

## 🏙️ 项目简介

本项目是一个针对于**长春伪满皇宫周边历史文化街区**开发的**多模态城市微更新决策支持平台**。平台深度整合了 **空间数字孪生 (Digital Twin)**、**计算机视觉 (CV)** 与 **生成式大模型 (AIGC/LLM)** 技术，旨在通过多源城市大数据（街景、社媒、交通、POI 等）的跨尺度融合，为历史街区的风貌修缮、活力激发和情感感知提供量化支撑与协同辅助设计能力。

## ✨ 核心功能模块

### 1. 🔬 数据底座与规划策略实验室 (`1_数据底座与规划策略.py`)
- 基于 AHP 层次分析法的多维度更新潜力指标体系 (MPI)，支持专家权重动态调节与实时排行。
- 集成 MarkItDown 跨模态语义萃取引擎，批量解析 PDF/Word/PPT 规划文档。
- 后台地理数据资产管理，支持 POI、交通、CV 分析结果、情感数据的在线预览与覆盖上传。

### 2. 🏙️ 数字孪生与全息诊断实验室 (`2_数字孪生与全息诊断.py`)
- 基于 PyDeck 构建高质量城市三维场景交互底座，支持 GVI/SVF 等空间指标的 3D 柱体与热力渲染。
- 24H 交通潮汐动态推演，POI 密度蜂窝聚合、实测散点与交通拥堵脉冲多图层叠加。
- 社会情感评价模块：基于 HuggingFace 多语言模型的真实情感分类，支持多平台数据源筛选与情感分布可视化。

### 3. 🎨 AIGC 创意生成推演实验室 (`3_AIGC设计推演.py`)
- 结合 Stable Diffusion 与 ControlNet 技术的历史街区风貌定向修复方案生成。
- 支持五大更新方向、十种设计策略，含景观介入度、历史锚定力等规划算子实时调控。
- 交互式图像几何校正、前后对比与成果导出。

### 4. ⚖️ LLM 智慧决策博弈实验室 (`4_LLM博弈决策.py`)
- 基于 Gemma 4 离线大模型的多利益相关者协商平台（居民/开发商/规划专家三方角色）。
- 多轮博弈推演与自动生成综合评估报告。

## 📁 核心目录结构

```text
ultimateDESIGN/
├── app.py                          # 平台主入口文件 (Streamlit)
├── pages/                          # 左侧导航栏界面体系模块
│   ├── 1_数据底座与规划策略.py      # 01 MPI评估 + MarkItDown萃取 + 数据管理
│   ├── 2_数字孪生与全息诊断.py      # 02 3D沙盘 + 交通诊断 + 社会情感
│   ├── 3_AIGC设计推演.py           # 03 Stable Diffusion + ControlNet 风貌推演
│   └── 4_LLM博弈决策.py            # 04 Gemma 4 多主体协商
├── core_engine.py                  # 数据核心调度：空间测度/NLP情感/交通/SD/LLM
├── cv_semantic_engine.py           # Segformer 语义分割与四维空间指标计算
├── run_deeplabv3.py                # DeepLabV3 备选 CV 推理方案
├── spider_engine.py                # 多源舆情采集引擎 (微博/小红书/抖音)
├── ui_components.py                # 全局导航栏与 CSS 样式组件
├── utils/geo_transform.py          # BD09→GCJ02→WGS84 坐标转换
├── check_env.py                    # 环境依赖与文件完整性自检
├── requirements.txt                # 系统全局环境依赖清单
├── assets/                         # 静态资源 (模块封面图 + style.css)
├── data/                           # 数据目录
│   ├── 空间数据/                   # 原始空间要素 (GeoJSON/SHP)
│   └── StreetViews/                # 街景图像集合 (Point_xxx/)
└── temp/                           # 参考文献 PDF
```

## 🚀 快速安装构建

本项目推荐在 Anaconda / VenV 虚拟环境下运行，Python 建议版本兼容 `3.8 ~ 3.10`。

### 1. 克隆与进入目录
```bash
git clone https://github.com/yourusername/ultimateDESIGN.git
cd <你的项目目录>
```

### 2. 建立虚拟环境并激活
```bash
python -m venv venv
# Windows 激活
venv\Scripts\activate
# Mac/Linux 激活 (如适用)
# source venv/bin/activate
```

### 3. 安装依赖树
```bash
pip install -r requirements.txt
```

*(因舆情嗅探爬虫模块内嵌了反爬渗透组件，首次部署建议初始化安装宿主浏览器环境)*：
```bash
playwright install chromium
```

### 4. 运行主控平台
完成基础环境配置后，运行 Streamlit 启动命令：
```bash
streamlit run app.py
```
*(Windows 系统亦可直接双击运行环境根目录的 `run.bat` 一键启动)*

## 🛠️ 技术栈与算法模型

- **前端与可视化底座**: Streamlit, Plotly, PyDeck (结合 deck.gl 构建数字高程与点云映射)
- **计算机视觉 (CV)**: PyTorch, Transformers (Hugging Face 提供基础支持), DeepLabV3+ / SegFormer
- **生成式 AI (AIGC)**: Stable Diffusion 模型底层架构 / ControlNet 结构控制器
- **自然语言处理 (NLP)**: HuggingFace Transformers 多语言情感分类模型 + Ollama 本地大模型 (Gemma 4) 博弈推理
- **数据工程体系**: Pandas, GeoPandas, Playwright (异步结构采集)

## 📄 许可证与使用声明

本项目受开源协议约束，内部附带之算法与城市特征空间数据源**仅供高等教育、学术科研、毕业设计及非营利用途展示**。未经直接许可，禁止将包含的各项基础平台组件与内置 API Key 直接复用于商业盈利性规划项目。

---

> **重要提示**: 环境初次构建及 CV 语义切割引擎启动时，程序可能在后台下载相关预训练视觉分类器权重 (Hugging Face 模型库)。请确保终端网络环境通畅通达；如启用高级情感报告，需要确保存续可用之大语言模型环境。
