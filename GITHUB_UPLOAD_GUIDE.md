[**English**](./README_EN.md) • [**简体中文**](./README.md) • [**🚀 快速启动**](./QUICK_START.md) • [**🔧 安装指南**](./INSTALL_GUIDE.md) • [**👶 新手教程**](./BEGINNER_GUIDE.md) • [**📖 核心术语**](./GLOSSARY.md) • [**☁️ GitHub部署**](./GITHUB_UPLOAD_GUIDE.md)

---

# ☁️ 代码托管与部署规约 (GitHub Upload Guide)

本文档旨在说明如何将本地经过优化的 UltimateDESIGN 源代码正确地上传至 GitHub 仓库，并利用 GitHub Actions 触发 CI/CD (持续集成/持续部署) 工作流。

---

### 📦 1. 暂存与代码提交

在推送代码之前，请务必在本地确认各项自检均已通过，杜绝将脏代码推至主线分支。

1. **执行健康检查**：在终端运行 `python tools/startup_smoke.py` 与 `pytest`，确保无致命的红字报错。
2. **规范化提交信息**：我们要求 Commit 遵循学术与工程融合的规范（如使用 `feat:`, `fix:`, `docs:`, `perf:` 前缀）。
   ```powershell
   git add .
   git commit -m "perf: 统一替换地图组件为 @st.fragment 挂载机制"
   ```

---

### 🚀 2. 推送至远程分支

确认无误后，将本地更迭推送到 GitHub 远端仓库：

```powershell
git push origin main
```

*(注：系统的主分支默认锁定为 `main`。若您在此前创建了本地特性分支，请先提交合并请求 PR)*

---

### ⚙️ 3. 触发 CI/CD 自动化检测

当您成功将代码 push 到 `main` 分支后，GitHub Actions 将会自动捕捉此操作，并在无头服务器环境拉取代码。它将按序执行以下操作，为您进行多重云端检验：

- **Lint 语法筛查**：自动检测 `src/` 和 `pages/` 下的 Python 缩进与类型定义。
- **依赖映射探测**：检测 `requirements.txt` 中是否出现了会导致不同平台装配崩溃的冗余包。
- **13 阶段页面遍历测试**：它将静默执行我们提前植入的 Smoke Test，逐一敲击 13 个 `page_XX.py` 的路由网关，确保无任何 `Errno 2: No such file` 或 `TypeError`。

**您可以在 GitHub 项目主页的 `Actions` 面板中，实时审视这枚绿色 `Pass` 徽章的点亮过程！**
