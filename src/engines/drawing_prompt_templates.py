"""图纸提示词模板库 —— 为每类缺失图纸预设基于研究区域数据的专业提示词。

每个模板包含：
- ``name``         图纸名称
- ``chapter``      所属图册章节
- ``stage``        对应阶段编号
- ``data_deps``    数据依赖函数（返回数据上下文字符串）
- ``prompt_tmpl``  提示词模板（含 {data_context} 占位符）
- ``sys_prompt``   系统提示词

调用 ``build_drawing_prompt(template_name)`` 即可自动注入数据并生成完整提示词。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DrawingTemplate:
    name: str
    chapter: str
    stage: str
    description: str
    prompt_tmpl: str
    sys_prompt: str = "你是城乡规划专业的毕业设计图纸制作顾问。请生成可直接用于 ChatGPT Image 2.0 的图纸提示词。"
    data_deps: list[str] = field(default_factory=list)


def _get_project_context() -> str:
    """获取项目基础数据上下文。"""
    ctx_parts = [
        "项目：长春市宽城区伪满皇宫周边街区更新规划设计",
        "研究范围：约150公顷，由长春大街、长白路、东九条、亚泰快速路围合",
        "核心资源：伪满皇宫、中车厂区工业遗产、老旧社区、长春站枢纽",
        "四大核心矛盾：历史保护与城市活力不足、工业低效与功能置换、社区老化与公共空间缺失、交通割裂与慢行体验不足",
    ]

    try:
        from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
        stats = get_hud_statistics()
        sky = get_skyline_features()
        ctx_parts.append(f"POI数据：{stats['poi_count']} 条记录")
        ctx_parts.append(f"街景样本：{stats['gvi_count']} 条记录")
        ctx_parts.append(f"研究范围面积：{stats['boundary_ha']} 公顷")
        ctx_parts.append(f"建筑总数：{sky['building_count']} 栋")
        ctx_parts.append(f"平均建筑高度：{sky['avg_height']} 米")
        ctx_parts.append(f"最高建筑：{sky['max_height']} 米")
        ctx_parts.append(f"高层建筑占比：{sky['high_rise_ratio']}%")
    except Exception:
        ctx_parts.append("（空间引擎数据暂不可用，请使用概括性表达）")

    try:
        from src.engines.site_diagnostic_engine import get_plot_diagnostics
        diags = get_plot_diagnostics()
        if diags:
            ctx_parts.append(f"重点更新单元：{len(diags)} 个地块")
            names = [d["name"] for d in diags[:5]]
            ctx_parts.append(f"地块名称：{'、'.join(names)}")
            avg_mpi = sum(d["mpi_score"] for d in diags) / len(diags)
            avg_gvi = sum(d["gvi_mean"] for d in diags) / len(diags)
            ctx_parts.append(f"平均MPI得分：{avg_mpi:.1f}")
            ctx_parts.append(f"平均绿视率GVI：{avg_gvi:.1f}%")
    except Exception:
        pass

    return "\n".join(ctx_parts)


# ============================================================
# 模板定义 —— 按阶段组织
# ============================================================

DRAWING_TEMPLATES: list[DrawingTemplate] = [
    # ---- 阶段 01 任务解读 ----
    DrawingTemplate(
        name="区位分析图",
        chapter="01 项目认知篇",
        stage="01",
        description="长春市—宽城区—伪满皇宫周边三级区位图",
        prompt_tmpl="""请为以下城市设计项目生成一张"区位分析图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 采用三级嵌套式区位表达：长春市全域→宽城区→研究范围
- 红色虚线标注研究范围，蓝色标注重点地块
- 标注长春站、伊通河、伪满皇宫等关键地标
- A3横版，左侧大区位、右侧研究范围放大
- 底色为蓝灰色调，避免过于鲜艳""",
    ),
    DrawingTemplate(
        name="周边关系图",
        chapter="01 项目认知篇",
        stage="01",
        description="长春站、伊通河、伪满皇宫、商业区、老旧社区关系",
        prompt_tmpl="""请为以下城市设计项目生成一张"周边关系图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 以研究范围为核心，用箭头和标注展示与周边的功能联系
- 北侧：长春站枢纽（站城联动关系）
- 东侧：伊通河生态廊道（生态联系）
- 南侧：伪满皇宫（文化遗产联系）
- 西侧：铁北老旧社区（社区更新联系）
- A3横版，清晰的关系箭头和文字标注""",
    ),
    DrawingTemplate(
        name="历史沿革图",
        chapter="01 项目认知篇",
        stage="01",
        description="伪满皇宫、铁路、工业厂区、老城住区演变时间线",
        prompt_tmpl="""请为以下城市设计项目生成一张"历史沿革图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 横向时间线结构：伪满时期→新中国建设→改革开放→当代
- 每个时期配一张示意图和关键事件标注
- 突出铁路工业遗产的历史演变
- 色彩从暖色（历史）渐变到冷色（当代）
- A3横版，4-5个时间节点""",
    ),
    DrawingTemplate(
        name="上位规划解读图",
        chapter="01 项目认知篇",
        stage="01",
        description="国土空间规划、历史文化名城保护规划、城市更新政策",
        prompt_tmpl="""请为以下城市设计项目生成一张"上位规划解读图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 提炼3-4项上位规划的核心管控要求
- 《长春市国土空间总体规划》中的功能定位
- 《长春市历史文化名城保护规划》中的保护要求
- 城市更新政策中的微更新导向
- 用关键词卡片+底图标注的方式表达
- A3横版，左侧规划名称和要点，右侧底图标注""",
    ),

    # ---- 阶段 04 现状分析 ----
    DrawingTemplate(
        name="AI诊断用地现状图",
        chapter="02 数据诊断篇",
        stage="04",
        description="低效用地、闲置用地、功能冲突区叠加（任务书必做图）",
        prompt_tmpl="""请为以下城市设计项目生成一张"AI诊断用地现状图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 这是任务书明确要求的核心图之一
- 在用地现状底图上叠加AI识别结果
- 红色标注低效用地区域（工业闲置、空置商铺）
- 橙色标注功能冲突区（居住与工业混杂）
- 黄色标注待更新区域
- 绿色标注生态和公共空间
- 右侧图例包含：AI识别类型、面积占比、识别置信度
- A3横版，突出"数据驱动"而非"经验判断"的技术特色""",
    ),
    DrawingTemplate(
        name="空间句法可达性分析图",
        chapter="02 数据诊断篇",
        stage="04",
        description="整合度、选择度、步行可达性分析（任务书必做图）",
        prompt_tmpl="""请为以下城市设计项目生成一张"空间句法可达性分析图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 这是任务书明确要求的核心图之一
- 用热力色带表达道路网络的整合度（红色=高可达、蓝色=低可达）
- 识别断头路、隔离区和通行瓶颈
- 铁路线和快速路作为主要阻隔要素标注
- 左侧主图为空间句法分析结果
- 右侧附小图展示步行5/10/15分钟等时圈
- A3横版，数据来源标注为"Space Syntax分析"
- 说明：数据不足处标注"示意"，避免生成虚假数值""",
    ),
    DrawingTemplate(
        name="建筑风貌识别图",
        chapter="02 数据诊断篇",
        stage="04",
        description="CV建筑风貌识别结果展示",
        prompt_tmpl="""请为以下城市设计项目生成一张"建筑风貌识别图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 展示计算机视觉(CV)对建筑风貌的分类识别结果
- 分类包括：日式历史建筑、中式传统民居、工业厂房、普通住宅、杂乱搭建
- 每类用不同颜色填充建筑轮廓
- 附4-6张典型街景识别示例（照片+标注框）
- 右侧图例包含各类型数量和占比
- A3横版，底图为建筑轮廓图""",
    ),

    # ---- 阶段 05 问题诊断 ----
    DrawingTemplate(
        name="环境品质问题地图",
        chapter="02 数据诊断篇",
        stage="05",
        description="杂乱界面、停车混乱、绿化不足、设施老化综合问题图（任务书必做图）",
        prompt_tmpl="""请为以下城市设计项目生成一张"环境品质问题地图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 这是任务书明确要求的重要成果图
- 在底图上综合标注以下环境品质问题：
  · 杂乱界面（红色区块）
  · 停车混乱区域（橙色标记）
  · 绿化严重不足区域（灰色，GVI<10%）
  · 设施老化节点（黄色图标）
  · 背街消极空间（灰色斜线填充）
- 配合街景实拍照片标注典型问题
- A3横版，主图+6张问题实拍照片环绕""",
    ),
    DrawingTemplate(
        name="遗产价值评估热力图",
        chapter="03 价值评估篇",
        stage="05",
        description="历史价值、风貌价值、工业遗产价值、空间识别度综合热力图（任务书必做图）",
        prompt_tmpl="""请为以下城市设计项目生成一张"遗产价值评估热力图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 这是任务书明确要求的必做图
- 用热力色带表达遗产综合价值：深红=极高价值、红=高价值、橙=中等价值、黄=一般价值
- 伪满皇宫及其核心保护区为深红色
- 中车老厂区工业遗产为红色
- 传统民居街巷为橙色
- 标注文保单位名称和保护等级
- 右侧附遗产评价指标说明
- A3横版""",
    ),
    DrawingTemplate(
        name="综合评价分区图",
        chapter="03 价值评估篇",
        stage="05",
        description="高价值保护区、风貌协调区、功能置换区、社区修补区、重点再生区",
        prompt_tmpl="""请为以下城市设计项目生成一张"综合评价分区图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 将研究范围划分为五类管控分区：
  · 高价值保护区（深红色）—— 伪满皇宫核心区
  · 风貌协调区（橙色）—— 历史风貌缓冲区
  · 功能置换区（蓝色）—— 工业低效用地
  · 社区修补区（绿色）—— 老旧社区微更新
  · 重点再生区（紫色）—— 站城门户等战略节点
- 标注5个重点深化地块
- A3横版，右侧图例包含各分区面积和占比""",
    ),

    # ---- 阶段 07 设计策略 ----
    DrawingTemplate(
        name="更新模式分区图",
        chapter="04 策略生成篇",
        stage="07",
        description="保护修缮、整治提升、功能置换、拆改更新、新建补充分类图",
        prompt_tmpl="""请为以下城市设计项目生成一张"更新模式分区图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 这是城市更新设计的关键图
- 按地块/建筑划分五种更新模式：
  · 保护修缮（深红色）—— 文保和历史建筑
  · 整治提升（橙色）—— 界面和环境提升
  · 功能置换（蓝色）—— 工业用地转型
  · 拆改更新（紫色）—— 危旧建筑更新
  · 新建补充（灰色）—— 公共设施和开放空间补充
- 标注典型案例地块名称
- A3横版，右侧图例含各类型面积占比""",
    ),
    DrawingTemplate(
        name="空间结构规划图",
        chapter="04 策略生成篇",
        stage="07",
        description="一核两轴多片多节点的空间结构",
        prompt_tmpl="""请为以下城市设计项目生成一张"空间结构规划图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 表达"一核、两轴、多片、多节点"的空间结构
- 一核：伪满皇宫文化核心
- 两轴：站城活力发展轴 + 工业遗产更新轴
- 多片：文旅展示片区、创意产业片区、社区生活片区、站前服务片区
- 多节点：门户节点、文化节点、社区节点、生态节点
- 用粗线表达轴线、色块表达片区、圆点表达节点
- A3横版，底图为简化建筑肌理""",
    ),

    # ---- 阶段 09 专项系统 ----
    DrawingTemplate(
        name="道路交通系统规划图",
        chapter="05 总体规划篇",
        stage="09",
        description="主次支路、内部慢行街巷、停车组织（任务书必做图）",
        prompt_tmpl="""请为以下城市设计项目生成一张"道路交通系统规划图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 这是任务书明确要求的必做图
- 红色粗线：主干路（长春大街、亚泰大街）
- 橙色中线：次干路
- 蓝色细线：支路和街巷
- 绿色虚线：慢行专用道
- 标注断头路打通位置（黄色箭头）
- 标注停车设施位置（P图标）
- 标注公交站和轨道站（蓝色圆点）
- A3横版""",
    ),
    DrawingTemplate(
        name="慢行系统规划图",
        chapter="05 总体规划篇",
        stage="09",
        description="游客路径、居民路径、骑行路径、无障碍路径",
        prompt_tmpl="""请为以下城市设计项目生成一张"慢行系统规划图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 区分三类慢行路径：
  · 红色：文旅游览路径（长春站→伪满皇宫→工业遗产）
  · 蓝色：居民日常路径（社区→菜市场→公园→学校）
  · 绿色：骑行路径（共享单车+专用车道）
- 标注慢行节点（广场、口袋公园、休憩设施）
- 强调长春站到伪满皇宫的步行联系
- A3横版，底图为简化路网""",
    ),
    DrawingTemplate(
        name="公共空间系统图",
        chapter="05 总体规划篇",
        stage="09",
        description="文化广场、社区活动场、口袋公园、街角空间层级网络",
        prompt_tmpl="""请为以下城市设计项目生成一张"公共空间系统图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 构建三级公共空间层级：
  · 一级：区域级文化广场（红色大圆）
  · 二级：社区级活动场地（橙色中圆）
  · 三级：街角口袋空间（绿色小圆）
- 用绿色廊道连接各级公共空间
- 标注步行5分钟服务半径覆盖
- A3横版""",
    ),
    DrawingTemplate(
        name="历史文化展示系统图",
        chapter="05 总体规划篇",
        stage="09",
        description="文化游线、展示节点、导视系统、历史界面（项目特色必做图）",
        prompt_tmpl="""请为以下城市设计项目生成一张"历史文化展示系统图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 这是项目特色图，必须重点表达
- 红色主线：历史文化游览主线路（长春站→伪满皇宫→铁北工业遗产）
- 金色节点：文化展示节点（伪满皇宫、中车厂区、传统民居街巷等）
- 蓝色标注：导视系统设置点位
- 灰色底纹：历史界面保护范围
- 附文化标识设计示意
- A3横版，突出历史文脉的连续性""",
    ),

    # ---- 阶段 11 实施路径 ----
    DrawingTemplate(
        name="分期实施图",
        chapter="07 技术推演与实施篇",
        stage="11",
        description="近期微更新、中期功能置换、远期整体提升三期分区",
        prompt_tmpl="""请为以下城市设计项目生成一张"分期实施图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 将研究范围划分为三期实施分区：
  · 近期（1-3年，绿色）：环境整治、口袋公园、街道微更新、社区设施补充
  · 中期（3-5年，蓝色）：重点地块功能置换、工业遗产活化、商业业态导入
  · 远期（5-10年，紫色）：片区整体更新、文旅品牌塑造、智慧系统完善
- 标注各期重点项目名称
- A3横版，三期用不同底色区分""",
    ),

    # ---- 阶段 13 成果表达 ----
    DrawingTemplate(
        name="AIGC技术推演过程图",
        chapter="07 技术推演与实施篇",
        stage="13",
        description="输入约束→风貌样本→生成参数→多方案比选→人工校核（任务书必做图）",
        prompt_tmpl="""请为以下城市设计项目生成一张"AIGC技术推演过程图"的 Image 2.0 提示词。

{data_context}

图纸要求：
- 这是回应任务书技术融合要求的必做图
- 展示AI辅助设计的完整技术路径：
  1. 数据采集层：GIS、街景、POI、建筑轮廓
  2. AI识别层：CV风貌识别、空间句法、NLP情感分析
  3. 方案生成层：ControlNet约束+Stable Diffusion推演
  4. 决策支持层：LLM多主体协商+RAG政策校验
  5. 成果输出层：图册、导则、Word文件
- 用流程图结构，每层配一张示意截图
- A3横版，从左到右的技术流程""",
    ),
]

# 构建名称索引
_TEMPLATE_INDEX = {t.name: t for t in DRAWING_TEMPLATES}


def get_template(name: str) -> DrawingTemplate | None:
    """按名称获取模板。"""
    return _TEMPLATE_INDEX.get(name)


def get_templates_by_stage(stage_code: str) -> list[DrawingTemplate]:
    """获取某阶段的全部模板。"""
    return [t for t in DRAWING_TEMPLATES if t.stage == stage_code]


def get_all_template_names() -> list[str]:
    """返回全部模板名称。"""
    return [t.name for t in DRAWING_TEMPLATES]


def build_drawing_prompt(template_name: str) -> tuple[str, str]:
    """构建完整的图纸提示词（自动注入项目数据）。

    Returns
    -------
    tuple[str, str]
        (完整提示词, 系统提示词)
    """
    tmpl = get_template(template_name)
    if not tmpl:
        return "", ""
    ctx = _get_project_context()
    prompt = tmpl.prompt_tmpl.replace("{data_context}", ctx)
    return prompt, tmpl.sys_prompt


def generate_drawing_prompt_with_llm(
    template_name: str,
    model: str = "gemma4:e2b-it-q4_K_M",
) -> str:
    """调用 Gemma 4 生成基于数据的图纸提示词。"""
    prompt, sys_prompt = build_drawing_prompt(template_name)
    if not prompt:
        return f"未找到模板: {template_name}"

    from src.engines.llm_engine import call_llm_engine
    try:
        return call_llm_engine(prompt=prompt, system_prompt=sys_prompt, model=model)
    except Exception as e:
        return f"LLM 调用失败: {e}"
