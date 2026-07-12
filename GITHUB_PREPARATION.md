# ultimateDESIGN GitHub 上传与发布准备指南

本指南为团队及个人开发者提供将 **ultimateDESIGN** 决策支持平台安全、规范地上传至 GitHub 的标准流程。通过执行本流程，可以确保代码库的纯净度，避免泄露敏感密钥（API Key），并规避大体积 GIS 数据文件导致的推送失败问题。

---

## 📋 核心准备流程

### 第一步：环境与页面完整性校验
在打包或上传前，必须确保平台的所有页面与运行时依赖均完整无缺。
```powershell
# 运行环境完整性与页面存在性校验
python tools/check_env.py
```
> [!NOTE]
> 该脚本会自动对 15 个页面（主入口 `app.py` 及 `pages/` 下 14 个阶段功能页面）进行扫描。如果返回 `[OK]` 即可进入下一步。

---

### 第二步：运行全量单元测试
上传前，必须确保所有核心算法和业务逻辑全部通过本地测试。重点地块、GIS 处理、提示词解耦和多版式图纸链路应先跑聚焦回归，再跑全量套件。
```powershell
# 重点回归：动态重点地块 / GIS 处理 / 多版式图纸 / 提示词链路
python -m pytest tests/test_key_plot_engine.py tests/test_process_key_plots.py tests/test_drawing_layout_engine.py tests/test_drawing_prompt_engine.py tests/test_drawing_prompt_templates.py tests/test_site_diagnostic_engine.py tests/test_prompt_decoupling.py tests/test_frame_generator.py -v

# 执行全量单元测试
python -m pytest -q
```
> [!IMPORTANT]
> 必须确保测试通过率为 100%。如果存在失败用例，请参照 [BUG_REPORT.md](./BUG_REPORT.md) 的排查思路修复后再进行上传。

> [!NOTE]
> `tests/test_prompt_decoupling.py` 会临时写入测试配置，和其他包含同一 fixture 的套件并行运行时容易造成配置文件脏写；建议按上述命令串行执行并在测试后确认 `git status --short` 为空。

---

### 第三步：敏感凭据扫描与清理
为防止百度地图 AK 或 DeepSeek API KEY 等私密凭证泄露至公共代码仓库，必须运行内置的静态凭据扫描器。
```powershell
# 扫描敏感泄露信息
python tools/secret_scan.py

# 与 GitHub Actions smoke job 对齐
python tools/check_env.py
python tools/startup_smoke.py
python tools/data_quality_check.py
```
#### 凭证清理与轮换标准：
1. **本地配置文件**：确保根目录下仅有本地专用的 `.env`，该文件已被 `.gitignore` 排除在外，绝对不会被提交。
2. **凭据占位模版**：仓库中只应存在 [`.env.example`](./.env.example)，其中所有 API Key 必须使用标准的占位符说明（如 `YOUR_DEEPSEEK_API_KEY`）。
3. **历史提交清理**：若通过 `secret_scan.py` 审计发现 Git 历史提交中包含真实密钥，必须使用工具清理历史提交：
   ```powershell
   git filter-repo --path <泄露文件名> --invert-paths
   ```
   并在服务商官网立即**废弃并轮换**泄露的 API Key。

---

### 第四步：骨架打包与大文件隔离
由于 GIS 矢量文件（如 33MB 的 `Building_Footprints.geojson`）以及生成的高清渲染图纸图集单文件体积巨大，不适合直接放入 Git 仓库。
我们提供了一键打包脚本，会自动剔除大文件，并对其生成 `.placeholder.txt` 占位说明文件，提醒下游接收者如何获取数据。

```powershell
# 运行项目骨架一键打包脚本
python scripts/package_skeleton.py
```
#### 打包细节说明：
- 自动读取并应用 `.gitignore` 中的过滤规则。
- 自动对虚拟环境（`.venv`、`venv`、`.runtime-packages`）进行剪枝跳过。
- 自动过滤所有体积超过 **10MB** 的大资产文件（如大型 geojson、mp4 录屏、psd 模板、bin 模型），并就地生成描述文件。
- 打包结果将输出至项目根目录下的 [`ultimate_design_skeleton.zip`](./ultimate_design_skeleton.zip)。

---

## 📦 项目发布排除清单

以下目录和文件在 GitHub 上传或归档时**严禁包含**：

| 类别 | 路径/格式 | 说明 |
| :--- | :--- | :--- |
| **敏感配置文件** | `.env` | 包含个人真实 API 凭证，只保留模板 `.env.example` |
| **运行时依赖** | `.venv/`, `venv/`, `.runtime-packages/` | 本地 Python 虚拟环境，使用 `requirements.txt` 重建 |
| **超大矢量数据** | `data/gis/Building_Footprints.geojson` | 33MB 的高精度建筑轮廓，GitHub 限制单文件上传 |
| **本地运行缓存** | `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` | Python 编译及测试产生的临时高速缓存文件 |
| **草稿与历史备份** | `scratch/`, `output/`, `logs/` | 调试日志与生成草稿，上传前已全量清空 |

---

## 🚀 首次推送至 GitHub 命令行指南

若需将此纯净代码库初始化并推送到您的 GitHub 新仓库，可使用以下标准 Git 指令集：

```powershell
# 1. 在项目根目录下初始化本地仓库
git init

# 2. 将所有纯净代码文件添加至暂存区 (会自动应用 .gitignore 过滤)
git add .

# 3. 提交至本地分支
git commit -m "feat: init ultimateDESIGN clean skeleton platform workflow"

# 4. 关联 GitHub 远程仓库
git remote add origin https://github.com/<您的用户名>/ultimate-design.git

# 5. 重命名主分支为 main
git branch -M main

# 6. 推送至远程仓库
git push -u origin main
```

指南更新完成，祝您打包与上传工作顺利开展！
