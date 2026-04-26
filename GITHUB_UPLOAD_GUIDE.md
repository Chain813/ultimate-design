# GitHub 上传与部署指南

本文档说明当前项目哪些内容适合上传 GitHub，哪些内容应留在本地，以及如何部署到 Streamlit Community Cloud。

## 1. 上传前检查

建议先运行：

```powershell
git status --short
python tools/secret_scan.py
python -m pytest tests/ -q
```

如果本地没有完整 AI 环境，也至少运行：

```powershell
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
```

## 2. 应上传的内容

| 类型 | 路径 |
| --- | --- |
| Streamlit 页面 | `app.py`, `pages/` |
| 核心代码 | `src/config/`, `src/engines/`, `src/ui/`, `src/utils/` |
| UI 和地图资源 | `assets/`, `static/` |
| 脱敏数据 | `data/*.csv`, `data/*.xlsx`, `data/shp/`, `data/meta/` |
| 工具与测试 | `tools/`, `tests/` |
| GitHub 说明文件 | `README.md`, `README_EN.md`, `PROJECT_STRUCTURE.md`, `QUICK_START.md`, `INSTALL_GUIDE.md` |

## 3. 不应上传的内容

项目 `.gitignore` 已默认排除：

| 类型 | 路径或规则 |
| --- | --- |
| 本地依赖环境 | `.venv/`, `.runtime-packages/` |
| 运行日志 | `*.log`, `*.err`, `*.err.log` |
| 本地密钥 | `.env` |
| 大体积原始影像 | `data/streetview/`, `data/raw_images/` |
| 本地规划资料 | `docs/`, `*.pdf` |
| 运行配置 | `config_daemon.json` |

这些文件不应通过普通 Git 提交进入公开仓库。若确实需要发布大文件，建议使用 Git LFS 或独立网盘，并在 README 中注明下载方式。

## 4. 推荐提交流程

```powershell
git status --short
git add app.py pages src assets data static tools tests README.md README_EN.md PROJECT_STRUCTURE.md QUICK_START.md INSTALL_GUIDE.md GITHUB_UPLOAD_GUIDE.md .github .gitignore requirements.txt pyproject.toml pytest.ini
git commit -m "Refactor UI structure and update project docs"
git push
```

提交前请根据 `git status --short` 再确认一次，不要把本地运行产物误加入暂存区。

## 5. Streamlit Cloud 部署

1. 打开 [Streamlit Community Cloud](https://share.streamlit.io/)。
2. 选择 GitHub 仓库。
3. Main file path 填写：

```text
app.py
```

4. Python 依赖由 `requirements.txt` 安装。
5. 云端通常没有本地 GPU、Stable Diffusion 和 Ollama，因此第 03 页、第 04 页会以离线或降级模式展示。

## 6. 部署后的验收项

| 检查项 | 预期 |
| --- | --- |
| 首页打开 | 能看到统一 Banner、模块入口和运行状态 |
| 01 页 | 能显示任务书/开题报告入口、MPI 表格、空间数据资产清单 |
| 02 页 | 能显示 3D 底图或降级提示、地块诊断数据 |
| 03 页 | 无本地 SD 时不崩溃，有演示图或提示 |
| 04 页 | 无 Ollama 时显示引擎未就绪提示，不阻断页面 |
| 05 页 | 能查看成果结构，并可在本地导出 Word |
