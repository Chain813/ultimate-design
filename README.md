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

---

## ✨ 核心功能

平台围绕规划全生命周期划分为五大模块：

1.  **📊 数据底座与规划策略**：整合任务书、开题报告及 MPI 更新潜力评估模型，确立研究起点。
2.  **🗺️ 现状空间全景诊断**：支持 3D 地图交互，叠加交通、品质、热力等图层，实现地块级的雷达图健康诊断。
3.  **🎨 AIGC 设计图景推演**：利用 Stable Diffusion 实时生成更新意向图，支持 Before/After 对比展示。
4.  **🤖 LLM 循证博弈决策**：基于知识库检索政策导则，驱动多角色 AI 进行博弈，生成规划建议书。
5.  **📋 更新设计成果展示**：汇总设计导则、总图成果及效果图集，支持一键导出 Word 研究报告。

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

## 📁 项目文档与开发

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)：详细的项目目录职责、UI 层约定与维护说明。
- [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md)：GitHub 上传规范、代码清理规则及 Streamlit Cloud 部署流程。

### 🧪 校验命令

```powershell
# 语法检查
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
# 单元测试
python -m pytest tests/ -q
# 启动冒烟测试
python tools/startup_smoke.py
```

---

## 📜 使用声明

本项目用于学术研究、课程展示和毕业设计演示。项目中的规划资料、空间数据和社会感知数据应按来源授权和隐私要求使用，不建议直接用于商业决策。
