# 开发者指南

## 1. 本地开发环境

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. 环境变量

1. 复制 `.env.example` 为 `.env`
2. 按真实值填写

| 变量名 | 说明 |
| --- | --- |
| `Baidu_Map_AK` | 百度地图 API Key（仅本地保存，禁止提交到仓库） |

## 3. 数据目录约定

- `data/`：业务主数据目录
- `data/shp/`：地理边界、地块等空间文件
- `data/streetview/`：街景原图（已在 `.gitignore` 中排除）
- `data/rag_knowledge.json`：RAG 检索知识库

建议：
- 原始大文件放在 `data/raw/`（如需新增，请在 `.gitignore` 中处理）
- 清洗后可复用数据放在 `data/` 根目录并保持英文命名

## 4. 模型服务依赖

本项目完整功能依赖两个本地服务：

1. Ollama（默认 `http://127.0.0.1:11434`）
   - 示例：`ollama run gemma4:e2b-it-q4_K_M`
2. Stable Diffusion WebUI API（默认 `http://127.0.0.1:7860`）
   - 启动时需开启 `--api`

服务地址可在 `config.yaml` 中调整。

## 5. 常用质量命令

```bash
ruff check .
pytest -q
python tools/check_env.py
python tools/startup_smoke.py
```

## 6. 提交前自动检查（pre-commit）

项目已提供 `.pre-commit-config.yaml`，可在本地启用提交前自动检查：

```bash
pip install -r requirements.txt
pre-commit install
```

手动执行一次全部钩子：

```bash
pre-commit run --all-files
```

当前默认钩子：
- `ruff check .`
- `pytest -q`

## 7. 常见问题排障

- **端口被占用**
  - 检查 11434/7860 是否被其他进程占用，或修改 `config.yaml`。
- **页面加载正常但模型调用失败**
  - 先确认 Ollama / SD WebUI 是否启动，再检查 URL 和超时配置。
- **依赖安装失败**
  - 建议使用 Python 3.10，执行 `pip install --upgrade pip` 后重试。
- **数据文件缺失**
  - 运行 `python tools/check_env.py` 查看缺失清单。
