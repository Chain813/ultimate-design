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

<p align="center">
  面向城乡规划毕业设计与城市更新研究的循证式工作流平台。<br/>
  围绕长春伪满皇宫周边街区，将任务书、开题报告、空间数据、AIGC 图景推演、LLM 多主体协商和成果展示整合为一套完整的决策支持系统。
</p>

---

## 🐣 快速上手

- **[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)：电脑小白超详细上手指南 (推荐新手阅读)**
- **[GLOSSARY.md](GLOSSARY.md)：规建专业学子的技术术语通俗解释 (像理解 Rhino/CAD 一样理解代码)**
- [QUICK_START.md](QUICK_START.md)：快速启动命令参考
- [INSTALL_GUIDE.md](INSTALL_GUIDE.md)：全量本地环境与 AI 引擎（SD / Ollama）部署指南

---

## ✨ 功能亮点

## 🚀 快速启动

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
