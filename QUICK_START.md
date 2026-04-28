# 🚀 快速启动

这份文档只保留最短启动路径。完整结构和维护规则见 `PROJECT_STRUCTURE.md`。

## 1. 📦 安装依赖

```powershell
pip install -r requirements.txt
```

## 2. ▶️ 启动应用

```powershell
streamlit run app.py
```

访问地址：

```text
http://localhost:8501/
```

## 3. 🧭 页面入口

页面跳转统一使用顶部导航栏。

| 图标 | 页面文件 | 用途 |
| --- | --- | --- |
| 🟦 | `pages/01_前期数据获取与现状分析.py` | 01-05 阶段概览 |
| 🟨 | `pages/02_中期概念生成与应对策略.py` | 06-07 阶段概览 |
| 🟩 | `pages/03_后期设计生成与成果表达.py` | 08-13 阶段概览 |
| 🚶 | `pages/04_现场调研.py` | streetview 街景调研图 |
| 📚 | `pages/11_数据底座与规划策略.py` | 资料、语义、空间资产和 MPI |
| 🗺️ | `pages/12_现状空间全景诊断.py` | 3D 现状底座和地块诊断 |
| 🎨 | `pages/13_AIGC设计推演.py` | 设计图景生成 |
| 🤝 | `pages/14_LLM博弈决策.py` | 多主体协商和图纸提示词 |
| 📦 | `pages/15_更新设计成果展示.py` | 成果图、文本和导出 |

## 4. ✅ 检查命令

```powershell
python -m compileall app.py pages src tests tools
pytest
python tools/check_env.py
python tools/startup_smoke.py
```

## 5. 🧠 可选本地 AI 服务

| 服务 | 用途 | 默认端口 |
| --- | --- | --- |
| Stable Diffusion WebUI | AIGC 图景推演 | `7860` |
| Ollama/Gemma | LLM 协商和政策问答 | `11434` |

未启动本地 AI 服务时，平台仍可查看资料、地图、诊断、街景和已有成果。
