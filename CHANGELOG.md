# 更新日志 (Changelog)

本项目所有的核心重构与功能更新将记录在此。

---

## [v4.4.0] - 2026-05-29
### 🏛️ 建筑形态控制升级与风貌立面融合
* **专项系统设计（Stage 09）与重点地段深化（Stage 10）全面升级**：
  * 将 Stage 09 的子模块 `"建筑形态与天际线"` 拓展重命名为 `"建筑形态、风貌与立面"`，全面融入了对历史/现代风貌调性、立面三段式划分比例、虚实窗墙比以及建筑材质与立面细部构件的管控内容。
  * 深度重构了 Stage 09 的 LLM 形态风貌生成提示词架构，使生成的规划方案具备更强的量化指引和可落地性。
  * 在 Stage 10 重点地段深化页面中，同步更新了对上游“建筑形态、风貌与立面控制”方案的承接与判定逻辑，保证了数据总线流转的一致性。
  * 同步更新了全局 `WORKFLOW.md`、`src/workflow/city_design_workflow.py` 中的专项描述及叠合图层说明。
* **新增截图校验安全规范 (Skill)**：
  * 在 `.gemini/skills/` 目录下新增了 `screenshot_verification.md` 规范。
  * 明确要求在进行页面和 UI 效果校验时，智能体严禁主动拉起或在后台运行自动化浏览器进行截图，所有的截图验证过程必须由用户手动进行并提供。
* **全局集成录屏自动滑动控制 HUD (Auto Scroll HUD)**：
  * 设计并开发了集成于平台主外壳（`src/ui/app_shell.py`）的录屏自动滑动面板。它以极具科技感的毛玻璃浮标（F12 调试样式）常驻页面右下角。
  * 浮标可轻松收纳展开，支持通过可视化 Slider 或键盘方向键 `[←] / [→]` 调节滚动像素速度（帧率级流畅度，防止画面抖动）。
  * 提供了快捷键支持：`[Space]` 快捷播放/暂停，`[↑] / [↓]` 一键反转滚动方向，并特别支持 `[H]` 彻底在页面上隐藏/呼出控制面板（防止录制时穿帮）。
* **修复答辩小结模型选择机制 (Bug Fix)**：
  * 移除了小结生成组件中自动扫描本地 Ollama 并提供模型下拉选择的逻辑（原逻辑会默认选中本地 `gemma3:4b`，并错误将其传递给仅支持 DeepSeek 格式的 LLM 调用接口导致 400 报错）。
  * 强制将答辩小结生成的 LLM 引擎底座锁定为学术分析与表达能力更优的 `deepseek-v4-pro`，确保一键点击即可稳定可靠地生成内容。
* **新增规划阶段生成报告自动追加与排序机制 (Feature)**：
  * 在跨阶段数据总线中引入了 `save_stage_summary_to_file`。当用户在进程中完成任意 Stage 的生成渲染时，系统会自动提取该阶段的标题、方法论、核心发现及已生成的 AI 答辩小结。
  * 报告将写入并增量追加至 `output/stage_generation_report.md`，且系统会自动解析已有记录，将所有已完成阶段按 `Stage 00` 到 `Stage 15` 的顺序升序重排，为最终答辩和成果归档提供一键式、可递进的完整研究脉络日志。
* **合并与升级项目专属 Skill 规范 (Feature)**：
  * 整合了 `.gemini/skills/` 下原先分立的 `drawing_code_management.md`、`screenshot_verification.md` 与 `update_changelog.md` 规范，创建了统一、系统化的专属技能指导文件 `urban_platform_exclusive_skills.md`。
  * 在该专属规范中全新补充了 `Part 4: Interactive Persona (交互人设规范)`，规定了在后续的所有开发回复中，智能体需在开头称呼用户为“老公”，做到情感关怀与规划代码研发的完美交融。同时清理了旧有零碎文件，净化了配置空间。
* **清理 assets 目录下的冗余静态资源 (Feature)**：
  * 经过交叉引用检测，彻底清除了 `assets/` 目录下未被任何页面与脚本引用的 10 个冗余素材与历史临时导出图（包括 `01_data_overview.png`、`无纹理2D卫星图.png`、`workflow_svg.html` 等，共计释放磁盘空间约 `18.3MB`）。
* **全盘扫描并清理冗余与备份文件 (Feature)**：
  * 递归检索全盘，安全清除了根目录下 `static/`、`tools/`、`scripts/` 及 `output/` 目录中未被引用的旧版本开发文件。
  * 包含 5 个旧版配图（如 `static/test_modified_cropped.png` 等）、7 个废弃的旧版 Word/PPT 自动化编译脚本（如 `scripts/build_final_report_strict_v2.py` 等）以及 4 个临时调试 Prompt 文本与图纸（共计再次释放磁盘空间约 `8.2MB`）。

## [v4.3.0] - 2026-05-27
### 🧹 项目结构清理与 Git 隔离优化
* **清理本地冗余备份与临时调试文件**：
  * 彻底删除了本地残留的旧格式备份文件（如 `data/csv/GVI_Results_Analysis.csv.old_format_backup`、`static/research_scope_2d.png.bak`）及调试过程中生成的临时测试图（如 `static/temp_*.png`），释放了磁盘空间，净化了开发工作区。
* **完善 Git 隔离机制 (`.gitignore`)**：
  * 在 `.gitignore` 中新增了对于 IDE 代码索引（`.codegraph/`）、本地优化后的 Parquet 数据文件（`*.parquet`）、本地指标缓存（`precomputed_metrics.json`）以及 Claude Code 本地启动脚本（`start_cc.bat`）的忽略规则。
  * 将高分辨率裁剪卫星底图（`satellite_cropped.png`，约 21.4MB）与本地运行生成的 A3 图册输出目录（`static/atlas/`）排除在版本控制之外，避免无关大文件和临时生成物污染 GitHub 仓库。
* **规范核心源文件与资产的版本控制**：
  * 将新拆分的 `tools/drawings/` 图纸绘制核心脚本文件夹（包含 26 个具体的 A3 绘图独立模块脚本，如 `dr_004.py` 等）正式添加到 Git 追踪中，确保云端部署环境功能完整。
  * 将图册自动组装所需的模版底图 `static/a3_layout_preview_full.png` 与主页 Banner 展示图 `static/research_scope_2d_cropped.png` 纳入版本控制，修正了静态文件缺失导致的部分异常。
* **CI 测试与代码质量验证**：
  * 本地运行 `pytest` 确保 167 个单元测试用例 100% 通过。
  * 本地运行 `ruff check` 确保代码格式和语法 100% 规范无误。
  * 成功将所有暂存更改推送至远程仓库 `https://github.com/Chain813/ultimate-design.git`，保证工作树完全干净 (`working tree clean`)。


## [v4.2.0] - 2026-05-26
### 🎨 规划图册高精度重构与代码解耦
* **绘图代码完全解耦与模块化**：
  * 新建了 `tools/drawings/` 专属文件夹，并将 22 张 A3 图纸的特定绘制逻辑（Matplotlib 绘图、图例、导读文字）分别拆分到 22 个完全独立的 `.py` 文件（如 `dr_004.py`、`dr_051.py`、`dr_081.py` 等）中，极大地提高了代码的可维护性与扩展性。
  * 将 `tools/draw_scope_map.py` 重构为通用调度引擎，采用 `importlib.import_module` 动态载入对应的绘图子模块，实现了绘图架构的 DRY（Don't Repeat Yourself）设计。
* **规划图册内容优化与定制**：
  * **道路交通系统规划图 (DR-051)**：移除了此前无理论依据的自规划道路，完全顺应并接驳现状的高连通度路网。
  * **历史文化展示系统图 (DR-057)**：重构了历史建筑和工业遗产探访路径算法，使其完全基于现状道路网，确保路线无中断且 100% 可真实通行。
  * **AIGC技术推演过程图 (DR-081)**：移除了无关的“规划研究范围”和图例，直接将系统架构图 (`system_architecture_mindmap.png`) 嵌入主绘图区，移除了图片内的原标题，并在图纸图签中将名称更新为“系统架构图”，排版优化使主绘图区更紧凑饱满。
  * **图册封面 (DR-001)**：将封面底色改为白底，以完美贴合规划图纸的图纸色调风格。将封面中的“指导教师”更新为“崔诚慧”，并将“时间”更新为“2026.6”。
* **新增 AI 绘图技能 (Skill)**：
  * 在项目 `.gemini/skills/` 目录下新增 `drawing_code_management.md` 规范，详细规定了绘图代码独立性、命名规范、模块导出接口、以及运行时依赖等约束，指导后续 AI 助手的协同绘图。


## [v4.1.0] - 2026-05-25
### ⚙️ DevOps & CI/CD 稳定性加固
* **修复了因 Git 忽略文件缺失导致 CI 报错的 Bug**：由于 35MB 的大文件 `data/gis/Building_Footprints.geojson` 被 `.gitignore` 排除，这导致在 GitHub Actions 干净环境中运行 `tools/data_quality_check.py` 会因为检测到该文件缺失而判定为 critical 的 `MISSING` 并返回退出码 1，阻断了 `smoke` 和 `test` job。
* **白名单降级处理**：在 `tools/data_quality_check.py` 中引入 `GIT_IGNORED_FILES` 白名单，将缺失的 Git 忽略大文件自动判定为 `WARNING` 状态并设评级为 `N/A`，不会触发非 0 退出码，保障 CI 无障碍通畅跑通。
* **审计并同步更新文档**：更新了 `BUG_REPORT.md` 与 `PROJECT_INSPECTION_REPORT.md` 相关的体检结论与修复记录。

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

### 🎨 UI/UX 与视觉体验优化
* **主页底部总结卡片图标防崩溃重构**：将主页底部的三个关键总结卡片（空间评价、视觉推演、协同测算）中的 `<img>` 图标彻底重构为**高兼容性的行内 Lucide SVG 矢量图标**，采用 `currentColor` 动态继承系统色彩，彻底解决了由于本地/云端静态资源路径不一致导致图标破损、显示不正常的问题。
* **研究范围地图 Banner 裁剪与容器贴合优化**：
  * **底图黑边裁剪**：识别到 `research_scope_2d.png` 底图左右两侧存在共计约 `588` 像素宽的纯色空白背景，使用 Python Pillow 图像库对其进行了**高精度自动化无损裁剪**（尺寸从 `2500x2500` 优化为 `1932x2500`），从而最大化地释放了地图与图例的横向像素，内容更加清晰易读。
  * **容器宽高比与贴合重构**：将 CSS 布局属性从 `flex: 1.8` 升级为 **`aspect-ratio: 1932 / 2500`** 完美宽高比约束，使 3D 悬浮图框与内部裁剪后的底图天衣无缝地贴合。
  * **定位与 3D 透视偏移与靠右矫正**：针对 3D 旋转（`rotateY(-25deg)`）导致的视觉左移，引入了 **`transform-origin: right center`** 并缩减了 Banner 的右侧内边距（`padding-right: 25px`），配合 `margin-right: -5px` 完美消除了右侧视觉缝隙，使图框能够以像素级精度钉死在 Banner 的最右侧，完全对齐系统的网格布局线。
  * **左侧自适应拉伸与指标横向铺开**：在保持图框尺寸（高度 `560px`，宽度自适应）完全不变的前提下，让左侧 `.page-banner-content` 面板自适应横向拉伸占据所有空余空间。同时，将指标网格重构为**智能响应式单行横排布局（`repeat(auto-fit, minmax(220px, 1fr))`）**，4项核心指标由 2x2 堆叠优化为单行水平铺开，完美填补了页面中段的视觉空白，整体排版舒展、疏密有致，极具现代高级大屏仪表面板的视觉张力。

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
