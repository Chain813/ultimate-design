"""Image 2.0 drawing-prompt assistant for planning atlas sheets.

The module is intentionally deterministic: it does not call an image model and
it refuses or downgrades prompts when the selected drawing lacks required
spatial/data references.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


PROJECT_DEFAULTS = {
    "project_cn": "数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计",
    "project_en": "To be confirmed",
    "project_types": "历史街区更新、TOD 综合开发、片区城市设计、老城复兴、城市更新、文旅融合",
    "location": "中国吉林省长春市宽城区伪满皇宫周边街区",
    "scope": "由长春大街、长白路、东九条、亚泰快速路围合而成",
    "area": "约150公顷",
    "landmarks": "伪满皇宫、长春站、伊通河",
    "themes": "数字孪生、AIGC推演、AI辅助设计、历史文化更新、遗产保护、TOD、城市缝合、街区微更新、文旅融合、智慧治理",
}


BOOK_CHAPTERS = {
    "01 项目认知篇": [
        "封面",
        "目录",
        "项目背景图",
        "区位分析图",
        "研究范围图",
        "周边关系图",
        "上位规划解读图",
        "规划依据图",
        "历史沿革图",
        "案例借鉴图",
    ],
    "02 数据诊断篇": [
        "数字孪生技术框架图",
        "数据来源图",
        "用地现状分析图",
        "AI诊断用地现状图",
        "建筑现状分析图",
        "建筑高度现状图",
        "建筑风貌识别图",
        "历史建筑与工业遗产分布图",
        "道路交通现状图",
        "空间句法可达性分析图",
        "公共交通覆盖图",
        "慢行系统现状图",
        "公共空间现状图",
        "绿地与生态现状图",
        "人群活动热力图",
        "POI功能活力分析图",
        "社交媒体情感分析图",
        "老龄社区分布图",
        "环境品质问题地图",
        "四大问题诊断总图",
    ],
    "03 价值评估篇": [
        "遗产价值评估热力图",
        "风貌敏感度评价图",
        "更新潜力评价图",
        "保护与更新冲突图",
        "综合评价分区图",
    ],
    "04 策略生成篇": [
        "设计理念图",
        "更新目标体系图",
        "总体策略图",
        "更新模式分区图",
        "功能策划图",
        "空间结构规划图",
        "5个重点地块定位图",
    ],
    "05 总体规划篇": [
        "总平面图",
        "鸟瞰效果图",
        "土地利用规划图",
        "功能布局规划图",
        "建筑更新控制图",
        "建筑高度控制图",
        "开发强度控制图",
        "道路交通系统规划图",
        "小街区密路网规划图",
        "慢行系统规划图",
        "公共交通与换乘图",
        "公共空间系统图",
        "绿地景观系统图",
        "历史文化展示系统图",
        "风貌控制图",
        "夜景照明与导视系统图",
        "规划指标表",
    ],
    "06 重点地块深化篇": [
        "地块1现状问题图",
        "地块1更新定位图",
        "地块1平面深化图",
        "地块1AIGC推演效果图",
        "地块1人视效果图",
        "地块1建筑更新图",
        "地块1街道断面图",
        "地块1改造前后对比图",
        "地块1运营场景图",
        "地块2现状问题图",
        "地块2更新定位图",
        "地块2平面深化图",
        "地块2AIGC推演效果图",
        "地块2人视效果图",
        "地块2建筑更新图",
        "地块2街道断面图",
        "地块2改造前后对比图",
        "地块2运营场景图",
        "地块3现状问题图",
        "地块3更新定位图",
        "地块3平面深化图",
        "地块3AIGC推演效果图",
        "地块3人视效果图",
        "地块3建筑更新图",
        "地块3街道断面图",
        "地块3改造前后对比图",
        "地块3运营场景图",
        "地块4现状问题图",
        "地块4更新定位图",
        "地块4平面深化图",
        "地块4AIGC推演效果图",
        "地块4人视效果图",
        "地块4建筑更新图",
        "地块4街道断面图",
        "地块4改造前后对比图",
        "地块4运营场景图",
        "地块5现状问题图",
        "地块5更新定位图",
        "地块5平面深化图",
        "地块5AIGC推演效果图",
        "地块5人视效果图",
        "地块5建筑更新图",
        "地块5街道断面图",
        "地块5改造前后对比图",
        "地块5运营场景图",
    ],
    "07 技术推演与实施篇": [
        "AIGC技术推演过程图",
        "实施分期图",
        "运营管理建议图",
        "更新成效评估图",
    ],
}


UPLOAD_CHANNELS = [
    "卫星底图",
    "红线边界图",
    "GIS专题图",
    "道路矢量图",
    "建筑肌理图",
    "DEM分析图",
    "空间句法图",
    "现状照片",
    "风格参考图",
    "图例参考图",
]


UPLOAD_REFERENCE_TEXT = {
    "卫星底图": "请严格参考上传的卫星底图作为空间基础，不得改变研究范围的空间关系、道路走向和主要建筑肌理。",
    "红线边界图": "请严格保持上传红线图中的研究范围边界和五个重点地块边界，不得扩大、缩小、旋转、偏移或重新解释边界。",
    "GIS专题图": "请严格依据上传 GIS 专题图中的分类、范围和图例逻辑进行视觉表达，不得自行新增不存在的数据分区。",
    "道路矢量图": "请严格保持上传道路矢量图中的道路等级、走向、交叉口和街区路网结构，不得自行增删主要道路。",
    "建筑肌理图": "请严格参考上传建筑肌理图中的建筑轮廓、建筑密度和街区肌理，建筑轮廓需基本一致。",
    "DEM分析图": "请参考上传 DEM 分析图中的地形、生态、雨洪或风险关系，不得虚构地形起伏和生态边界。",
    "空间句法图": "请严格参考上传空间句法图中的整合度、选择度或可达性分级，仅进行符号和版式美化。",
    "现状照片": "请参考上传现状照片中的建筑风貌、街道界面、空间尺度和材料质感，进行更新后的视觉表达。",
    "风格参考图": "请仅参考上传风格图的版式、色彩和表现气质，不得借用其空间边界、地名或具体建筑布局。",
    "图例参考图": "请参考上传图例参考图中的颜色、符号和分类表达，保持图面与图例一致。",
}


PRECISION_ONE = {
    "研究范围图",
    "研究范围与5个重点地块图",
    "用地现状分析图",
    "AI诊断用地现状图",
    "建筑现状分析图",
    "建筑高度现状图",
    "道路交通现状图",
    "土地利用规划图",
    "总平面图",
    "功能布局规划图",
    "建筑更新控制图",
    "建筑高度控制图",
    "开发强度控制图",
    "道路交通系统规划图",
    "重点地块平面深化图",
}

PRECISION_TWO = {
    "区位分析图",
    "周边关系图",
    "公共交通覆盖图",
    "慢行系统现状图",
    "公共空间现状图",
    "绿地与生态现状图",
    "空间句法可达性分析图",
    "POI功能活力分析图",
    "人群活动热力图",
    "环境品质问题地图",
    "遗产价值评估热力图",
    "风貌敏感度评价图",
    "更新潜力评价图",
    "保护与更新冲突图",
    "综合评价分区图",
    "公共空间系统图",
    "绿地景观系统图",
    "历史文化展示系统图",
    "更新模式分区图",
    "功能策划图",
    "空间结构规划图",
    "5个重点地块定位图",
    "建筑风貌识别图",
    "历史建筑与工业遗产分布图",
    "社交媒体情感分析图",
    "老龄社区分布图",
    "四大问题诊断总图",
    "小街区密路网规划图",
    "公共交通与换乘图",
    "风貌控制图",
    "夜景照明与导视系统图",
    "实施分期图",
    "运营管理建议图",
    "更新成效评估图",
}

PRECISION_THREE = {
    "封面",
    "目录",
    "项目背景图",
    "技术路线图",
    "数字孪生技术框架图",
    "数据来源图",
    "设计理念图",
    "更新目标体系图",
    "总体策略图",
    "AIGC技术推演过程图",
    "鸟瞰效果图",
    "人视效果图",
    "运营场景图",
}


NEGATIVE_COMMON = (
    "不要卡通风，不要漫画风，不要儿童插画风，不要过度赛博朋克，不要旅游宣传海报风，"
    "不要房地产广告风，不要虚构城市天际线，不要虚构道路，不要虚构地名，不要改变研究范围边界，"
    "不要改变五个重点地块边界，不要改变道路走向，不要改变建筑肌理，不要错误比例尺，不要错误指北针，"
    "不要乱码中文，不要大段难以阅读的文字，不要杂乱排版，不要低清晰度，不要无关人物占据画面。"
)
NEGATIVE_BY_PRECISION = {
    "一级精度": "不要修改底图，不要重新绘制错误边界，不要改变道路结构，不要改变建筑轮廓，不要移动重点地块，不要虚构用地分类，不要虚构数据，不要生成与上传 GIS 图不一致的分析结果。",
    "二级精度": "不要虚构热力数据，不要虚构评价等级，不要生成无依据的分析结论，不要让图例与图面不一致，不要将示意图伪装成真实数据图。",
    "三级精度": "不要过度装饰，不要脱离城市规划语境，不要变成纯科技海报，不要变成商业宣传图，不要让历史建筑形象喧宾夺主。",
}

UNIFIED_STYLE = (
    "整体采用蓝黑色底极简专业风，深蓝黑色背景，青蓝色发光线条，白色中文标题，少量英文辅助。"
    "历史文化重点使用暖金色，问题识别与预警使用红橙黄色，生态绿地和公共空间使用低饱和青绿色。"
    "整体图面简洁、理性、专业、高清，适合城市规划毕业设计图册、A1展板和方案汇报PPT。"
)

FRAME_SYSTEM = (
    "画面中应保留统一图框系统，包括标题栏、编号系统、指北针、比例尺、坐标系、缩略图、图例区和信息框。"
    "图框风格应简洁克制，使用青蓝色细线和半透明信息面板，不要喧宾夺主。"
)


@dataclass(frozen=True)
class DrawingProfile:
    name: str
    drawing_type: str
    precision: str
    required_uploads: List[str]
    allows_ai_expression: bool
    needs_real_data: bool
    requires_standard_frame: bool


@dataclass(frozen=True)
class ImagePromptRequest:
    chapter: str
    drawing_name: str
    drawing_type: str
    aspect_ratio: str
    output_scene: str
    uploaded_channels: Sequence[str]
    main_expression: str = ""
    must_include: str = ""
    legend_content: str = ""
    key_plots: str = ""
    design_strategy: str = ""
    analysis_conclusion: str = ""
    emphasized_problem: str = ""
    emphasized_advantage: str = ""
    avoid_content: str = ""
    layout_structure: str = "地图主图 + 右侧图例 + 底部信息框"
    style_system: str = UNIFIED_STYLE
    text_rules: str = "中文文字使用微软雅黑风格，英文辅助使用 Times New Roman 风格，只生成清晰标题和少量关键词；信息不完整处使用占位符，避免乱码。"
    mark_as_schematic: bool = False
    use_existing_results: bool = True
    evidence_blocks: Dict[str, str] = None


@dataclass(frozen=True)
class PromptBuildResult:
    can_generate: bool
    prompt: str
    negative_prompt: str
    profile: DrawingProfile
    missing_items: List[str]
    notices: List[str]
    template_only: bool = False


def get_drawing_profile(drawing_name: str) -> DrawingProfile:
    """Infer type, precision level, and upload requirements for a drawing."""
    normalized = _normalize_plot_detail_name(drawing_name)
    precision = _infer_precision(normalized)
    drawing_type = _infer_drawing_type(normalized)
    required_uploads = _infer_required_uploads(normalized, precision)
    allows_ai_expression = precision == "三级精度"
    needs_real_data = precision in ("一级精度", "二级精度")
    requires_standard_frame = not any(key in normalized for key in ("封面", "目录", "鸟瞰", "人视", "运营场景", "效果"))
    return DrawingProfile(
        name=drawing_name,
        drawing_type=drawing_type,
        precision=precision,
        required_uploads=required_uploads,
        allows_ai_expression=allows_ai_expression,
        needs_real_data=needs_real_data,
        requires_standard_frame=requires_standard_frame,
    )


def build_image_prompt(request: ImagePromptRequest) -> PromptBuildResult:
    profile = get_drawing_profile(request.drawing_name)
    missing, notices, template_only = check_prompt_completeness(request, profile)
    if missing and profile.precision == "一级精度":
        reason = "该图纸属于一级精度图纸，必须上传真实底图和边界数据。"
        return PromptBuildResult(
            can_generate=False,
            prompt="",
            negative_prompt="",
            profile=profile,
            missing_items=missing,
            notices=[reason] + notices,
            template_only=False,
        )
    mandatory_missing = [item for item in missing if item not in UPLOAD_CHANNELS]
    if mandatory_missing and profile.precision == "二级精度":
        reason = "该图纸属于二级精度图纸，缺少必要主题或表达内容，暂不生成提示词。"
        return PromptBuildResult(
            can_generate=False,
            prompt="",
            negative_prompt="",
            profile=profile,
            missing_items=missing,
            notices=[reason] + notices,
            template_only=template_only,
        )
    if missing and profile.precision == "三级精度":
        reason = "该图纸属于三级精度图纸，可生成概念表达提示词，但当前缺少图纸主题、版式或输出比例。"
        return PromptBuildResult(
            can_generate=False,
            prompt="",
            negative_prompt="",
            profile=profile,
            missing_items=missing,
            notices=[reason] + notices,
            template_only=False,
        )

    negative_prompt = build_negative_prompt(profile.precision)
    prompt = _compose_prompt(request, profile, negative_prompt, template_only)
    return PromptBuildResult(
        can_generate=True,
        prompt=prompt,
        negative_prompt=negative_prompt,
        profile=profile,
        missing_items=missing,
        notices=notices,
        template_only=template_only,
    )


def check_prompt_completeness(request: ImagePromptRequest, profile: DrawingProfile = None):
    profile = profile or get_drawing_profile(request.drawing_name)
    uploaded = set(request.uploaded_channels or [])
    missing = []
    notices = []
    template_only = False

    for channel in profile.required_uploads:
        if channel not in uploaded:
            missing.append(channel)

    if profile.precision == "一级精度":
        if not _has_text(request.main_expression):
            missing.append("本图主要表达")
        if _requires_legend(profile.name) and not _has_text(request.legend_content):
            missing.append("图例内容 / 分类标准")
        if profile.name == "规划指标表" and not _has_text(request.analysis_conclusion):
            missing.append("规划指标数据")
        if not _has_text(request.output_scene):
            missing.append("图纸用途")
        if not _has_text(request.aspect_ratio):
            missing.append("画面比例")
        if missing:
            notices.append("缺少必要底图或分类信息时，系统不会强行生成 Image 2.0 提示词。")

    elif profile.precision == "二级精度":
        data_channels = {"GIS专题图", "空间句法图", "图例参考图", "道路矢量图"}
        if not uploaded.intersection(data_channels):
            template_only = True
            notices.append("该图纸属于二级精度图纸，当前缺少真实数据支撑；可生成版式提示词，但不能生成具体分析结论。")
        if not _has_text(request.main_expression):
            missing.append("本图主要表达")
        if not _has_text(request.legend_content):
            notices.append("建议补充图例分类；否则提示词将要求使用占位符。")

    else:
        if not _has_text(request.main_expression):
            missing.append("图纸主题 / 本图主要表达")
        if not _has_text(request.layout_structure):
            missing.append("版式结构")
        if not _has_text(request.aspect_ratio):
            missing.append("画面比例")

    missing = _dedupe(missing)
    return missing, notices, template_only


def build_negative_prompt(precision: str) -> str:
    return f"{NEGATIVE_COMMON}{NEGATIVE_BY_PRECISION.get(precision, '')}"


def revise_prompt_by_rating(prompt: str, rating: str, issue_types: Iterable[str]) -> str:
    issue_types = set(issue_types or [])
    additions = []
    if rating == "A级：可直接放入图册":
        additions.append("保留当前提示词结构与风格，后续相似图纸优先继承该版式、色彩和图框系统。")
    if rating == "B级：需要轻微后期修改":
        additions.append("在保持原提示词主体不变的前提下，仅针对以下问题进行局部强化。")
    if rating == "C级：只适合作为背景或灵感":
        additions.append("保留可用的画面风格，但重新强化图纸结构、底图约束、图例逻辑和内容层级。")
    if rating == "D级：不可用，需要重生成":
        additions.append("废弃当前图面结果，回到完整性检查；重新确认图纸类型、底图、精度等级、图例和核心内容后再生成。")

    if "边界不准" in issue_types:
        additions.append("必须严格保持上传红线图边界；不得改变研究范围形状，不得改变五个重点地块位置，不得对边界进行艺术化处理。")
    if "图面太杂" in issue_types or "信息太密" in issue_types:
        additions.append("减少装饰元素，保留主要模块和核心图面；文字以短标签为主，增加留白，降低背景纹理透明度。")
    if "文字不准" in issue_types or "文字乱码" in issue_types:
        additions.append("只生成一级标题和少量关键词，其余文字使用占位符；避免长句说明，后期由用户在 PS / AI / PPT 中替换正式文字。")
    if "风格不一致" in issue_types or "颜色不统一" in issue_types:
        additions.append("保持蓝黑色底极简专业风；深蓝黑背景、青蓝色线条、白色文字、暖金色历史重点、红橙黄色问题预警、低饱和青绿色生态表达。")
    if "数据不真实" in issue_types or "图例不准" in issue_types:
        additions.append("必须基于上传 GIS 图和专题数据，不得虚构统计数值，不得生成不存在的分析分区；不确定内容使用“示意”或占位符。")
    if "画面太空" in issue_types:
        additions.append("强化主图层级和必要信息框，补充图例、编号、研究范围缩略图和关键策略标签，但不要增加无依据内容。")
    if "清晰度不足" in issue_types:
        additions.append("提高线条边缘清晰度、文字可读性和图例分辨率，输出 4K 超清、适合打印、具有 300dpi 视觉效果。")

    if not additions:
        return prompt
    return prompt.rstrip() + "\n\n【根据成图评级追加修正】\n" + "\n".join(f"- {item}" for item in additions)


def flatten_chapter_drawings() -> List[str]:
    drawings = []
    for names in BOOK_CHAPTERS.values():
        drawings.extend(names)
    return drawings


def _compose_prompt(request: ImagePromptRequest, profile: DrawingProfile, negative_prompt: str, template_only: bool) -> str:
    uploaded = [channel for channel in UPLOAD_CHANNELS if channel in set(request.uploaded_channels or [])]
    upload_text = "\n".join(f"- {UPLOAD_REFERENCE_TEXT[channel]}" for channel in uploaded) or "- 当前未上传底图；仅可生成概念或版式提示词，不得虚构真实空间信息。"
    frame_text = FRAME_SYSTEM if profile.requires_standard_frame else "封面、目录或效果类图纸不强制加入完整图框，可保留克制的标题与必要项目信息。"
    schematic_text = "请在图面角落明确标注“示意 / Diagrammatic expression”。" if request.mark_as_schematic or template_only else ""
    evidence_text = _format_evidence(request.evidence_blocks or {}, enabled=request.use_existing_results)
    content_text = _format_content_block(request)
    template_prefix = "这是一条视觉表达模板提示词，不能输出具体评价等级、热力强弱或统计结论。" if template_only else ""

    body = f"""生成一张{request.aspect_ratio}城市规划毕业设计“{request.drawing_name}”图册图纸，用于{request.output_scene}，图纸类型为{profile.drawing_type}。

项目名称为“{PROJECT_DEFAULTS['project_cn']}”。项目地点为{PROJECT_DEFAULTS['location']}，研究范围为{PROJECT_DEFAULTS['scope']}，总用地面积{PROJECT_DEFAULTS['area']}，核心地标包括{PROJECT_DEFAULTS['landmarks']}。项目主题包括{PROJECT_DEFAULTS['themes']}。

{template_prefix}
本图属于{profile.precision}图纸。{_precision_rule_text(profile)}

【上传底图与资料引用】
{upload_text}

【现有数据与分析结果参考】
{evidence_text}

【图纸核心内容】
{content_text}

【版式结构】
版式采用{request.layout_structure}。图面需形成清晰的信息层级：主图优先，策略标签次之，图例和说明辅助。避免让装饰性元素压过真实数据和空间关系。

【图例与标注】
图例内容包括：{request.legend_content or '使用占位符标注图例分类，等待用户后期替换。'}。必须出现的重点地块或空间对象：{request.key_plots or '五个重点地块、研究范围边界、主要道路和伪满皇宫周边核心节点。'}。{schematic_text}

【风格与图框】
{request.style_system or UNIFIED_STYLE}
{frame_text}

【文字规则】
{request.text_rules}

【输出规格】
输出 4K 超清画质，适合打印，具有 300dpi 视觉效果；整体简洁、理性、专业，适合 A3 横版图册、A1 展板和方案汇报 PPT。

【负面要求】
{negative_prompt}"""

    return f"【{request.drawing_name}】\n\n完整提示词：\n{body.strip()}"


def _format_content_block(request: ImagePromptRequest) -> str:
    lines = [
        f"- 本图主要表达：{request.main_expression or '围绕图纸主题进行概念表达，不得虚构真实数据。'}",
        f"- 必须出现的内容：{request.must_include or '研究范围、核心地标、主要道路、重点地块、关键策略标签。'}",
        f"- 设计策略：{request.design_strategy or '将问题诊断、价值评估与多主体博弈共识转译为空间响应。'}",
        f"- 分析结论：{request.analysis_conclusion or '如信息不完整，请使用占位符，不要虚构结论。'}",
        f"- 需要强调的问题：{request.emphasized_problem or '交通割裂、用地混杂、公共空间不足、历史风貌保护与开发强度冲突。'}",
        f"- 需要强调的优势：{request.emphasized_advantage or '伪满皇宫历史文化资源、长春站 TOD 潜力、伊通河生态联系、老城复兴示范价值。'}",
        f"- 需要避免的内容：{request.avoid_content or '避免虚构边界、虚构道路、虚构政策、虚构统计数据和大段不可读文字。'}",
    ]
    return "\n".join(lines)


def _format_evidence(evidence_blocks: Dict[str, str], enabled: bool = True) -> str:
    if not enabled:
        return "本次不嵌入前序阶段结果，仅依据用户填写字段生成。"
    cleaned = []
    for title, value in evidence_blocks.items():
        if _has_text(value):
            clipped = " ".join(str(value).split())[:420]
            cleaned.append(f"- {title}：{clipped}")
    if not cleaned:
        return "暂无可引用的阶段成果；图面中不生成具体数据结论，只保留占位符和示意表达。"
    return "\n".join(cleaned)


def _precision_rule_text(profile: DrawingProfile) -> str:
    if profile.precision == "一级精度":
        return "必须严格依据上传底图，不允许 AI 改变边界、道路、地块形状和空间关系；不得改变研究范围边界、五个重点地块边界、道路关系、建筑轮廓和用地分类。"
    if profile.precision == "二级精度":
        return "必须基于真实数据或已上传专题图，但允许在图面表达、色彩、符号和版式上进行视觉美化；缺少数据时只能生成视觉表达模板。"
    return "以概念表达、风格表达和图册视觉为主，允许 AI 适度发挥，但不能虚构真实地理位置、道路、地块和数据。"


def _infer_precision(name: str) -> str:
    if name in PRECISION_ONE or "平面深化" in name:
        return "一级精度"
    if name in PRECISION_TWO:
        return "二级精度"
    if name in PRECISION_THREE or any(key in name for key in ("封面", "目录", "理念", "目标", "策略", "技术", "鸟瞰", "人视", "运营场景", "效果")):
        return "三级精度"
    if any(key in name for key in ("规划", "控制", "道路", "建筑", "用地", "范围")):
        return "一级精度"
    if any(key in name for key in ("热力", "评价", "分区", "系统", "覆盖", "活力", "诊断", "现状")):
        return "二级精度"
    return "三级精度"


def _infer_drawing_type(name: str) -> str:
    rules = [
        (("封面", "目录"), "封面类"),
        (("研究范围", "区位", "周边关系"), "研究范围类"),
        (("现状", "道路交通", "建筑", "用地", "公共空间", "绿地", "慢行", "交通覆盖"), "现状分析类"),
        (("AI诊断", "诊断总图", "问题地图"), "AI诊断类"),
        (("价值", "敏感度", "潜力", "冲突", "综合评价"), "价值评估类"),
        (("策略", "目标", "功能策划", "空间结构", "定位"), "策略生成类"),
        (("总平面", "土地利用", "功能布局", "控制", "系统图", "规划指标"), "总体规划类"),
        (("地块", "街道断面", "改造前后", "运营场景"), "重点地块深化类"),
        (("技术", "实施", "运营管理", "成效评估", "数据来源", "数字孪生"), "技术推演类"),
    ]
    for keywords, drawing_type in rules:
        if any(keyword in name for keyword in keywords):
            return drawing_type
    return "标准图纸类"


def _infer_required_uploads(name: str, precision: str) -> List[str]:
    if precision == "三级精度":
        if any(key in name for key in ("鸟瞰", "人视", "效果", "改造前后", "运营场景")):
            return ["现状照片", "风格参考图"]
        return []

    required = []
    if precision == "一级精度":
        required.extend(["卫星底图", "红线边界图"])
    else:
        required.extend(["红线边界图"])

    if any(key in name for key in ("用地", "土地利用", "功能布局", "评价", "分区", "热力", "活力", "问题", "诊断", "公共空间", "绿地")):
        required.append("GIS专题图")
    if any(key in name for key in ("道路", "交通", "慢行", "路网", "换乘", "可达性")):
        required.append("道路矢量图")
    if any(key in name for key in ("空间句法", "可达性")):
        required.append("空间句法图")
    if any(key in name for key in ("建筑", "高度", "风貌", "总平面", "鸟瞰", "肌理")):
        required.append("建筑肌理图")
    if "总平面" in name:
        required.append("GIS专题图")
    if any(key in name for key in ("重点地块", "地块")):
        required.append("红线边界图")
    if _requires_legend(name):
        required.append("图例参考图")
    return _dedupe(required)


def _requires_legend(name: str) -> bool:
    return not any(key in name for key in ("封面", "目录", "鸟瞰", "人视", "效果", "运营场景"))


def _normalize_plot_detail_name(name: str) -> str:
    for idx in range(1, 6):
        name = name.replace(f"地块{idx}", "重点地块")
    return name


def _has_text(value) -> bool:
    return bool(str(value or "").strip())


def _dedupe(items: Iterable[str]) -> List[str]:
    result = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
