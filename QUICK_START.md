[**English**](./README_EN.md) • [**简体中文**](./README.md) • [**🚀 快速启动**](./QUICK_START.md) • [**🔧 安装指南**](./INSTALL_GUIDE.md) • [**👶 新手教程**](./BEGINNER_GUIDE.md) • [**📖 核心术语**](./GLOSSARY.md) • [**☁️ GitHub部署**](./GITHUB_UPLOAD_GUIDE.md)

---

# 🚀 快速启动 (Quick Start)

这份文档旨在为您提供**最短路径**将本项目在本地跑通。对于底层算力的详细配置方案，请参阅 **[🔧 安装指南](./INSTALL_GUIDE.md)**。

---

### 📦 1. 环境准备与依赖安装

请确保您的计算机已安装 Python 3.10+。打开终端，克隆代码库并安装核心依赖：

```powershell
# 1. 抓取代码
git clone https://github.com/Chain813/ultimate-design.git
cd ultimate-design

# 2. 安装依赖
pip install -r requirements.txt
```

---

### ▶️ 2. 启动总控制台

无需预先配置任何复杂的 API Key，您可以直接通过 Streamlit 唤醒系统界面：

```powershell
streamlit run app.py
```

服务启动后，您的默认浏览器将自动打开并访问：
`http://localhost:8501/`

---

### 🧭 3. 基础页面导航机制

系统取消了传统的侧边栏导航，所有的模块跳转均在 **顶部导航栏 (Top Nav)** 完成。
请按照 `[01]` 到 `[13]` 的编号顺序，依次体验城市设计的完整推演流。

---

### ✅ 4. 健康自检 (Smoke Test)

如果您修改了任何代码，请在重新启动前运行以下命令以确保系统状态健康：

```powershell
# 语法合规性检查
python -m compileall app.py pages src tests tools

# 自动化测试引擎校验
pytest

# 启动核心环境监测
python tools/startup_smoke.py
```
