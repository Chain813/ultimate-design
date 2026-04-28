[**English**](./README_EN.md) • [**简体中文**](./README.md) • [**🚀 快速启动**](./QUICK_START.md) • [**🔧 安装指南**](./INSTALL_GUIDE.md) • [**👶 新手教程**](./BEGINNER_GUIDE.md) • [**📖 核心术语**](./GLOSSARY.md) • [**☁️ GitHub部署**](./GITHUB_UPLOAD_GUIDE.md)

---

# 🔧 安装与算力挂载指南 (Installation Guide)

要激活 UltimateDESIGN 的「完全体」形态（包括 AIGC 推演与 LLM 博弈），您需要将本地的算力基础设施与应用进行挂载。

---

### 🧠 1. 挂载本地大模型引擎 (Ollama)

本平台使用轻量级的高性能语言模型 Gemma 来执行政策推演和导则撰写。

1. 前往 [Ollama 官网](https://ollama.com/) 下载并安装客户端。
2. 打开终端，拉取并运行特定的 Gemma 量化版本：
   ```powershell
   ollama run gemma4:e2b-it-q4_K_M
   ```
3. **验证机制**：确保 Ollama 在后台静默运行（默认监听 `127.0.0.1:11434`）。平台主页的 HUD 会自动侦测到该端口，并亮起绿色状态灯。

---

### 🎨 2. 挂载视觉渲染引擎 (Stable Diffusion WebUI)

平台内置的 41 种图纸模板需要依托 SD 的强大生图能力及 ControlNet 约束机制。

1. 启动您的本地 SD WebUI 环境（如秋叶整合包或纯净版 WebUI）。
2. **核心步骤**：必须开启 API 监听模式。在您的启动脚本（如 `webui-user.bat`）中添加以下参数：
   ```bat
   set COMMANDLINE_ARGS=--api --listen
   ```
3. **验证机制**：确保 SD 运行在默认端口 `127.0.0.1:7860`。回到平台主页，此时视觉渲染引擎 HUD 指示灯将显示「已联机」。

---

### 📂 3. 空间数据与资产管理

如果您希望将平台迁移到全新的设计地块，只需替换 `data/` 目录下的底层数据即可，**代码层无需任何修改**。

```text
data/
├── shp/
│   ├── Boundary_Scope.geojson       --- 研究红线底图
│   ├── buildings.geojson            --- 建筑基底（必须包含 Floor 高度字段）
│   └── Key_Plots_District.json      --- 5 个重点更新地块边界
├── streetview/
│   └── (您的调研相片库)              --- 街景调研数据，建议按命名规范存储
└── ...
```

按照上述完成算力挂载与数据替换后，使用 `streamlit run app.py` 启动系统，您即可获得 100% 算力全开的循证更新平台！
