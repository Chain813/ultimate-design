# 快速启动指南

本指南用于快速运行当前重构后的 Streamlit 项目。完整安装和 AI 引擎挂载见 [INSTALL_GUIDE.md](INSTALL_GUIDE.md)。

## 1. 轻量演示模式

适合只查看首页、空间数据、3D 地图、诊断结果、成果展示和离线演示内容。

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开：

```text
http://localhost:8501
```

未启动 Stable Diffusion 或 Ollama 时，页面会显示引擎未就绪提示，这是正常状态。系统会尽量保留地图、表格、已有图集和成果导出能力。

## 2. 全量本地模式

如果需要第 03 页实时生图和第 04 页 LLM 多主体协商，请额外启动两个本地服务。

### Ollama

```powershell
ollama run gemma4:e2b-it-q4_K_M
```

默认服务地址：

```text
http://127.0.0.1:11434
```

### Stable Diffusion WebUI

启动 WebUI 时必须开启 API：

```text
--api
```

默认服务地址：

```text
http://127.0.0.1:7860
```

## 3. 当前页面结构

| 页面 | 地址入口 | 用途 |
| --- | --- | --- |
| 首页 | `app.py` | 系统总台、研究范围、模块导览 |
| 01 | `pages/1_数据底座与规划策略.py` | 任务书、开题报告、空间数据、MPI |
| 02 | `pages/2_现状空间全景诊断.py` | 3D 现状底图和地块诊断 |
| 03 | `pages/3_AIGC设计推演.py` | AIGC 设计推演与图集 |
| 04 | `pages/4_LLM博弈决策.py` | 五阶段协商与政策检索 |
| 05 | `pages/5_更新设计成果展示.py` | 成果总图、导则、效果展示 |

## 4. 常用检查

```powershell
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
python -m pytest tests/ -q
python tools/startup_smoke.py
```

## 5. 常见问题

| 问题 | 处理方式 |
| --- | --- |
| 依赖安装慢 | 使用 `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| 第 03 页无法实时生成 | 确认 SD WebUI 已启动并开启 `--api` |
| 第 04 页没有 LLM 回复 | 确认 Ollama 已运行并加载 `gemma4:e2b-it-q4_K_M` |
| GitHub 上传文件过大 | 查看 [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md)，不要上传本地依赖、PDF 和原始影像 |
