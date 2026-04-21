# 项目结构优化说明

## 1. 目标

本轮结构优化聚焦“在不破坏现有功能的前提下，提升可读性与可维护性”：

- 统一路径管理，避免页面和脚本散落硬编码路径
- 收敛导入链路，减少运行目录依赖（cwd 依赖）
- 明确工程分层，降低后续重构成本

## 2. 当前推荐目录分层

```text
ultimateDESIGN/
├── app.py                         # Streamlit 主页入口
├── pages/                         # 业务页面
├── src/
│   ├── config/                    # 配置与路径抽象层
│   │   ├── runtime.py             # project_root/resolve_path
│   │   ├── paths.py               # 统一数据/资源路径常量
│   │   └── __init__.py
│   ├── engines/                   # 业务引擎（NLP/CV/LLM/AIGC/Spider）
│   ├── ui/                        # UI 组件层
│   └── utils/                     # 通用工具层
├── tools/                         # 运维与离线任务脚本
├── tests/                         # pytest 测试
├── docs/                          # 项目文档
└── .github/workflows/             # CI 流水线
```

## 3. 本次已落地的结构改造

### 3.1 新增统一路径模块

- 新增 `src/config/paths.py`
  - `ROOT_DIR`, `DATA_DIR`, `SHP_DIR`, `ASSETS_DIR`, `STATIC_DIR`
  - `DATA_FILES`（POI/Traffic/NLP/GVI/Points/RAG）
  - `SHP_FILES`（Boundary/Plots/Buildings）
- `src/config/__init__.py` 统一导出，供页面/引擎直接引用

### 3.2 页面路径硬编码收敛

- `pages/1_数据底座与规划策略.py`
  - 地块 JSON 读取切换为 `SHP_FILES["plots"]`
  - 物理底座管理 CSV 路径切换为 `DATA_FILES[...]`
- `pages/2_数字孪生与全息诊断.py`
  - 地图模板改为 `ASSETS_DIR / "map3d_standalone.html"`
  - 数据读取改为 `DATA_FILES[...]`
  - shp 路径改为 `SHP_FILES[...]`
  - 修复本地导入错误：`from core_engine` -> `from src.engines.core_engine`
  - 去除 `sys.path.append(...)` 的隐式路径注入依赖

### 3.3 配置读取路径稳定化

- `src/engines/core_engine.py` 已采用 `resolve_path(...)` 读取 `config.yaml` 与 RAG 文件，避免 cwd 漂移问题

## 4. 结构规范（后续建议遵循）

1. **路径规范**
   - 页面/引擎内禁止再写 `data/...`、`assets/...` 字面路径
   - 一律从 `src.config` 导入路径常量

2. **导入规范**
   - 使用绝对导入（`from src....`）
   - 禁止 `sys.path.append` 临时注入

3. **脚本规范**
   - `tools/` 内脚本以仓库根为基准路径
   - 读写路径优先通过 `Path` 对象处理

4. **文档规范**
   - 业务说明放 `docs/PROJECT_DETAILED_SPEC.md`
   - 开发/运维流程放 `docs/DEVELOPER_GUIDE.md`

## 5. 后续可继续执行的结构化升级（可选）

- 将 `pages/` 内数据处理逻辑进一步下沉至 `src/engines/`（页面只做编排和渲染）
- 将 `tools/` 中与业务强耦合脚本逐步改造成可导入服务模块
- 引入 `src/domain/`（数据模型）和 `src/services/`（应用服务）实现更严格分层
