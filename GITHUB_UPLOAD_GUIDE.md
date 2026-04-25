# 📤 GitHub 上传与云端部署指南 (Upload & Deploy Guide)

将您的数字孪生平台上传到 GitHub 并非仅仅为了备份，这是将其部署至 **Streamlit Community Cloud** 供全球访问的必经之路。

---

## 🛑 第一步：了解数据的“去与留” (.gitignore 机制)

本项目的核心数据资产较多。为了防止因为文件过大导致 GitHub 拒绝上传，项目中已提前配置好 `.gitignore` 文件。

**✅ 以下核心文件会被自动上传（云端能够直接读取）：**
- 代码包：`app.py`, `pages/`, `src/` (13模块：6引擎+4工具+UI+配置), `tools/`
- 前端静态资源：`assets/` (CSS / SVG / HTML)
- 测试套件：`tests/` (49 测试，8 模块覆盖)
- 地理要素基底：`data/shp/` 目录下的 GeoJSON 文件（包括建筑轮廓）
- 脱敏指标表：`data/` 目录下的各类 `.csv` 与 `.xlsx` 统计报表

**🚫 以下大体积文件将被自动阻挡拦截（保护您的隐私与流量）：**
- `data/streetview/`：包含成千上万张从百度街景抓取的高清影像图。
- `data/raw_images/`：高清航拍底图与正射影像。
- `*.pdf`：所有扫描版规划长图与法条文本。

> [!TIP]
> **无需担心云端报错死机！(自适应降级机制)**
> 系统代码中已编写了基于环境变量的“熔断保护与自适应演示模式”回退逻辑。云端页面在侦测到处于无显卡环境时，会**自动阻断底层的 Selenium 高频爬虫与大模型生图请求**，全面切入“离线静态数据湖”展示，绝不引发任何崩溃！

---

## 🚀 第二步：推送代码至 GitHub

若您对 Git 命令行不熟悉，建议使用以下最简明的方案。

### 推荐方案：使用 GitHub Desktop (白痴级极简操作)

1. 前往下载并安装 [GitHub Desktop](https://desktop.github.com/)，并登录您的 GitHub 账号。
2. 运行软件，点击左上角 `File` -> `Add local repository`。
3. 选择您本地的 `ultimateDESIGN` 文件夹路径，点击 `Add repository`。
4. 在左下角的 **Summary** 框中随便写点什么（例如 `init project`），然后点击蓝色的 **Commit to main**。
5. 最后，点击界面顶部蓝色的 **Publish repository** 按钮。在弹出的确认框中，确保**取消勾选** "Keep this code private"（如果您要公开展示的话），最后点击确认。

---

## ☁️ 第三步：在 Streamlit Cloud 一键上线

当您的代码成功上传到 GitHub 后，将其变成所有人可以通过网址访问的网页，只需 1 分钟：

1. 访问 [Streamlit Community Cloud](https://share.streamlit.io/) 并使用您的 GitHub 账号授权登录。
2. 点击右上角的 **New app**。
3. 在部署配置界面：
   - **Repository**：选择您刚刚上传的 `ultimateDESIGN`。
   - **Branch**：默认 `main` 即可。
   - **Main file path**：务必填写 `app.py`（这是系统的核心总枢纽）。
   - **App URL**：可以自定义一串炫酷的网址。
4. 点击 **Deploy!**。

静候大约 1-3 分钟，等云端服务器自动根据 `requirements.txt` 安装完依赖后，您的学术成果便正式向全世界开放啦！🎉
