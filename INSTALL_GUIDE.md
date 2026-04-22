# 🖥️ 深度安装与核心引擎部署指南 (Installation & Deployment Guide)

本文档将指导您从零开始搭建本项目的开发环境，并详细解读两大核心 AI 引擎（Stable Diffusion & Ollama）的本地挂载流程。

---

## 💻 硬件配置推荐

为了获得流畅的全息渲染与 AI 推演体验，建议您的设备满足以下要求：

| 组件 | 最低配置 (演示模式) | 推荐配置 (全量算力模式) |
| :--- | :--- | :--- |
| **操作系统** | Windows 10 / 11 (64位) | Windows 11 (64位) |
| **处理器** | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| **内存 (RAM)** | 8GB | 16GB 甚至 32GB |
| **独立显卡** | 无需独立显卡 | **NVIDIA RTX 3060 (8GB显存) 及以上** |
| **硬盘空间** | 1GB 可用空间 | 30GB 可用 SSD 空间（需预留给大模型库） |

---

## 🛠️ 第一阶段：数字孪生总台安装

如果您只希望运行核心的地图交互与空间评价模块，请完成本阶段即可。

### 1. 安装 Python 环境
请前往 [Python 官方网站](https://www.python.org/downloads/) 下载并安装 **Python 3.10** 或更高版本。
> [!IMPORTANT]
> 在安装向导的第一步，务必勾选 **"Add Python to PATH"**（将 Python 添加到环境变量），否则终端将无法识别 `pip` 和 `python` 命令。

### 2. 克隆项目与安装依赖
打开您的命令行终端（CMD 或 PowerShell），依次执行：

```bash
# 1. 克隆代码仓库
git clone https://github.com/您的用户名/ultimateDESIGN.git

# 2. 进入项目根目录
cd ultimateDESIGN

# 3. 安装专属依赖包 (如果下载缓慢，请加上 -i https://pypi.tuna.tsinghua.edu.cn/simple)
pip install -r requirements.txt
```

### 3. 冒烟测试
依赖安装完成后，您可以直接启动应用进行测试：
```bash
streamlit run app.py
```
若浏览器成功打开网页且不报错，则第一阶段部署成功！

---

## 🧠 第二阶段：AI 引擎本地挂载 (硬核解锁)

由于云端缺乏高昂的 GPU 算力，真实的生成式预演与博弈对话需要调用您本地的显卡资源。

### 🧩 引擎 A：Ollama 大语言模型引擎
负责系统中的【04 博弈决策实验室】，推演不同角色的诉求对话。

1. **下载安装**：前往 [Ollama 官网](https://ollama.com/) 下载 Windows 安装包并完成安装。
2. **下载并运行模型**：打开终端，执行以下命令。系统会自动拉取为本平台深度适配的 Gemma 4 轻量化量化模型：
   ```bash
   ollama run gemma4:e2b-it-q4_K_M
   ```
3. **验证挂载**：在浏览器输入 `http://localhost:11434`，若显示 "Ollama is running"，说明挂载成功。

### 🎨 引擎 B：Stable Diffusion 视觉衍生引擎
负责系统中的【03 方案模拟实验室】，基于 ControlNet 约束生成街景修缮草图。

1. **下载安装**：推荐国内用户使用 [秋叶一键安装包 (Bilibili)](https://space.bilibili.com/12566101) 部署 SD WebUI。
2. **开放 API 接口（极其重要）**：
   - 打开您的 SD 启动器，在左侧菜单寻找“高级选项”或“启动参数”。
   - 勾选 **“启用 API (--api)”** 选项。
   - (如果是手动脚本启动，请在 `webui-user.bat` 中配置 `set COMMANDLINE_ARGS=--api --listen`)。
3. **模型准备**：建议提前在 SD 中下载好任意写实风格大模型（如 Realistic Vision）以及 ControlNet (Canny/Depth) 插件，以获得最佳渲染效果。
4. **验证挂载**：启动 SD 后，确认控制台输出中包含 `Running on local URL:  http://127.0.0.1:7860`。

---

## 🛡️ 最终联调启动

当上述两个底层引擎均在后台稳定运行时，回到项目目录重新启动总台：
```bash
streamlit run app.py
```

在系统主页，您将看到左侧的 **「底层算力设施调用监控」** 中，【多主体交互大语言模型】与【空间影像衍生网络】均亮起 **<span style="color:#4ADE80;">绿灯 (已联机)</span>**。
恭喜您，已解锁本平台的全部潜能！
