<p align="center">
  <a href="README.md">简体中文 🇨🇳</a> | <a href="README_EN.md">English 🇬🇧</a>
</p>

<h1 align="center">循证导向的长春铁北历史街区微更新决策支持平台</h1>

<p align="center">
  <img src="https://img.shields.io/badge/学科定位-城乡规划%20%2F%20城市科学-blue.svg" alt="Subject">
  <img src="https://img.shields.io/badge/核心方法-循证决策%20%2F%20多模态评估-FF4B4B.svg" alt="Methodology">
  <img src="https://img.shields.io/badge/技术框架-数字孪生%20%2F%20生成式AI-818cf8.svg" alt="UI">
  <img src="https://img.shields.io/badge/模型支撑-Stable%20Diffusion%20%2F%20LLM-purple.svg" alt="Engines">
</p>

## 🏙️ 项目愿景与科学定位

本平台（原 **ultimateDESIGN** 数字孪生系统）是针对长春市宽城区铁北历史文化街区及伪满皇宫周边区域开发的**循证式空间微更新辅助方案决策系统**。

平台旨在通过整合多源异构大数据，解决传统城市更新中“感知主观化”、“评价定性化”与“博弈不透明”的痛点。通过深度融合 **3D 空间数字孪生**、**计算机视觉 (CV)** 与 **生成式大模型 (AIGC/LLM)** 技术，为规划师、政府管理部门及公众提供可量化、动态化的更新方案预演与协商底座。

---

## ✨ 核心科研实验室模块

### 1. 📊 空间资产综合测度（01 策略实验室）
- **MPI 指标体系 (Multi-dimensional Potential Index)**：基于 AHP 层次分析法的多维度评价模型，通过构建判断矩阵，将专家定性经验转化为定量数学权重，实现对更新单元潜力的科学分级。
- **策略语义萃取引擎**：集成跨模态解析算法，实现对上位保护规划文本（如《名城保护条例》）的语义精准降维与关键导则提取。

### 2. 🌐 数字孪生与全息诊断（02 诊断实验室）
- **多指标空间沙盘**：基于 WebGL 引擎构建，实现对绿视率 (GVI)、天空开阔度 (SVF)、空间围合度等街道空间品质因子的 3D 全息映射。
- **人本要素感知**：融合高德 POI 实测分布、职住交通潮汐与社会感知 (UGC) 情绪极值，构建反映“物质-社会”双重属性的城市全息图谱。

### 3. 🎨 空间风貌图景推演（03 方案模拟实验室）
- **基于先验约束的生成式预演**：利用局部特征约束网络 (ControlNet)，在保留历史建筑骨架纹理的前提下，模拟不同修缮干预下的风貌演变。
- **规划算子调控矩阵**：通过动态调节景观介入度、历史锚定力等核心算子，实现方案生成的参数化控制。

### 4. ⚖️ 利益主体协商决策（04 博弈决策实验室）
- **多代理人博弈模拟**：引入大语言模型 (LLM)，模拟“公众权益代表、市场投资主体、规划编制专家”三方角色的动态利益交锋。
- **共识收敛机制**：基于政策 RAG (检索增强) 机制，自动对博弈结论进行合规性校核并生成最终政策建议。

### 5. 🎯 更新设计成果展示（05 成果展示实验室）
- **循证文书自动化流转**：聚合各实验室测度、推演与博弈共识数据，一键生成符合规范的结构化 Markdown/PDF 行政文书。
- **4D 时空方案全景漫游**：集成“留改拆”管线透视与 AIGC 重绘视界，提供跨尺度的微更新数字化交付方案。

---

## 📂 模块化分层架构

```text
ultimateDESIGN/
├── app.py                      # 系统控制总台 (核心导航与状态监视)
├── pages/                      # 5大核心实验室 (资产测度/全息诊断/方案模拟/博弈决策/成果展示)
├── src/                        # 核心解析引擎包
│   ├── engines/                # 空间测度核心、CV 语义提取、NLP 情感分类引擎
│   ├── ui/                     # 统一设计系统 (Apple/Cyber Aesthetic)
│   └── utils/                  # 动态坐标转换与时空投影组件
├── data/                       # 数据底座资产
│   ├── shp/                    # 法定红线边界与重点地块 GeoJSON
│   └── streetview/             # 采集测区全景影像 (作为 CV 引擎输入)
├── docs/                       # 学术文档、规格书、法律法规文件汇编
├── tools/                      # 环境自检与数据质量冒烟测试工具
└── .gitignore                  # 数据安全与隐私脱敏忽略配置
```

---

## 🚀 部署与体验指南 (Deployment Guide)

本项目支持两种运行模式，以平衡展示便捷性与计算完整性：

### 1. 🌐 云端演示模式 (Cloud Demo)
若您通过 Streamlit Community Cloud 访问，系统将自动进入**演示模式**。由于云端缺乏 GPU 算力，AIGC 推演与 LLM 博弈将展示预置的高质量成果，而地图交互与空间评价算法保持 100% 实时运行。

### 2. 💻 本地全算力模式 (Local Perfect Experience)
为解锁实时 AIGC 图像生成与真实 LLM 对话，请在本地部署。
(👉 **[初学者请点击：保姆级手把手部署教程](#newbie-guide-cn)**)

- **算力要求**：建议 NVIDIA RTX 3060 (8GB 显存) 及以上。
- **环境准备**：
    1. 启动 [Ollama](https://ollama.com/) 并运行 `gemma4:e2b-it-q4_K_M`。
    2. 启动 **Stable Diffusion WebUI** 并添加 `--api` 参数。
- **快速启动**：
    ```bash
    pip install -r requirements.txt
    streamlit run app.py
    ```

---

<a name="newbie-guide-cn"></a>

## 🐣 新手保姆级部署教程 (Step-by-Step)

如果您对编程一无所知，请按照以下步骤操作，即可在您的电脑上运行本项目：

### 第一步：准备环境（这是基础）
1.  **安装 Python**：前往 [Python.org](https://www.python.org/downloads/) 下载并安装。**注意**：安装时务必勾选 "Add Python to PATH"（添加到路径）。
2.  **获取本项目代码**：点击本页面顶部的绿色按钮 `Code` -> `Download ZIP`，下载并解压到您的电脑。

### 第二步：安装“运行插件”
1.  在项目文件夹的空白处，按住键盘上的 `Shift` 键并点击鼠标右键，选择“在此处打开 PowerShell 窗口”或“在终端中打开”。
2.  输入以下命令并按回车（这会自动安装本项目需要的所有功能组件）：
    ```bash
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```

### 第三步：启动 AI 智能大脑 (Ollama)
1.  下载并安装 [Ollama](https://ollama.com/)。
2.  安装完成后，打开您的电脑终端（按 Win+R 输入 cmd 回车），输入：
    ```bash
    ollama run gemma4:e2b-it-q4_K_M
    ```
    *第一次运行会自动下载模型，请耐心等待。*

### 第四步：启动风貌渲染引擎 (Stable Diffusion)
1.  建议使用“秋叶 Stable Diffusion 一键包”。
2.  **关键设置**：在启动器中找到“启用 API”选项并勾选。如果您是手动启动，请在 `webui-user.bat` 的参数中加入 `--api`。
3.  点击“一键启动”，看到浏览器弹出 SD 页面即可。

### 第五步：见证奇迹的时刻
回到第二步打开的那个黑窗口，输入：
```bash
streamlit run app.py
```
稍等片刻，您的浏览器会自动弹出本项目的数字孪生界面。

---

## 📚 进阶文档导航 (Advanced Documentation)

如果您希望深入了解本系统的底层逻辑或获取完整的部署帮助，请查阅以下深度文档：
- ⚡ **[快速启动指南 (3分钟体验教程)](QUICK_START.md)**：包含纯净版体验与全量算力版体验的双模式路线。
- 🖥️ **[深度安装与核心引擎部署指南](INSTALL_GUIDE.md)**：详尽解读 Python 环境搭建以及 Stable Diffusion、Ollama 本地挂载流程。
- 📤 **[GitHub 上传与云端上线指南](GITHUB_UPLOAD_GUIDE.md)**：针对小白的 Streamlit Community Cloud 一键部署教学。

---

## 🛠️ 核心开发组件
- **动态坐标转换器** (`src/utils/geo_transform.py`)：集成 BD09 / GCJ02 / WGS84 工业级转换算法，支撑多源数据对齐。
- **AHP 决策矩阵**：内置于 `pages/1_数据底座与规划策略.py`，支持专家权重的实时重算。
- **WebGL 渲染管线**：基于 Deck.GL 实现百万级建筑要素的毫秒级渲染。

---

## ⚠️ 使用声明

本项目仅供学术研讨、毕业论文展示及长春城市科学研究使用。项目数据涉及经脱敏处理的社会感知信息与高德 API 快照，严禁用于任何商业开发活动。

---

**循证导向 · 科学织补 · 智慧决策**
