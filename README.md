# UltimateDESIGN

**长春伪满皇宫周边街区微更新与城市设计决策支持平台**

UltimateDESIGN 是一个面向城乡规划专业城市设计课程、毕业设计和研究展示的 Streamlit 应用。项目按 **13 个专业阶段** 组织页面，每个阶段页面集成功能模块、数据驱动的图纸提示词生成和面向答辩的阶段研究小结。

## 三大板块与 13 阶段

| 板块 | 阶段 | 独立页面 |
| --- | --- | --- |
| 前期 | 01-05 | pages/01 ~ pages/05 |
| 中期 | 06-07 | pages/06 ~ pages/07 |
| 后期 | 08-13 | pages/08 ~ pages/13 |

## 13 阶段页面功能概览

每个阶段页面都包含：功能模块 + 图纸提示词生成 + 阶段研究小结。

| 阶段 | 页面 | 核心功能 |
| --- | --- | --- |
| 01 | 任务解读 | 项目概况、任务书/开题报告、区位图提示词 |
| 02 | 资料收集 | 语义萃取引擎、空间数据资产管理 |
| 03 | 现场调研 | 街景样本库 |
| 04 | 现状分析 | 3D底座概览、POI/建筑/天际线统计 |
| 05 | 问题诊断 | AHP-MPI评估 + 地块雷达 + AI诊断报告 |
| 06 | 目标定位 | LLM案例对标 + 设计理念提炼 |
| 07 | 设计策略 | 三角色协商 + 共识雷达 + RAG政策校验 |
| 08 | 总体城市设计 | 概念总平面图AIGC生形 |
| 09 | 专项系统设计 | 轴测推演 + 四大专项叠合 |
| 10 | 重点地段深化 | 5类地块选择 + AIGC街景推演 |
| 11 | 实施路径 | 六类更新方式 + 三期实施计划 |
| 12 | 城市设计导则 | LLM导则生成 + 管控指标 + Word导出 |
| 13 | 成果表达 | 图纸提示词总览(16+模板) + 导出中心 |

## 核心模块

| 模块 | 职责 |
| --- | --- |
| src/workflow/stage_data_bus.py | 跨阶段数据总线 |
| src/ui/module_summary.py | 阶段研究小结组件 |
| src/engines/drawing_prompt_templates.py | 图纸提示词模板库 |
| src/engines/spatial_engine.py | POI/街景/天际线统计 |
| src/engines/site_diagnostic_engine.py | 地块诊断/策略矩阵 |
| src/engines/llm_engine.py | Ollama/Gemma调用 |

## 启动

pip install -r requirements.txt
streamlit run app.py

## 验证

python -m compileall app.py pages src tests tools
pytest
