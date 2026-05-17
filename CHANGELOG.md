# 更新日志 (Changelog)

本项目所有的核心重构与功能更新将记录在此。

---

## [v4.0.0] - 2026-05-17
### 🛠️ 工作流与 AI 技能 (Skills) 增强
* **自动更新日志技能**：在本项目根目录 `.gemini/skills/update_changelog.md` 中新增了一项定制技能，强制约束 AI 以后每次在本项目中执行任务时，必须自动在 `CHANGELOG.md` 中记录更新。
* **全局 Superpower 技能引擎**：从 GitHub (`anthonylee991/gemini-superpowers-antigravity`) 下载并部署了完整的 Superpower 开源工作流引擎作为 Gemini 的全局级 Skill，为后续进行复杂的计划制定、并行开发和测试驱动开发提供了坚实的理论和流程保障。

### 🚀 核心架构升级 (Stage 13 & 14 重构)
* **移除了重量级的外部渲染框架**：彻底弃用了在本地运行不稳定、极易崩溃的 Stable Diffusion + ControlNet 渲染管线，以及依赖 Node.js 环境的 HyperFrames 视频框架。
* **人机协同制图工作流 (Stage 13)**：
  * **Python 高精度直出底图**：在 `pages/13_成果表达.py` 中，支持直接调用 `GeoPandas` 与 `Matplotlib` 对 `data/gis` 中的路网、建筑和用地色块进行矢量级精度出图，百分百保障空间逻辑。
  * **Web LLM 重绘规范**：提供针对网页端 Gemini/ChatGPT 的“防篡改提示词”，实现低技术门槛的高保真美术渲染。
  * **自动红头图框引擎**：新增 `src/engines/frame_generator.py` (基于 PIL)，可将用户传回的美化图自动嵌套标准的工程 A3 图框（含图纸编号、中英标题、动态 AI 图面摘要和自动比例尺）。
* **智能分镜与导演脚本系统 (Stage 14)**：
  * 弃用了机械的自动录屏逻辑，转而通过 `stage_data_bus` 动态抓取前序阶段落定的真实评估指标（如 MPI 排行、设计愿景、交通策略等）。
  * 在 `pages/14_视频生成.py` 中自动拼接生成一份精确到分秒的《全流程录屏导演分镜脚本》Markdown 文档，为用户手工录制高质量解说视频提供保姆级指引。
* **精简了项目体积与复杂度**：
  * 移除了 `tools/video_generator/composer` 目录及冗余的 npm 依赖。
  * 移除了项目中大量遗留的 SD 调用脚本。

### 🔒 安全与仓库管理优化
* **全面硬化敏感信息泄露防线**：
  * 扫描并验证了本地环境，确保所有实际运行的百度 AK 和 DeepSeek API 密钥均安全存放在外部忽略文件 `.env` 中，代码没有任何硬编码的敏感信息。
  * **Git 历史脏数据擦除**：检测到过往开发 Commit 中曾不慎硬编码暴露过百度地图 AK 与 DeepSeek 接口密钥。使用专业的 `git-filter-repo` 工具在项目所有的 **107 个历史 Commit** 中全面覆写检索，对上述两组敏感字符串进行了无损替换（用 `YOUR_BAIDU_MAP_AK` 与 `YOUR_DEEPSEEK_API_KEY` 完美覆盖），并强制推送到 GitHub 覆盖，彻底杜绝了因历史 Commit 被追溯而导致的安全泄露风险。
  * **Claude Code 本地配置安全隔离**：将 Claude Code 本地授权配置文件所在的 `.claude/` 文件夹添加至 `.gitignore` 进行安全忽略；并使用 `git-filter-repo --path .claude/ --invert-paths` 命令，**将历史 Commit 记录中已提交的 `.claude/settings.local.json` 彻底抹去**，同时已在云端 GitHub 仓库完成覆盖，百分之百保证其不在公共网络上可见。
  * 升级 `.gitignore` 配置，新增了 `.gemini/`（AI 代理缓存）、`scratch/`（临时便签空间）和 `output/`（高保真渲染图等大文件）的忽略规则，防止由于误操作而将冗余数据和缓存上传至 GitHub。

### 📚 文档体系更新
* 刷新了 `WORKFLOW.md`、`README.md` 和 `README_EN.md`，将管线描述与新版的轻量化“人机协同”理念完全对齐。
* 更新了 `GLOSSARY.md` 核心术语库，移除了 ControlNet 等概念，增加了 Python 矢量直出、智能分镜等新词汇。

---

## [v3.0.0] - 2026-05-10
### 🚀 数据与制图管线 (GIS-to-AIGC)
* **矢量裁切引擎**：`scripts/clip_city_data.py` 实现对城市级大规模路网 (4.1GB) 和轨交数据的秒级精准裁切，并将研究范围限定于 150 公顷。
* **自动光栅化服务**：将裁切后的 GeoJSON 数据自动转化为 ControlNet 引导图 (Road/Landuse/Satellite Base)。
* **国标用地色值**：`src/engines/spatial_engine.py` 支持 10 类国标用地分类颜色的标准映射。
* **数据目录结构调整**：确立了 `data/gis/` 与 `data/csv/` 的核心架构，由 `src/config/paths.py` 全局接管路径注册。

---

## [v2.0.0] - 2026-04-20
### 🧠 AI 推演引擎升级
* 引入了基于 `stage_data_bus.py` 的跨阶段数据总线机制，彻底解决多页面的状态隔离问题。
* 构建了 `QualityAssessor` 双重评估体系，采用 Gemma 对画面完整性把关，使用 DeepSeek API 评估专业合理性。
* 建立了基于 AHP（层次分析法）的 MPI（微更新潜力指数）评估模型，驱动核心地块的靶向识别。

---

## [v1.0.0] - 2026-03-01
### 🎉 初始发布
* 发布 `ultimateDESIGN` 城乡规划多模态 AI 平台 1.0 版。
* 初步完成 15 个阶段 (Stage 00-14) 的 Streamlit UI 框架搭建。
* 实现了基础的 Deck.GL 3D 建筑底座交互展示能力。
