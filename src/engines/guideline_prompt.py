"""城市设计导则生成提示词模板

提供详细的导则生成 prompt，集成 RAG 政策检索和多阶段数据引用。

Usage:
    from src.engines.guideline_prompt import build_guideline_prompt
"""

from typing import Dict, Optional


GUIDELINE_CHAPTERS = [
    {
        "id": "1",
        "title": "总则",
        "sections": ["编制目的", "适用范围", "规划依据", "术语定义", "基本原则"],
        "word_target": 800,
        "description": "说明导则的编制背景、法律依据、适用对象和基本原则",
    },
    {
        "id": "2",
        "title": "总体定位与发展目标",
        "sections": ["区域定位", "发展愿景", "分项目标", "核心策略体系"],
        "word_target": 1000,
        "description": "明确街区的整体定位、发展愿景和分层目标体系",
    },
    {
        "id": "3",
        "title": "现状分析与问题诊断",
        "sections": ["区位与范围", "土地利用现状", "建筑现状", "交通现状", "公共空间现状", "历史文化资源", "核心问题识别"],
        "word_target": 1200,
        "description": "系统梳理场地现状，识别核心矛盾和更新潜力",
    },
    {
        "id": "4",
        "title": "空间结构与功能布局",
        "sections": ["空间结构规划", "功能分区", "用地规划", "开发强度控制"],
        "word_target": 1000,
        "description": "确定空间结构、功能分区和用地布局",
    },
    {
        "id": "5",
        "title": "建筑风貌控制导则",
        "sections": ["高度控制", "色彩与材质", "屋顶形式", "立面改造", "建筑界面", "重点建筑保护"],
        "word_target": 1200,
        "description": "规定建筑高度、色彩、材质、界面等风貌控制要求",
    },
    {
        "id": "6",
        "title": "公共空间与绿地系统",
        "sections": ["公共空间体系", "绿地系统", "广场与节点", "口袋公园", "街道家具"],
        "word_target": 1000,
        "description": "构建三级公共空间体系和绿地网络",
    },
    {
        "id": "7",
        "title": "道路交通与慢行系统",
        "sections": ["道路系统规划", "停车规划", "慢行网络", "公共交通", "断头路打通"],
        "word_target": 1000,
        "description": "优化道路网络、慢行系统和公共交通组织",
    },
    {
        "id": "8",
        "title": "历史文化保护与活化",
        "sections": ["保护对象清单", "保护范围划定", "风貌协调要求", "活化利用策略", "工业遗产活化"],
        "word_target": 1000,
        "description": "明确历史文化保护要求和活化利用策略",
    },
    {
        "id": "9",
        "title": "基础设施与市政工程",
        "sections": ["给排水", "电力通信", "环卫设施", "消防设施", "无障碍设施"],
        "word_target": 600,
        "description": "规定基础设施和市政工程的配置标准",
    },
    {
        "id": "10",
        "title": "实施保障与管理机制",
        "sections": ["分期实施计划", "资金保障", "管理机制", "公众参与", "监督评估"],
        "word_target": 800,
        "description": "建立实施保障体系和长效管理机制",
    },
]


def build_outline_prompt(
    diagnosis: str = "",
    case_benchmark: str = "",
    design_concept: str = "",
    strategy_matrix: str = "",
    spatial_stats: str = "",
    policy_context: str = "",
) -> str:
    """第一步：生成导则大纲要素。

    让 LLM 先梳理每章的核心要点、管控条文和指标，
    再以此为基础扩展为完整文本。
    """

    chapter_list = "\n".join(
        f"第{ch['id']}章 {ch['title']}（目标{ch['word_target']}字）：{ch['description']}"
        for ch in GUIDELINE_CHAPTERS
    )

    return f"""你是一位资深城市规划师，正在为长春市伪满皇宫周边街区微更新项目编制《城市设计导则》。

请先为以下10章导则生成详细的【要素大纲】，每章列出：
1. 本章核心论点（2-3个）
2. 关键管控条文（3-5条，使用「应/宜/可」分级）
3. 必须包含的量化指标（表格形式）
4. 数据引用来源（来自哪个阶段的分析）
5. 相关政策依据

══════ 导则结构 ══════

{chapter_list}

══════ 阶段数据 ══════

【问题诊断】{diagnosis[:2000] if diagnosis else "暂无"}
【案例对标】{case_benchmark[:2000] if case_benchmark else "暂无"}
【设计理念】{design_concept[:2000] if design_concept else "暂无"}
【策略协商】{strategy_matrix[:2000] if strategy_matrix else "暂无"}
【空间统计】{spatial_stats[:1000] if spatial_stats else "研究范围约150公顷，建筑约110,289栋"}
【政策依据】{policy_context[:2000] if policy_context else "《城市更新行动意见》《历史文化名城保护规划》"}

══════ 项目概况 ══════

- 项目：数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新
- 地点：长春市宽城区，约150公顷
- 核心地标：伪满皇宫（研究范围内，全国重点文保单位）
- 紧邻要素：长春站（北侧，东北铁路枢纽）、伊通河（东侧，城市生态廊道）
- 四大矛盾：历史保护与活力不足、工业低效与功能置换、社区老化与空间缺失、交通割裂与慢行不足

══════ 输出格式 ══════

每章格式：
## 第X章 章节标题

### 核心论点
- 论点1：...
- 论点2：...
- 论点3：...

### 管控条文
- 【应】条文内容（依据：数据来源/政策名称）
- 【宜】条文内容（依据：...）
- 【可】条文内容（依据：...）

### 量化指标
| 指标 | 控制值 | 依据 |
|------|--------|------|
| ... | ... | ... |

### 关键设计引导
- 引导1：...
- 引导2：...

请为全部10章生成要素大纲。"""


def build_expansion_prompt(
    outline: str,
    diagnosis: str = "",
    case_benchmark: str = "",
    design_concept: str = "",
    strategy_matrix: str = "",
    spatial_stats: str = "",
    policy_context: str = "",
) -> str:
    """第二步：基于要素大纲扩展为完整导则文本。"""

    total_words = sum(ch["word_target"] for ch in GUIDELINE_CHAPTERS)

    return f"""你是一位资深城市规划师。以下是一份《城市设计导则》的要素大纲，请将其扩展为完整的导则正文。

══════ 格式要求 ══════

1. 公文格式：1. / 1.1 / 1.1.1 三级编号
2. 每章开头有导言（50-100字）
3. 管控条文保持「应/宜/可」分级
4. 每条要求注明依据
5. 适当使用表格呈现指标
6. 总字数不少于{total_words}字
7. 不得使用「待补充」「TBD」等占位符
8. 语言严谨、规范、可交付

══════ 要素大纲（请扩展为完整文本）═══════

{outline}

══════ 补充数据（可引用）═══════

【问题诊断】{diagnosis[:2000] if diagnosis else "暂无"}
【案例对标】{case_benchmark[:2000] if case_benchmark else "暂无"}
【设计理念】{design_concept[:2000] if design_concept else "暂无"}
【策略协商】{strategy_matrix[:2000] if strategy_matrix else "暂无"}
【空间统计】{spatial_stats[:1000] if spatial_stats else ""}
【政策依据】{policy_context[:2000] if policy_context else ""}

══════ 项目概况 ══════

- 项目：数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新
- 地点：长春市宽城区，约150公顷
- 核心地标：伪满皇宫（研究范围内，全国重点文保单位）
- 紧邻要素：长春站（北侧，东北铁路枢纽）、伊通河（东侧，城市生态廊道）
- 核心管控：容积率≤1.4、核心区限高≤9m、一般区≤18m、绿地率≥25%

请将上述大纲扩展为完整的10章导则正文。每一章都必须有实质内容，条文清晰、数据准确、逻辑连贯。"""


def build_guideline_prompt(
    diagnosis: str = "",
    case_benchmark: str = "",
    design_concept: str = "",
    strategy_matrix: str = "",
    mpi_data: str = "",
    spatial_stats: str = "",
    policy_context: str = "",
) -> str:
    """构建完整的城市设计导则生成提示词。

    Parameters
    ----------
    diagnosis : str
        阶段一：问题诊断报告
    case_benchmark : str
        阶段二：案例对标分析
    design_concept : str
        阶段三：设计理念与目标
    strategy_matrix : str
        阶段四：多主体博弈策略矩阵
    mpi_data : str
        MPI 更新潜力排行数据
    spatial_stats : str
        空间统计指标（建筑数量、高度、密度等）
    policy_context : str
        RAG 检索的政策文件内容

    Returns
    -------
    str
        完整的导则生成提示词
    """

    chapter_structure = "\n".join(
        f"第{ch['id']}章 {ch['title']}\n"
        f"  章节内容：{ch['description']}\n"
        f"  包含小节：{'、'.join(ch['sections'])}\n"
        f"  目标字数：约{ch['word_target']}字"
        for ch in GUIDELINE_CHAPTERS
    )

    total_words = sum(ch["word_target"] for ch in GUIDELINE_CHAPTERS)

    prompt = f"""你是一位资深的城市规划师，正在为长春市宽城区伪满皇宫周边街区微更新项目编制《城市设计导则》。

请基于以下多阶段循证数据，生成一份完整的、可交付的城市设计导则文本。

═══════════════════════════════════════════════════════
一、导则结构要求（共10章，目标总字数{total_words}字以上）
═══════════════════════════════════════════════════════

{chapter_structure}

═══════════════════════════════════════════════════════
二、格式规范
═══════════════════════════════════════════════════════

1. 使用标准公文格式：1. / 1.1 / 1.1.1 三级编号
2. 每章开头有简短导言（50-100字），说明本章目的和适用范围
3. 管控条文使用「应」「宜」「可」三级强度：
   - 「应」表示强制性要求（必须遵守）
   - 「宜」表示推荐性要求（一般应遵守）
   - 「可」表示可选要求（鼓励遵守）
4. 每条管控要求注明数据来源或政策依据
5. 涉及具体指标时，给出数值范围和约束条件
6. 适当使用表格呈现指标体系

═══════════════════════════════════════════════════════
三、核心管控指标（必须包含）
═══════════════════════════════════════════════════════

| 管控维度 | 指标名称 | 控制要求 | 依据 |
|---------|---------|---------|------|
| 开发强度 | 容积率 | ≤1.4 | 历史文化名城保护规划 |
| 建筑高度 | 核心保护区限高 | ≤9m | 伪满皇宫视廊保护 |
| 建筑高度 | 风貌协调区限高 | ≤12m | 天际线控制 |
| 建筑高度 | 一般更新区限高 | ≤18m | 城市设计导则 |
| 建筑高度 | 站前服务区限高 | ≤24m | TOD开发要求 |
| 建筑密度 | 建筑密度 | ≤40% | 居住区设计标准 |
| 绿地率 | 绿地率 | ≥25% | 居住区设计标准 |
| 公共空间 | 5分钟覆盖率 | ≥80% | 完整社区建设标准 |
| 街道界面 | 街墙连续率 | ≥70% | 街道设计导则 |
| 慢行交通 | 人行道宽度 | ≥2m | 无障碍设计标准 |
| 混合用地 | 混合用地比例 | ≥30% | 城市更新政策 |

═══════════════════════════════════════════════════════
四、阶段一：问题诊断（数据来源）
═══════════════════════════════════════════════════════

{diagnosis[:3000] if diagnosis else "暂无诊断数据，请基于项目概况进行合理推断。"}

═══════════════════════════════════════════════════════
五、阶段二：案例对标（数据来源）
═══════════════════════════════════════════════════════

{case_benchmark[:3000] if case_benchmark else "暂无案例数据，请引用国内知名历史街区更新案例。"}

═══════════════════════════════════════════════════════
六、阶段三：设计理念（数据来源）
═══════════════════════════════════════════════════════

{design_concept[:3000] if design_concept else "暂无设计理念数据，请基于项目特点推断。"}

═══════════════════════════════════════════════════════
七、阶段四：策略协商（数据来源）
═══════════════════════════════════════════════════════

{strategy_matrix[:3000] if strategy_matrix else "暂无策略数据，请基于多主体博弈逻辑推断。"}

═══════════════════════════════════════════════════════
八、空间数据指标
═══════════════════════════════════════════════════════

{spatial_stats[:1500] if spatial_stats else "研究范围约150公顷，建筑总量约110,289栋。"}

═══════════════════════════════════════════════════════
九、MPI 更新潜力数据
═══════════════════════════════════════════════════════

{mpi_data[:1500] if mpi_data else "暂无MPI数据。"}

═══════════════════════════════════════════════════════
十、政策法规依据（RAG 检索结果）
═══════════════════════════════════════════════════════

{policy_context[:3000] if policy_context else "《中共中央办公厅国务院办公厅关于持续推进城市更新行动的意见》、《长春市历史文化名城保护规划》、《长春市国土空间总体规划》"}

═══════════════════════════════════════════════════════
十一、项目概况（固定信息）
═══════════════════════════════════════════════════════

- 项目名称：数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计
- 项目地点：中国吉林省长春市宽城区
- 研究范围：由长春大街、长白路、东九条、亚泰快速路围合
- 总用地面积：约150公顷
- 核心地标：伪满皇宫（研究范围内，全国重点文保单位）
- 紧邻要素：长春站（北侧，东北铁路枢纽）、伊通河（东侧，城市生态廊道）
- 项目类型：历史街区更新、TOD综合开发、片区城市设计
- 四大核心矛盾：历史保护与城市活力不足、工业低效与功能置换、社区老化与公共空间缺失、交通割裂与慢行体验不足

═══════════════════════════════════════════════════════

请严格按照上述结构和格式要求，生成完整的城市设计导则文本。每一章都必须有实质内容，不得使用「待补充」「TBD」等占位符。总字数不少于{total_words}字。"""

    return prompt


def retrieve_policy_context(query: str = "城市更新 历史文化街区 保护 微更新") -> str:
    """从 RAG 知识库检索相关政策文件内容。

    Parameters
    ----------
    query : str
        检索查询词

    Returns
    -------
    str
        检索到的政策内容拼接
    """
    try:
        from src.engines.rag_engine import retrieve_rag_context
        results = retrieve_rag_context(query, top_k=5)
        if results:
            return "\n\n".join(
                f"【{r.get('source', '未知来源')}】\n{r.get('content', '')[:800]}"
                for r in results
            )
    except Exception:
        pass
    return ""


def build_spatial_stats_summary(stats: dict = None, skyline: dict = None) -> str:
    """构建空间统计摘要。"""
    parts = []
    if stats:
        parts.append(f"研究范围面积：{stats.get('boundary_ha', 150)} 公顷")
        parts.append(f"POI 数据量：{stats.get('poi_count', 0)} 条")
        parts.append(f"街景采样点：{stats.get('gvi_count', 0)} 个")
    if skyline:
        parts.append(f"建筑总量：{skyline.get('building_count', 0)} 栋")
        parts.append(f"平均建筑高度：{skyline.get('avg_height', 0)} 米")
        parts.append(f"最高建筑：{skyline.get('max_height', 0)} 米")
        parts.append(f"高层建筑占比：{skyline.get('high_rise_ratio', 0)}%")
    return "\n".join(parts) if parts else ""
