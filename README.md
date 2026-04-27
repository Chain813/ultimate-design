<p align="right">
  <a href="README_EN.md">English Version</a> | <strong>中文版</strong>
</p>

<h1 align="center">🏙️ UltimateDESIGN</h1>
<h3 align="center">长春伪满皇宫周边街区微更新决策支持平台</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10~3.12-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.38-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/LLM-Ollama%20%2F%20Gemma-8A2BE2" alt="LLM">
  <img src="https://img.shields.io/badge/AIGC-Stable%20Diffusion-green" alt="AIGC">
  <img src="https://img.shields.io/badge/Image%202.0-Prompt%20Assistant-0EA5E9" alt="Image Prompt Assistant">
  <img src="https://img.shields.io/badge/License-Academic-orange" alt="License">
</p>

---

## 📖 项目概况

**UltimateDESIGN** 是一款专为**城乡规划**、**建筑学**专业学生及研究人员设计的、基于数据驱动的城市微更新决策支持平台。

### 1. 研究背景与挑战
本项目以**长春伪满皇宫周边街区**为实证研究对象。该区域作为典型的历史文化街区，在城市更新过程中面临着：
- **数据孤岛**：空间数据、政策条文、社情民意散落在不同平台。
- **决策主观**：传统规划往往依赖规划师个人经验，缺乏量化的现状诊断。
- **沟通鸿沟**：复杂的规划方案难以让非专业人士（如居民、政府人员）直观理解并参与讨论。

### 2. 解决方案
平台提出了一套**“数据底座 + 循证诊断 + AI 协同”**的闭环工作流：
- **数字孪生基底**：整合多源空间数据（GIS、路网、POI、街景），构建 3D 现状诊断底座。
- **循证推演模型**：建立从“任务书解析”到“空间诊断”，再到“多主体博弈”的五阶段决策路径。
- **双引擎 AI 驱动**：
    - **AIGC (Stable Diffusion)**：将枯燥的规划参数转化为高保真的设计意向图，实现“设计即见”。
    - **LLM (Ollama/Gemma)**：利用 RAG 技术对政策库进行检索，模拟多主体（政府、开发商、居民）协商，辅助达成规划共识。
- **图纸提示词助手**：在 LLM 博弈决策页面接入 ChatGPT Image 2.0 图纸提示词生成流程，按图册章节、图纸类型、精度等级和上传资料完整性生成可复制提示词。

---

## ✨ 核心功能

平台围绕规划全生命周期划分为五大模块，并在决策页内补充图册生产辅助工具：

1.  **📊 数据底座与规划策略**：整合任务书、开题报告及 MPI 更新潜力评估模型，确立研究起点。
2.  **🗺️ 现状空间全景诊断**：支持 3D 地图交互，叠加交通、品质、热力等图层，实现地块级的雷达图健康诊断。
3.  **🎨 AIGC 设计图景推演**：利用 Stable Diffusion 实时生成更新意向图，支持 Before/After 对比展示。
4.  **🤖 LLM 循证博弈决策**：基于知识库检索政策导则，驱动多角色 AI 进行博弈，生成规划建议书。
5.  **📋 更新设计成果展示**：汇总设计导则、总图成果及效果图集，支持一键导出 Word 研究报告。
6.  **🖼️ 图纸提示词助手**：面向 A3 图册、A1 展板和汇报 PPT，生成符合真实边界、底图约束、图例规则和统一风格的 Image 2.0 提示词；一级精度图纸缺少底图时会拦截生成，二级精度图纸缺少数据时仅输出视觉表达模板。

---

## 🐣 快速上手

- **[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)：电脑小白超详细上手指南 (推荐新手阅读)**
- **[GLOSSARY.md](GLOSSARY.md)：城乡规划专业学子的技术术语通俗解释 (像理解 GIS/控规一样理解代码)**
- [QUICK_START.md](QUICK_START.md)：快速启动命令参考
- [INSTALL_GUIDE.md](INSTALL_GUIDE.md)：全量本地环境与 AI 引擎（SD / Ollama）部署指南

---

## 🚀 启动预览

> **轻量演示模式** — 无需 GPU 或 AI 引擎，可直接查看首页、空间数据、3D 地图、诊断结果和成果展示。
> 
> 详细步骤请参考：**[QUICK_START.md](QUICK_START.md)**

---

## 📁 项目文件结构说明

```text
ultimateDESIGN/
├── app.py                         # Streamlit 平台总台入口
├── pages/                         # 业务功能页面 (01-05 循证工作流)
│   ├── 1_数据底座与规划策略.py      # 资料管理、评估指标与资产清单
│   ├── 2_现状空间全景诊断.py      # 3D 地图交互与空间量化评估
│   ├── 3_AIGC设计推演.py          # 基于 SD 的更新图景生成
│   ├── 4_LLM博弈决策.py          # 基于 RAG 的多主体协商模型与图纸提示词助手
│   └── 5_更新设计成果展示.py      # 成果汇总与报告导出
├── src/                           # 核心业务逻辑组件
│   ├── config/                    # 系统配置：路径注册、环境变量、模型参数
│   ├── engines/                   # 核心引擎：空间分析、AIGC、RAG、LLM、图纸提示词模板
│   ├── ui/                        # 统一 UI 系统：设计组件、图表主题、导航
│   └── utils/                     # 通用工具：坐标转换、服务探活、文档生成
├── assets/                        # 前端静态资源：CSS 样式、地图 HTML 模板、流程图与封面图片
├── data/                          # 规划数据底座
│   ├── shp/                       # 地块、建筑、边界等空间 GeoJSON 数据
│   ├── meta/                      # 政策文本、语义提取等文本元数据
│   └── *.csv / *.xlsx             # POI、交通、人口、评价指标等统计数据
├── tools/                         # 独立工具脚本
│   ├── get_poi.py                 # POI 数据抓取工具
│   ├── rebuild_rag.py             # 重新构建政策知识库索引
│   └── startup_smoke.py           # 系统启动冒烟测试
├── docs/                          # 本地资料库：规划规范 PDF、项目任务书 (默认不上传 GitHub)
├── static/                        # Streamlit 静态资源缓存 (如超大体积 GeoJSON)
├── tests/                         # 系统单元测试（含核心引擎与图纸提示词助手测试）
├── config.yaml                    # 全局运行配置文件
├── requirements.txt               # Python 环境依赖清单
├── setup_env.bat                  # 一键配置本地环境脚本
└── README.md                      # 项目主说明文档
```

---

## 📁 项目文档与开发

### 🧪 校验命令

```powershell
# 语法检查
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
# 单元测试
python -m pytest tests/ -q
# 本次图纸提示词助手相关回归测试
python -m pytest tests/test_core_engine.py tests/test_image_prompt_engine.py -q
# 启动冒烟测试
python tools/startup_smoke.py
```

---

## 📜 使用声明

本项目用于学术研究、课程展示和毕业设计演示。项目中的规划资料、空间数据和社会感知数据应按来源授权和隐私要求使用，不建议直接用于商业决策。
