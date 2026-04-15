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

### 1. 🌳 数字孪生沙盘平台 (`1_数字孪生沙盘.py`)
- 基于 PyDeck 构建高质量的城市三维场景交互底座。
- 自动化测度：通过 DeepLabV3+ / Segformer 实现大规模街景的三维空间指标计算（绿视率、天空开阔度、围合度、视觉杂乱度）。
- POI 与路网多层次叠加渲染。

### 2. 🎨 AIGC 历史街区风貌管控 (`2_AIGC风貌管控.py`)
- 结合 Stable Diffusion 与 ControlNet 技术的工业遗产/历史建筑风貌定向修复方案生成。
- 支持四种微更新设计风格迁移：工业遗产保护、生态绿色融合、现代艺术创意、历史文化复兴。
- 交互式效果对比与评估。

### 3. 🚥 交通、人口与活力 (`3_交通与人口.py`)
- 利用路网数据、交通站点数据构建多模态交通耦合分析。
- 基于 POI 密度进行商业活力潮汐时间推演。
- 探索街道活力点与居民/游客分布的时空特征。

### 4. 💬 大语言模型情感计算 (`5_LLM 情感分析.py`)
- 引入前沿的大语言模型 (如 Qwen / DeepSeek) 替代传统词典法，提供对小红书、微博等长文本隐含情绪和空间口碑的精准挖掘分析。
- 城市空间情绪倾向（喜爱、愤怒、悲伤等）的可视化热力分布。
- 社媒数据多维指标穿透分析，自动生成“舆情决策报告”。

### 5. 🕷️ 深度渗透舆情采集引擎 (`spider_engine.py`)
- 基于 Playwright 自动化框架构建的高级浏览态网络爬虫，支持突破反爬机制，深度抓取主流社交媒体用户评价。
- 自带长文本分词、结构化处理、去重和脏数据清洗机制。

### 6. 📊 空间数据管理体系 (`4_数据管理中心.py` & `6_数据总览.py`)
- 支持对所有接入的 CSV / Excel 源数据进行缓存管理、动态清洗和可视化预览。
- 沉浸式的空间数据全景看板大屏概览。

## 📁 核心目录结构

```text
ultimateDESIGN/
├── app.py                      # 平台主入口文件 (Streamlit)
├── pages/                      # 左侧导航栏界面体系模块
│   ├── 1_数字孪生沙盘.py       
│   ├── 2_AIGC风貌管控.py       
│   ├── 3_交通与人口.py         
│   ├── 4_数据管理中心.py       
│   ├── 5_LLM 情感分析.py       
│   └── 6_数据总览.py       
├── spider_engine.py            # 社交舆情数据深度抓取底层架构
├── cv_semantic_engine.py       # CV Segformer 语义级理解与评估引擎
├── core_engine.py              # 数据核心调度和图表方法封装
├── run_deeplabv3.py            # DeepLab 模型推理处理层
├── ui_components.py            # 界面玻璃拟物化通用UI组件与CSS样式池
├── requirements.txt            # 系统全局环境依赖清单
├── 空间数据/                   # 原始空间要素 (SHP/GeoJSON/OSM) 底图
└── StreetViews/                # 分发和用于图像推理的街景集合
```

## 🚀 快速安装构建

本项目推荐在 Anaconda / VenV 虚拟环境下运行，Python 建议版本兼容 `3.8 ~ 3.10`。

### 1. 克隆与进入目录
```bash
git clone https://github.com/yourusername/ultimateDESIGN.git
cd ultimateDESIGN
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
- **自然语言处理 (NLP)**: 集成国产大规模语言模型 (Qwen) 处理分析计算任务
- **数据工程体系**: Pandas, GeoPandas, Playwright (异步结构采集)

## 📄 许可证与使用声明

本项目受开源协议约束，内部附带之算法与城市特征空间数据源**仅供高等教育、学术科研、毕业设计及非营利用途展示**。未经直接许可，禁止将包含的各项基础平台组件与内置 API Key 直接复用于商业盈利性规划项目。

---

> **重要提示**: 环境初次构建及 CV 语义切割引擎启动时，程序可能在后台下载相关预训练视觉分类器权重 (Hugging Face 模型库)。请确保终端网络环境通畅通达；如启用高级情感报告，需要确保存续可用之大语言模型环境。
