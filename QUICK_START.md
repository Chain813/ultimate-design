# 🚀 快速启动指南

👈 **[返回项目主页 (Back to Home)](README.md)**

## 3 分钟快速开始

### 前提条件
- ✅ 已安装 Anaconda/Miniconda
- ✅ 已创建 `gis_ai` 环境

### 启动步骤

#### 第 1 步：安装依赖（仅首次）

```powershell
# 打开 Anaconda Prompt
cd <你的项目目录>

# 方式 1: 使用自动安装脚本
```.\setup_env.bat

# 方式 2: 手动安装
conda activate gis_ai
pip install -r requirements.txt
```

#### 第 2 步：启动应用

```powershell
# 方式 1: 双击启动 (最简单)
双击 run.bat

# 方式 2: 命令行启动
streamlit run app.py
```

#### 第 3 步：访问应用

浏览器自动打开: **http://localhost:8501**

---

## 常用命令速查

| 任务 | 命令 |
|------|------|
| **启动应用** | `.\run.bat` |
| **安装依赖** | `.\setup_env.bat` |
| **检查环境** | `python tools/check_env.py` |
| **激活环境** | `conda activate gis_ai` |
| **更新依赖** | `pip install -r requirements.txt --upgrade` |
| **查看已安装包** | `pip list` |
| **更换端口** | `streamlit run app.py --server.port 8502` |

---

## 常见问题快速修复

| 问题 | 解决方法 |
|------|---------|
| ❌ 找不到环境 | 运行 `.\setup_env.bat` |
| ❌ 依赖缺失 | 运行 `pip install -r requirements.txt` |
| ❌ 端口被占用 | 使用 `--server.port 8502` |
| ❌ 下载太慢 | 使用清华镜像源 (见下方) |

### 使用清华镜像源加速下载

```powershell
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt
```

---

## 贡献流程（开发 -> 检查 -> 提交）

```powershell
# 1) 安装依赖
pip install -r requirements.txt

# 2) 启用本地提交前检查（仅需一次）
pre-commit install

# 3) 开发并本地验证
ruff check .
pytest -q
python tools/startup_smoke.py

# 4) 提交（会自动触发 pre-commit）
git add .
git commit -m "your message"
```

CI 会在远端并行执行 `lint`、`test`、`smoke` 三项检查，请确保本地先通过。

---

## 项目模块

| 模块 | 功能 | 入口 |
|------|------|------|
| 🔬 01 数据底座 | 指标总览、MPI 评估、文档管理 | `pages/1_数据底座与规划策略.py` |
| 🏙️ 02 全息诊断 | 数字孪生、交通潮汐、情感分析 | `pages/2_数字孪生与全息诊断.py` |
| 🎨 03 AIGC推演 | 风貌修复、空间织补、方案生成 | `pages/3_AIGC设计推演.py` |
| ⚖️ 04 LLM决策 | 利益相关者协商、政策推演 | `pages/4_LLM博弈决策.py` |

---

**详细文档**: 请参阅 [INSTALL_GUIDE.md](./INSTALL_GUIDE.md)
