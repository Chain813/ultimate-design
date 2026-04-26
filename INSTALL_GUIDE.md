# 安装与本地引擎部署指南

本文档说明如何在本地运行项目，以及如何挂载第 03 页和第 04 页需要的 AI 引擎。

## 1. 环境要求

| 项目 | 轻量演示模式 | 全量本地模式 |
| --- | --- | --- |
| 操作系统 | Windows 10/11、macOS、Linux | Windows 10/11 优先 |
| Python | 3.10 到 3.12 | 3.10 到 3.12 |
| 内存 | 8GB 以上 | 16GB 以上 |
| GPU | 不需要 | 建议 NVIDIA RTX 3060 8GB 以上 |
| AI 服务 | 不需要 | Stable Diffusion WebUI、Ollama |

## 2. 安装项目依赖

```powershell
git clone https://github.com/Chain813/ultimateDESIGN.git
cd ultimateDESIGN

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

国内网络较慢时可使用镜像：

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 3. 启动 Streamlit

```powershell
streamlit run app.py
```

默认访问：

```text
http://localhost:8501
```

如果端口被占用，可指定其他端口：

```powershell
streamlit run app.py --server.port 8502
```

## 4. Stable Diffusion WebUI

Stable Diffusion WebUI 用于第 03 页实时生成更新设计图景。

启动要求：

- WebUI 本地服务地址为 `http://127.0.0.1:7860`
- 启动参数必须包含 `--api`
- 推荐提前准备写实或建筑表现相关模型

手动启动时示例：

```text
set COMMANDLINE_ARGS=--api
```

启动后可在浏览器打开：

```text
http://127.0.0.1:7860
```

## 5. Ollama / Gemma

Ollama 用于第 04 页 LLM 多主体协商。

安装 Ollama 后运行：

```powershell
ollama run gemma4:e2b-it-q4_K_M
```

验证地址：

```text
http://127.0.0.1:11434
```

如果模型名称需要调整，可在第 04 页侧边栏修改模型标签。

## 6. 当前代码结构

```text
src/
├── config/
│   ├── paths.py              # 数据、文档、静态资源路径
│   ├── loader.py             # 配置加载
│   └── runtime.py            # 运行时配置
├── engines/
│   ├── spatial_engine.py     # 空间测度
│   ├── diagnostic_engine.py  # 地块诊断与政策矩阵
│   ├── aigc_engine.py        # Stable Diffusion 调用
│   ├── rag_engine.py         # 政策知识库检索
│   ├── llm_engine.py         # Ollama 对话
│   └── core_engine.py        # 旧导入兼容出口
├── ui/
│   ├── design_system.py      # 统一页面组件
│   ├── chart_theme.py        # 统一图表主题
│   └── ui_components.py      # 导航、状态提示和兼容导出
└── utils/
    ├── document_generator.py # Word 成果导出
    ├── service_check.py      # SD / Ollama 探活
    ├── daemon_manager.py     # 本地守护进程控制
    └── geo_transform.py      # 坐标转换
```

更完整的结构说明见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)。

## 7. 验证命令

```powershell
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
python -m pytest tests/ -q
python tools/startup_smoke.py
```

如果没有完整 AI 环境，`pytest` 中与外部服务有关的测试可能需要根据本地环境调整；页面级语法检查和启动冒烟测试应优先通过。

## 8. 常见问题

| 问题 | 处理方式 |
| --- | --- |
| `streamlit` 命令不存在 | 确认虚拟环境已激活，并重新执行 `pip install -r requirements.txt` |
| 第 03 页显示 SD 未就绪 | 确认 WebUI 已用 `--api` 启动并监听 7860 |
| 第 04 页显示 Gemma 未就绪 | 确认 Ollama 正在运行，且模型标签与页面侧边栏一致 |
| 页面找不到 PDF | `docs/` 是本地资料目录，GitHub 默认不上传，需要在本机保留对应文件 |
| 上传 GitHub 文件过大 | 检查是否误加入 `.runtime-packages/`、PDF、原始影像或日志 |
