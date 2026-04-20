# 🏙️ 长春伪满皇宫微更新决策支持平台 - 安装与部署指南

## 📋 目录

1. [系统要求](#系统要求)
2. [快速开始（已有环境）](#快速开始已有环境)
3. [全新安装步骤](#全新安装步骤)
4. [项目结构说明](#项目结构说明)
5. [常见问题排查](#常见问题排查)
6. [分发给其他用户](#分发给其他用户)
7. [附录：依赖清单](#附录依赖清单)

---

## 系统要求

### 最低配置

| 组件 | 要求 |
|------|------|
| **操作系统** | Windows 10/11 (64位) |
| **处理器** | Intel i5 / AMD Ryzen 5 或更高 |
| **内存** | 8GB RAM (推荐 16GB+) |
| **硬盘空间** | 10GB 可用空间 |
| **Python 版本** | 3.10.x (通过 Conda 管理) |
| **Conda** | Anaconda 或 Miniconda |

### 推荐配置

| 组件 | 推荐 |
|------|------|
| **操作系统** | Windows 11 (64位) |
| **处理器** | Intel i7 / AMD Ryzen 7 或更高 |
| **内存** | 16GB RAM 或更高 |
| **显卡** | NVIDIA GPU (用于 AI 模型推理) |
| **硬盘空间** | 20GB SSD 可用空间 |
| **网络** | 稳定网络连接 (首次安装需下载依赖) |

---

## 快速开始（已有环境）

如果你已经安装了 Anaconda 并创建了 `gis_ai` 环境：

### 方式 1: 双击启动（最简单）

```
1. 进入项目文件夹
2. 双击运行: run.bat
3. 浏览器将自动打开 http://localhost:8501
```

### 方式 2: 命令行启动

```powershell
# 打开 Anaconda Prompt 或 PowerShell
cd <项目目录>

# 激活环境
conda activate gis_ai

# 启动应用
streamlit run app.py
```

### 方式 3: 使用便携启动脚本

```powershell
# 使用自动检测 Conda 路径的脚本
.\run_portable.bat
```

---

## 全新安装步骤

如果你是第一次使用本项目，请按以下步骤操作：

### 第 1 步: 安装 Anaconda

1. 访问 [Anaconda 官网](https://www.anaconda.com/products/distribution)
2. 下载 Windows 版本 (Python 3.10+)
3. 运行安装程序，建议安装到非系统盘 (节省 C 盘空间)
4. 安装时勾选 **"Add Anaconda to PATH"** (可选，但推荐)

### 第 2 步: 创建 Conda 环境

打开 **Anaconda Prompt** (在开始菜单搜索)，依次运行：

```powershell
# 创建新环境 (Python 3.10)
conda create -n gis_ai python=3.10 -y

# 激活环境
conda activate gis_ai
```

### 第 3 步: 安装项目依赖

```powershell
# 进入项目目录
cd <你的项目目录>

# 安装所有依赖 (可能需要 10-30 分钟，取决于网速)
pip install -r requirements.txt
```

**提示**: 如果下载速度慢，可以使用清华镜像源：

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 第 4 步: 验证安装

```powershell
# 运行环境检查脚本
python check_env.py
```

如果显示 `SUCCESS: Everything looks good!` 说明安装成功。

### 第 5 步: 启动应用

```powershell
# 方式 1: 使用启动脚本
.\run.bat

# 方式 2: 直接启动
streamlit run app.py
```

### 第 6 步: 配置环境变量（可选）

复制环境变量模板并填写你的 API 密钥：

```powershell
copy .env.example .env
notepad .env
```

在 `.env` 文件中填写：

```ini
# 百度地图 API 密钥 (用于 POI 和街景数据)
Baidu_Map_AK=你的API密钥
```

---

## 项目结构说明

```
ultimateDESIGN/
│
├── 📁 assets/                      # 静态资源 (图片、样式)
│   ├── 01_data_overview.png        # 模块预览图
│   ├── 02_strategy_library.png
│   ├── 03_digital_twin.png
│   ├── 04_urban_diagnosis.png
│   ├── 05_design_inference.png
│   ├── 06_llm_consultation_v2.png
│   ├── 07_system_config_v2.png
│   ├── 08_social_sentiment_v2.png
│   └── style.css                   # 全局样式
│
├── 📁 pages/                       # Streamlit 子页面
│   ├── 1_数据底座与规划策略.py      # 模块 1: 数据管理
│   ├── 2_数字孪生与全息诊断.py      # 模块 2: 可视化
│   ├── 3_AIGC设计推演.py           # 模块 3: AI 生成
│   └── 4_LLM博弈决策.py            # 模块 4: 决策推理
│
├── 📁 utils/                       # 工具模块
│   ├── __init__.py
│   └── geo_transform.py            # 坐标转换工具
│
├── 📁 data/                        # 数据文件夹 (需要手动创建)
│   └── 空间数据/
│       └── Boundary_Scope.geojson  # 项目边界数据
│
├── 📁 temp/                        # 临时文件/参考文献
│
├── app.py                          # 🏠 主入口文件
├── core_engine.py                  # 核心计算引擎
├── spider_engine.py                # 爬虫引擎
├── ui_components.py                # UI 组件库
│
├── get_poi.py                      # POI 数据采集
├── get_streetview.py               # 街景数据采集
├── get_traffic_poi.py              # 交通数据采集
│
├── cv_semantic_engine.py           # CV 语义分析引擎
├── run_deeplabv3.py                # DeepLabV3 推理脚本
│
├── requirements.txt                # Python 依赖清单
├── .env.example                    # 环境变量模板
├── .gitignore                      # Git 忽略规则
│
├── run.bat                         # 🚀 主启动脚本
├── run_portable.bat                # 便携启动脚本
├── setup_env.bat                   # 环境安装脚本
├── check_env.py                    # 环境检查脚本
│
└── README.md                       # 项目说明
```

---

## 常见问题排查

### Q1: 运行 run.bat 提示 "未找到 gis_ai Python 环境"

**原因**: Conda 环境未创建或路径不在检测列表中

**解决方法**:

```powershell
# 1. 检查环境是否存在
conda env list

# 2. 如果不存在，创建环境
conda create -n gis_ai python=3.10 -y

# 3. 如果路径特殊，修改 run.bat 添加你的路径
# 在 run.bat 第 34-67 行之间添加你的 Python 路径检查
```

### Q2: 依赖安装失败或下载速度慢

**原因**: 网络连接问题或 PyPI 服务器在国外

**解决方法**:

```powershell
# 使用清华镜像源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 重新安装
pip install -r requirements.txt

# 如果单个包安装失败，可以逐个安装
pip install streamlit pandas pydeck torch torchvision transformers
```

### Q3: Streamlit 启动后浏览器无法打开

**原因**: 端口被占用或防火墙阻止

**解决方法**:

```powershell
# 1. 检查端口是否被占用
netstat -ano | findstr :8501

# 2. 更换端口启动
streamlit run app.py --server.port 8502

# 3. 或在 run.bat 中修改端口 (第 134 行)
```

### Q4: 提示 "No module named 'xxx'"

**原因**: 依赖未正确安装

**解决方法**:

```powershell
# 1. 确认当前环境
conda activate gis_ai
python -c "import sys; print(sys.executable)"

# 2. 检查缺失的模块
python -c "import 模块名"

# 3. 重新安装
pip install --upgrade --force-reinstall 模块名
```

### Q5: POI/街景数据获取失败

**原因**: 百度地图 API 密钥未配置或无效

**解决方法**:

```powershell
# 1. 检查 .env 文件是否存在
dir .env

# 2. 编辑 .env 文件，填入有效的 API 密钥
notepad .env

# 3. 获取百度地图 API 密钥:
#    访问 https://lbsyun.baidu.com/
#    注册账号 -> 创建应用 -> 获取 AK
```

### Q6: AI 模型 (Stable Diffusion / Gemma) 无法连接

**原因**: 外部服务未启动

**解决方法**:

```powershell
# 1. 启动 Ollama (Gemma 4)
ollama serve

# 2. 启动 Stable Diffusion WebUI
#    导航到 SD WebUI 目录并运行 webui.bat

# 3. 检查服务状态
#    SD: 访问 http://localhost:7860
#    Ollama: 访问 http://localhost:11434
```

### Q7: 运行内存不足

**原因**: AI 模型占用过多内存

**解决方法**:

1. 关闭其他程序释放内存
2. 减少模型加载数量 (修改配置文件)
3. 考虑升级内存到 16GB+

---

## 分发给其他用户

### 方式 1: 完整分发（推荐）

1. **打包项目文件夹**
   ```powershell
   # 压缩整个项目目录
   Compress-Archive -Path "<你的项目目录>" -DestinationPath "微更新决策平台.zip"
   ```

2. **提供环境安装说明**
   将本文档一起分发给用户

3. **用户收到后**
   - 解压到任意目录
   - 安装 Anaconda (如未安装)
   - 运行 `setup_env.bat` 或按文档手动安装
   - 双击 `run.bat` 启动

### 方式 2: 使用 conda-pack 打包环境

适合需要完全隔离环境的场景：

```powershell
# 1. 安装 conda-pack
conda install -c conda-forge conda-pack

# 2. 打包 gis_ai 环境
conda pack -n gis_ai -o gis_ai_env.tar.gz

# 3. 解压到目标机器
mkdir <目标路径>\gis_ai_env
cd <目标路径>\gis_ai_env
tar -xzf gis_ai_env.tar.gz

# 4. 激活环境
<目标路径>\gis_ai_env\Scripts\activate

# 5. 运行项目
cd <你的项目目录>
python -m streamlit run app.py
```

### 方式 3: Docker 容器化（高级用户）

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

构建和运行：

```powershell
docker build -t micro-renewal-platform .
docker run -p 8501:8501 micro-renewal-platform
```

---

## 附录：依赖清单

### 核心框架

| 包名 | 版本 | 用途 |
|------|------|------|
| streamlit | latest | Web 应用框架 |
| streamlit-lottie | latest | Lottie 动画支持 |
| streamlit-folium | latest | 地图可视化集成 |

### 数据处理

| 包名 | 版本 | 用途 |
|------|------|------|
| pandas | latest | 数据处理与分析 |
| geopandas | latest | 地理空间数据处理 |
| pydeck | latest | 3D 可视化 |
| numpy | latest | 数值计算 |

### AI/ML

| 包名 | 版本 | 用途 |
|------|------|------|
| torch | latest | 深度学习框架 |
| torchvision | latest | 计算机视觉工具 |
| transformers | latest | HuggingFace 模型库 |

### 爬虫与采集

| 包名 | 版本 | 用途 |
|------|------|------|
| selenium | latest | 浏览器自动化 |
| playwright | latest | 现代爬虫框架 |
| webdriver-manager | latest | 浏览器驱动管理 |
| beautifulsoup4 | latest | HTML 解析 |
| requests | latest | HTTP 请求库 |

### 文档处理

| 包名 | 版本 | 用途 |
|------|------|------|
| markitdown | latest | 多格式文档转 Markdown |
| mammoth | latest | Word 文档处理 |
| python-docx | latest | Word 文档创建/编辑 |
| pdfminer.six | latest | PDF 文本提取 |
| pymupdf | latest | PDF 高级处理 |
| pypdf | latest | PDF 基础操作 |
| lxml | latest | XML/HTML 解析 |

### 可视化与其他

| 包名 | 版本 | 用途 |
|------|------|------|
| plotly | latest | 交互式图表 |
| folium | latest | Leaflet 地图 |
| pillow | latest | 图像处理 |
| jieba | latest | 中文分词 |
| openpyxl | latest | Excel 文件处理 |
| python-dotenv | latest | 环境变量管理 |

---

## 📞 技术支持

如遇到本文档未涵盖的问题：

1. 检查 [README.md](./README.md) 获取项目概述
2. 运行 `python check_env.py` 诊断环境状态
3. 查看 Streamlit 终端输出的错误信息
4. 联系项目维护者

---

**最后更新**: 2026-04-18
**适用版本**: v1.0
**维护者**: 项目团队
