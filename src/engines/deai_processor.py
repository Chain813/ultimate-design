"""降 AI 率后处理器 —— 降低毕业报告设计报告的 AIGC 检测率

核心策略（借鉴 AI-Cleaner、TextHumanize、Adversarial-Paraphrasing 等开源项目）：

1. 多模型指纹混淆 — 不同章节使用不同模型生成，打破单一模型特征
2. 风格扰动改写 — 第二遍 LLM 以"人类学生"身份重写
3. 中文 AI 模式打散 — 正则替换模板化句式、高频 AI 词汇
4. 个人观察注入 — 每章强制插入一条第一人称调研细节
5. 段落节奏扰动 — 随机化段落长度，打散句长均匀分布

Usage:
    from src.engines.deai_processor import deai_chapter, deai_all_chapters, DEAI_MODELS
    processed = deai_chapter(text, section_id="3.1", strategy="aggressive")
    all_processed = deai_all_chapters(chapters_dict)
"""

from __future__ import annotations

import random
import re
from collections.abc import Callable

from src.engines.llm_engine import call_llm_engine

# ═══════════════════════════════════════════════════════════════
# 多模型指纹混淆 — 不同章节使用不同模型
# ═══════════════════════════════════════════════════════════════

DEAI_MODELS = {
    "deepseek-v4-pro": "deepseek-v4-pro",
    "deepseek-v4-flash": "deepseek-v4-flash",
    "deepseek-chat": "deepseek-chat",
}

# 章节 → 模型分配（轮流使用不同模型打破单一指纹）
CHAPTER_MODEL_MAP: dict[str, str] = {}
_available_models = list(DEAI_MODELS.values())


def _assign_models():
    """为 27 个小节随机分配模型"""
    global CHAPTER_MODEL_MAP
    if CHAPTER_MODEL_MAP:
        return
    from src.engines.document_composer import REPORT_CHAPTERS
    for _i, sec in enumerate(REPORT_CHAPTERS):
        # 轮流分配，不同章用不同模型
        ch = sec.chapter
        CHAPTER_MODEL_MAP[sec.section_id] = _available_models[ch % len(_available_models)]


_assign_models()


# ═══════════════════════════════════════════════════════════════
# 中文 AI 高频模式库
# ═══════════════════════════════════════════════════════════════

# 模板化过渡词 → 替换词池
TRANSITION_REPLACEMENTS: dict[str, list[str]] = {
    "首先": ["最初，", "在调研初期，", "项目启动阶段，", "第一步，", "一开始，", "从头梳理，"],
    "其次": ["接着，", "进一步来看，", "在随后的分析中，", "另外，", "与此同时，", "继而，"],
    "最后": ["最终，", "综合各方面因素，", "经过多轮论证，", "落实到方案层面，", "收束来看，"],
    "综上所述": ["综合以上分析，", "梳理全部工作后，", "从整体来看，", "回顾整个设计过程，"],
    "通过分析发现": ["数据分析表明，", "从数据中可以看到，", "实地调查显示，", "空间测度揭示，"],
    "研究表明": ["既有文献指出，", "学术共识认为，", "前人研究总结，", "相关领域普遍认同，"],
    "值得注意的是": ["需要强调的是，", "尤其关键的是，", "不应忽视的是，", "更值得关注的一点是，"],
    "基于": ["立足于", "依托于", "以...为依据", "从...出发", "根据"],
    "赋能": ["提升", "增强", "激活", "助力", "驱动", "支撑"],
    "织补": ["缝合", "修补", "弥合", "衔接", "连通"],
    "触媒": ["催化剂", "引爆点", "启动器", "核心动力", "引擎"],
    "韧性": ["抗风险能力", "适应性", "恢复力", "弹性"],
}

# AI 高频结尾模式
AI_SENTENCE_ENDS = re.compile(
    r'(具有重要的\w+意义|'
    r'为\w+提供了\w+支撑|'
    r'实现了\w+的\w+提升|'
    r'推动了\w+的\w+发展|'
    r'展现出\w+的\w+特征)'
)

# 句长均匀化检测 — AI 倾向产出长度高度一致的句子
# 应对：随机插入短句（1-5字）打破均匀分布


def _random_short_sentence() -> str:
    """生成一个随机短句，用于插入段落间打破句长均匀分布"""
    short_sentences = [
        "这一点很关键。",
        "数据不会说谎。",
        "需要特别注意。",
        "实际情况更复杂。",
        "现场感受尤为直观。",
        "这个发现值得重视。",
        "不能一概而论。",
        "还有改进空间。",
        "具体问题具体分析。",
        "这条路走得通。",
    ]
    return random.choice(short_sentences)


# ═══════════════════════════════════════════════════════════════
# 个人观察素材库
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# Layer 1: 规则层 — 正则打散中文 AI 模式
# ═══════════════════════════════════════════════════════════════

def apply_rule_deai(text: str, intensity: float = 0.5) -> str:
    """应用规则层降 AI 处理（零 token 消耗）。

    Args:
        text: 输入文本
        intensity: 强度 0.0-1.0，越高改动越多

    Returns:
        处理后的文本
    """
    result = text

    # 1. 替换模板化过渡词
    for ai_word, replacements in TRANSITION_REPLACEMENTS.items():
        if ai_word in result and random.random() < intensity * 0.7:
            # 随机替换一定比例的出现
            count = result.count(ai_word)
            replace_count = max(1, int(count * intensity))
            positions = [m.start() for m in re.finditer(re.escape(ai_word), result)]
            for pos in random.sample(positions, min(replace_count, len(positions))):
                # 每次替换用不同的替代词
                replacement = random.choice(replacements)
                result = result[:pos] + replacement + result[pos + len(ai_word):]

    # 2. AI 高频结尾 → 随机改写
    if intensity > 0.3:
        for match in AI_SENTENCE_ENDS.finditer(result):
            if random.random() < intensity * 0.4:
                # 20-40% 概率替换
                result = result.replace(match.group(), _rewrite_ai_ending(match.group()), 1)

    # 3. 插入短句打破句长均匀分布
    if intensity > 0.4:
        paragraphs = result.split('\n')
        new_paragraphs = []
        for i, para in enumerate(paragraphs):
            new_paragraphs.append(para)
            # 每 3-5 段插入一个短句
            if len(para) > 80 and i % random.randint(3, 5) == 0 and random.random() < intensity:
                # 在段落中随机位置插入短句
                sentences = re.split(r'(?<=[。！？])', para)
                if len(sentences) > 3:
                    insert_pos = random.randint(1, len(sentences) - 1)
                    sentences.insert(insert_pos, _random_short_sentence())
                    new_paragraphs[-1] = ''.join(sentences)
        result = '\n'.join(new_paragraphs)

    return result


def _rewrite_ai_ending(ending: str) -> str:
    """改写 AI 高频结尾句式"""
    alternatives = {
        "具有重要的意义": ["意义重大", "影响深远", "不容忽视", "值得深思"],
        "提供了有力支撑": ["奠定了坚实基础", "创造了有利条件", "提供了关键依据"],
        "实现了显著提升": ["改善明显", "有了质的变化", "取得了长足进步"],
        "推动了持续发展": ["注入了新的活力", "拓展了发展空间", "迎来了新的契机"],
    }
    for pattern, alts in alternatives.items():
        if pattern in ending:
            return ending.replace(pattern, random.choice(alts))
    return ending


# ═══════════════════════════════════════════════════════════════
# Layer 2: LLM 层 — 风格扰动改写
# ═══════════════════════════════════════════════════════════════

DEAI_SYSTEM_PROMPT = """你是一个文本风格调整工具。你的任务是对给定的学术文本进行句式层面的微调，
使其句长和段落节奏看起来更自然，但严格保持原文的信息内容不变。

## 可以做的（仅限句式层面）：
1. 调整句子长度：拆分过长的句子（>40字），合并过短的句子（<5字连续出现）
2. 调整段落长度：确保段落长短有变化（2-6句不等）
3. 替换模板化过渡词："首先"→"在规划初期，"/"此外"→"同时，"等
4. 微调语序使表达更紧凑，但不改变含义

## 绝对禁止（违反即失败）：
1. 不得添加原文中没有的数据、数字、地名、人名、日期、法规编号
2. 不得添加任何个人观察、个人经历、个人感受（如"笔者走访""实地发现""给人印象"）
3. 不得添加评价性语言（如"具有重要意义""影响深远""值得关注"）
4. 不得改变原文的任何结论、数据或事实陈述
5. 不得删除原文中的任何数据
6. 不得添加新的案例、引用或参考文献
7. 不得使用"赋能""织补""触媒""韧性"等AI高频词

只输出改写后的正文，不要加任何说明。"""


def deai_llm_rewrite(text: str, section_id: str = "", model: str = "deepseek-v4-flash") -> str:
    """LLM 风格扰动 — 用不同模型以"学生"身份重写

    Args:
        text: 原始 LLM 生成文本
        section_id: 章节编号
        model: 用于改写的模型（应与生成模型不同以打破指纹）

    Returns:
        改写后的文本
    """
    # 选取与生成时不同的模型
    rewrite_model = model
    if section_id in CHAPTER_MODEL_MAP and CHAPTER_MODEL_MAP[section_id] == model:
        # 用不同模型改写
        alt_models = [m for m in _available_models if m != model]
        rewrite_model = alt_models[0] if alt_models else model

    prompt = f"""请对以下学术文本进行句式层面的微调，使句长和段落节奏更自然。

【章节】{section_id}
【原文】
{text}

改写要求（仅限句式层面，不得改变信息内容）：
- 拆分过长句子（>40字），合并连续出现的过短句子（<5字）
- 段落长短有变化（2-6句不等），不要每段都一样长
- 替换模板化过渡词（"首先""其次""最后""综上所述"等）
- 避免使用"赋能""织补""触媒""韧性"等AI高频词
- 句子长度自然变化，不要所有句子都一样长

【绝对禁止】
- 不得添加原文中没有的数据、地名、人名、数字、日期
- 不得添加任何个人观察或个人经历（如"笔者""实地走访""调研发现"）
- 不得添加评价性语言
- 不得改变原文的任何结论或事实

只输出改写后的正文。"""

    result = call_llm_engine(
        prompt=prompt,
        system_prompt=DEAI_SYSTEM_PROMPT,
        model=rewrite_model,
    )

    if result and len(result) > 30:
        return result.strip()
    return text  # 改写失败返回原文


# ═══════════════════════════════════════════════════════════════
# Layer 3: 个人观察注入
# ═══════════════════════════════════════════════════════════════

def inject_personal_observation(text: str, chapter: int) -> str:
    """⚠️ 已废弃 — 不再注入虚假个人观察。保留函数签名以兼容旧调用。"""
    return text


# ═══════════════════════════════════════════════════════════════
# 主编排函数
# ═══════════════════════════════════════════════════════════════

def deai_chapter(
    text: str,
    section_id: str = "",
    chapter: int = 0,
    intensity: float = 0.7,
    model: str = "deepseek-v4-flash",
) -> str:
    """对单个章节执行完整降 AI 处理管线

    Args:
        text: 原始文本
        section_id: 章节编号（如 "3.1"）
        chapter: 所属章号（1-5）
        intensity: 处理强度 0.0-1.0
        model: 原始生成模型（用于选择不同的改写模型）

    Returns:
        处理后的文本
    """
    if not text or len(text) < 50:
        return text

    result = text

    # Layer 1: 规则层（零成本）
    result = apply_rule_deai(result, intensity=min(intensity, 0.8))

    # Layer 2: LLM 风格扰动（主要降 AI 率手段）
    if intensity > 0.3 and len(result) > 100:
        result = deai_llm_rewrite(result, section_id=section_id, model=model)

    return result


def deai_all_chapters(
    chapters: dict[str, str],
    intensity: float = 0.7,
    progress_callback: Callable[[int, int, str], None] | None = None,
    log_callback: Callable[[str], None] | None = None,
) -> dict[str, str]:
    """对全部章节执行降 AI 处理

    Args:
        chapters: {section_id: text}
        intensity: 处理强度
        progress_callback: 进度回调
        log_callback: 日志回调

    Returns:
        处理后的 chapters dict
    """
    from src.engines.document_composer import REPORT_CHAPTERS

    # 构建 section_id → chapter 映射
    section_chapter = {sec.section_id: sec.chapter for sec in REPORT_CHAPTERS}

    processed: dict[str, str] = {}
    items = list(chapters.items())
    total = len(items)

    for i, (sid, text) in enumerate(items):
        if progress_callback:
            progress_callback(i, total, f"降AI {sid}")

        try:
            ch = section_chapter.get(sid, 0)
            orig_model = CHAPTER_MODEL_MAP.get(sid, "deepseek-v4-pro")
            result = deai_chapter(text, section_id=sid, chapter=ch, intensity=intensity, model=orig_model)
            processed[sid] = result
            if log_callback:
                orig_len = len(text)
                new_len = len(result)
                log_callback(f"  ✅ {sid} 降AI完成 ({orig_len}→{new_len} 字)")
        except Exception as e:
            processed[sid] = text  # 失败保留原文
            if log_callback:
                log_callback(f"  ⚠️ {sid} 降AI失败，保留原文: {e}")

    return processed


def deai_acknowledgments(text: str) -> str:
    """处理致谢部分的降 AI（仅做句式微调，不注入虚假内容）"""
    if not text or len(text) < 50:
        return text
    # 仅做规则层处理，不注入任何虚假个人经历
    return apply_rule_deai(text, intensity=0.3)
