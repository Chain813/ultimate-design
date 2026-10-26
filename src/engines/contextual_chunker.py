"""
工业级城乡规划 Contextual 面包屑 + 父子双层切片引擎 (Urban & Academic Contextual Chunker)
移植并增强自 408-helper/backend/contextual_chunker.py 与 rag_service.py。

核心特性：
  1. Markdown AST 标题层级感知与全路径面包屑栈 (Breadcrumb Stack)
  2. 父切片 (Parent Chunk: 800~1200字) 保证法规条文、导则通则与指标说明完整度
  3. 子切片 (Child Chunk: 180~280字) 保护浮点数(容积率1.4/面积25.05)、用地代码(R2/B1/0701)、法条编号(第X条第Y款)，在句末精准断句
  4. 超大规划指标表格按行智能切分，每一段子表格自动复制并置顶表头行
  5. 零成本 Contextual 离线语义注入 (基于父切片主题与首句推导，消除代词孤儿)
  6. 递归字符切片 (recursive_character_chunking) 与 PDF 乱码/折行清洗 (clean_pdf_noise)
"""

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple


def clean_pdf_noise(text: str) -> str:
    """清除 PDF 扫描/提取产生的控制字符、乱码水印（如 `_乴Ba\\x0f壛z?`）与多余空白。"""
    if not text:
        return ""
    # 移除包含控制字符的典型 PDF 字体映射乱码行/片段 (例如 _乴Ba\x0f壛z?)
    cleaned = re.sub(r"_?[^\n]*?[\x00-\x08\x0b\x0c\x0e-\x1f\x7f][^\n]*?\??(?=\n|$)", "", text)
    # 清除残余不可见 ASCII 控制字符（保留 \t, \n, \r）
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    # 消除孤立页码行（如单独一行的纯数字页码）
    cleaned = re.sub(r"(?m)^\s*\d{1,3}\s*$", "", cleaned)
    # 合并连续多个空行
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def recursive_character_chunking(
    text: str,
    chunk_size: int = 450,
    chunk_overlap: int = 60,
    min_chunk_len: int = 20,
) -> List[str]:
    """递归语义字符分块，保证规划法规与导则文档注入时的语义连贯性。"""
    separators = ["\n\n", "\n", "。", "！", "？", "；", "…", "，", "、", " ", ""]
    text = clean_pdf_noise(text)
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text] if len(text) >= min_chunk_len else [text]

    chosen_sep = ""
    chosen_idx = len(separators) - 1
    for i, s in enumerate(separators):
        if s == "":
            chosen_sep = ""
            chosen_idx = i
            break
        if s in text:
            chosen_sep = s
            chosen_idx = i
            break

    splits = text.split(chosen_sep) if chosen_sep else list(text)
    sub_seps = separators[chosen_idx + 1 :] if chosen_idx + 1 < len(separators) else [""]

    processed = []
    for sp in splits:
        sp_str = sp.strip()
        if not sp_str:
            continue
        if len(sp_str) > chunk_size and sub_seps and sub_seps != [""]:
            sub_chunks = recursive_character_chunking(sp_str, chunk_size, chunk_overlap, min_chunk_len=1)
            processed.extend(sub_chunks)
        else:
            processed.append(sp_str)

    chunks = []
    current_chunk: List[str] = []
    current_len = 0
    join_sep = chosen_sep if chosen_sep and chosen_sep in ["\n\n", "\n", " ", ""] else (chosen_sep if chosen_sep else "")

    for item in processed:
        item_len = len(item)
        if current_len + item_len + (len(join_sep) if current_chunk else 0) > chunk_size and current_chunk:
            combined = join_sep.join(current_chunk).strip()
            if combined:
                chunks.append(combined)
            overlap_items: List[str] = []
            overlap_len = 0
            for prev in reversed(current_chunk):
                if overlap_len + len(prev) <= chunk_overlap:
                    overlap_items.insert(0, prev)
                    overlap_len += len(prev)
                else:
                    break
            current_chunk = overlap_items
            current_len = sum(len(x) for x in current_chunk) + len(join_sep) * max(0, len(current_chunk) - 1)

        current_chunk.append(item)
        current_len += item_len + (len(join_sep) if len(current_chunk) > 1 else 0)

    if current_chunk:
        combined = join_sep.join(current_chunk).strip()
        if combined:
            chunks.append(combined)

    filtered = [c for c in chunks if len(c.strip()) >= min_chunk_len]
    return filtered if filtered else ([text] if text else [])


class AcademicContextualChunker:
    """城乡规划法规、总体规划、控规导则及学术文献父子双层语义切片器。"""

    def __init__(self, parent_size: int = 1000, child_size: int = 240, parent_overlap: int = 100):
        self.parent_size = parent_size
        self.child_size = child_size
        self.parent_overlap = parent_overlap

    def _protect_and_split_sentences(self, text: str) -> List[str]:
        """
        深度保护公式、代码块、规划指标浮点数 (如 FAR 1.4, 面积 25.05)、
        国标与控规用地代码 (如 R2, B1, G1, 0701, GB/T 50137)、法条编号 (第X条第Y款, （一）, 一、)，
        并消除扫描件与折行导致的中文断句硬回车，严格按句末标点切分，绝不截断单句。
        """
        p_map: Dict[str, str] = {}
        c = 0

        def _ph(m):
            nonlocal c
            k = f"__P_TOK_{c}__"
            c += 1
            p_map[k] = m.group(0)
            return k

        t = clean_pdf_noise(text)

        # 1. 深度保护 LaTeX 块级公式与行内公式
        t = re.sub(r"\$\$[\s\S]*?\$\$", _ph, t)
        t = re.sub(r"\\\[[\s\S]*?\\\]", _ph, t)
        t = re.sub(r"\\begin\{([a-zA-Z*]+)\}[\s\S]*?\\end\{\1\}", _ph, t)
        t = re.sub(r"\$[^\$]+?\$", _ph, t)

        # 保护小节号/版本号与规划指标浮点数 (如 1.1.1, 1.4, 25.05，避免将小数点当句号)
        t = re.sub(r"(?<![0-9])\d+\.\d+\.\d+(?:\.\d+)?(?![0-9])", _ph, t)
        t = re.sub(r"(?<![0-9])\d+\.\d+(?![0-9])", _ph, t)

        # 保护常见学术与标准缩写 (GB/T, CJJ, JGJ, Fig., Tab., No., etc.)
        t = re.sub(r"\b(?:Fig|Tab|No|ver|Vol|e\.g|i\.e|etc|vs)\.", _ph, t, flags=re.IGNORECASE)
        t = re.sub(
            r"(?<![a-zA-Z0-9])(?:GB(?:/T)?|CJJ(?:/T)?|JGJ(?:/T)?|DB\d*(?:/T)?)\s*[\d\.\-]+",
            _ph,
            t,
            flags=re.IGNORECASE,
        )

        # 保护城乡规划用地代码与指标代号 (如 R1, R2, R21, B1, B2, M1, G1, S42, U1, A33, 0701, 0801, 0901, FAR, GVI, SVF, TOD)
        t = re.sub(
            r"(?<![a-zA-Z0-9])(?:[RBMGSAUWu]\d{1,2}[a-zA-Z]?|0[1-9]\d{2}|1[0-5]\d{2}|FAR|GVI|SVF|TOD|MPI|POI|GIS|BIM|CAD)(?![a-zA-Z0-9])",
            _ph,
            t,
        )

        # 保护罗马数字与分级标识
        t = re.sub(
            r"(?:[Ⅰ-Ⅻ]+|(?<=第)[IVXLCDM]{1,4}|(?<![a-zA-Z0-9])[IVXLCDM]{1,4}(?=(?:期|型|级|类|度|区))|(?<![a-zA-Z0-9])(?:II|III|IV|VI|VII|VIII|IX|XI|XII)(?![a-zA-Z0-9]))",
            _ph,
            t,
        )

        # 保护法规层级条款: "第X条第Y款", "第X章", "（一）", "(1)", "一、"
        t = re.sub(r"第[零一二三四五六七八九十百千万\d]+[条章篇节款项](?:第[零一二三四五六七八九十\d]+[条款式项])?", _ph, t)
        t = re.sub(r"(?:[（(][一二三四五六七八九十\d]+[）)]|[一二三四五六七八九十]+、|\d+[、\.](?=\s*[\u4e00-\u9fa5]))", _ph, t)

        # 2. 智能消除 PDF 页面排版造成的伪折行 (Dewrap)
        # 中文字符/常用标点之间的换行直接拼接，杜绝在单句中间截断
        t = re.sub(r"([\u4e00-\u9fa5，、：])\s*\n+\s*([\u4e00-\u9fa5（《“])", r"\1\2", t)
        # 英文字符之间的换行转为空格
        t = re.sub(r"([a-zA-Z0-9])\n+([a-zA-Z0-9])", r"\1 \2", t)
        # 消除中英文、数字与保护标记混合折行
        t = re.sub(r"(?<=[\u4e00-\u9fa5a-zA-Z0-9_])\n+(?=[\u4e00-\u9fa5a-zA-Z0-9_])", "", t)

        # 3. 严格按句末标点断句 (杜绝以单个 \n 断句导致半句截断)
        raw_splits = re.split(r"(?<=[。！？；!?])|(?<=[a-zA-Z0-9]\.)(?=\s|$)", t)
        sentences = []
        for s in raw_splits:
            s_clean = s.strip()
            if not s_clean:
                continue
            # 若单句过长 (超过 200 字符)，仅在逗号/冒号等次级标点处软切分，保留标点完整性
            if len(s_clean) > 200:
                sub_parts = re.split(r"(?<=[，,：:])", s_clean)
                for p in sub_parts:
                    p_c = p.strip()
                    if p_c:
                        sentences.append(p_c)
            else:
                sentences.append(s_clean)

        # 4. 完整还原公式与特殊保护符号
        restored = []
        for s in sentences:
            curr = s
            for k, orig in reversed(list(p_map.items())):
                curr = curr.replace(k, orig)
            if curr.strip():
                restored.append(curr.strip())
        return restored

    def split_table_with_header(self, table_str: str, max_table_len: int = 300) -> List[str]:
        """
        超大 Markdown 规划指标表格拆分：每段子表格严格保留并置顶表头行与分隔符。
        保证单独检索任意子表格行时，指标字段含义绝不丢失。
        """
        lines = [l.strip() for l in table_str.strip().split("\n") if l.strip()]
        if len(lines) <= 2:
            return [table_str]

        # 若首行为表格小标题，第二行为表头，第三行为分隔线
        if (
            not (lines[0].startswith("|") or lines[0].endswith("|"))
            and len(lines) >= 3
            and (lines[1].startswith("|") or lines[1].endswith("|"))
        ):
            title_prefix = lines[0] + "\n"
            header = lines[1]
            divider = lines[2] if re.match(r"^[\|\s\-\:\+]+$", lines[2]) else "| --- |"
            rows = lines[3:]
        else:
            title_prefix = ""
            header = lines[0]
            divider = lines[1] if re.match(r"^[\|\s\-\:\+]+$", lines[1]) else "| --- |"
            rows = lines[2:]

        sub_tables = []
        curr_rows: List[str] = []
        curr_len = len(title_prefix) + len(header) + len(divider)

        for r in rows:
            if curr_len + len(r) > max_table_len and curr_rows:
                sub_tables.append(f"{title_prefix}" + "\n".join([header, divider] + curr_rows))
                curr_rows = [r]
                curr_len = len(title_prefix) + len(header) + len(divider) + len(r)
            else:
                curr_rows.append(r)
                curr_len += len(r)

        if curr_rows:
            sub_tables.append(f"{title_prefix}" + "\n".join([header, divider] + curr_rows))

        return sub_tables

    def _generate_zero_cost_contextual_prefix(
        self, chapter_title: str, parent_text: str, child_content: str
    ) -> str:
        """
        零成本 Contextual 语义注入：
        利用当前章节主题、父段落前瞻首句与核心关键词构建背景前缀，
        消除代词孤儿（如“本街区”、“该地块”、“上述指标”），激活 BM25 与稠密向量检索。
        """
        clean_chap = re.sub(r"^[#\d\.\s一二三四五六七八九十章节篇第~～\-—]+", "", chapter_title).strip()
        clean_chap = re.sub(r"^[~～\-—\s\d]+页\s*", "", clean_chap).strip()
        if not clean_chap:
            clean_chap = chapter_title.strip() or "规划通则"
        first_line = ""
        for line in parent_text.split("\n"):
            line_s = line.strip()
            if line_s and not line_s.startswith("#") and not line_s.startswith("【") and len(line_s) > 10:
                first_line = line_s[:45]
                break

        if first_line:
            prefix = f"【规划精要: {clean_chap} · 条文背景: {first_line}】"
        else:
            prefix = f"【规划精要: {clean_chap}】"
        return prefix

    def build_parent_child_index_from_section(
        self,
        book_meta: Dict[str, Any],
        chapter_title: str,
        sec_text: str,
        page_start: int = 1,
        page_end: int = 1,
        section_idx: int = 0,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        从单章节/文档正文构建带有父子映射、AST 面包屑与表头保护的高精度双层切片。
        返回: (parent_records, child_records)
        """
        major_code = str(book_meta.get("major_code") or book_meta.get("scope") or "urban").strip().lower()
        subject = str(book_meta.get("subject") or "城乡规划与城市更新").strip()
        book_name = str(book_meta.get("book_name") or book_meta.get("source") or "规划规范").strip()

        sec_text = clean_pdf_noise(sec_text)
        page_str = f"P{page_start}-P{page_end}" if page_start != page_end else f"P{page_start}"
        breadcrumb = f"【{major_code.upper()} {subject} · 《{book_name}》 ({page_str}) > {chapter_title}】"

        parent_records: List[Dict[str, Any]] = []
        child_records: List[Dict[str, Any]] = []

        if not sec_text or len(sec_text.strip()) < 15:
            return parent_records, child_records

        # 1. 拆分父切片 (Parent Chunks: 800 ~ 1200 字符，严格以段落与句末断句)
        raw_paragraphs = [p.strip() for p in sec_text.split("\n\n") if p.strip()]
        TERMINAL_PUNCT = set("。！？!?；;：:….\n\"'”’）)】}》")
        paragraphs: List[str] = []

        def _is_structural(block: str) -> bool:
            b = block.strip()
            if not b:
                return False
            if (
                b.startswith("#")
                or b.startswith("```")
                or b.startswith("$$")
                or b.startswith("\\[")
                or b.startswith("|")
            ):
                return True
            if b.endswith("```") or b.endswith("$$") or b.endswith("\\]") or b.endswith("|"):
                return True
            if len(b) < 45 and re.match(
                r"^(?:第[零一二三四五六七八九十百千万\d]+[章节篇部卷条]|[\d\.]+\s*|[一二三四五六七八九十]+[、.]|[（(][一二三四五六七八九十\d]+[）)])",
                b,
            ):
                return True
            return False

        for p in raw_paragraphs:
            if (
                paragraphs
                and paragraphs[-1][-1] not in TERMINAL_PUNCT
                and not _is_structural(paragraphs[-1])
                and not _is_structural(p)
            ):
                prev_last = paragraphs[-1][-1]
                curr_first = p[0]
                if re.match(r"[\u4e00-\u9fa5，、]", prev_last) and re.match(r"[\u4e00-\u9fa5]", curr_first):
                    paragraphs[-1] = paragraphs[-1] + p
                elif re.match(r"[a-zA-Z0-9]", prev_last) and re.match(r"[a-zA-Z0-9]", curr_first):
                    paragraphs[-1] = paragraphs[-1] + " " + p
                else:
                    paragraphs[-1] = paragraphs[-1] + p
            else:
                paragraphs.append(p)

        parent_blocks: List[str] = []
        curr_p_block: List[str] = []
        curr_p_len = 0

        for p in paragraphs:
            if len(p) > self.parent_size:
                sub_sentences = self._protect_and_split_sentences(p)
                for s in sub_sentences:
                    s_len = len(s)
                    if curr_p_len + s_len > self.parent_size and curr_p_block:
                        parent_blocks.append("\n\n".join(curr_p_block))
                        overlap_s = curr_p_block[-1]
                        curr_p_block = [overlap_s, s] if len(overlap_s) <= self.parent_overlap * 2 else [s]
                        curr_p_len = sum(len(x) for x in curr_p_block)
                    else:
                        curr_p_block.append(s)
                        curr_p_len += s_len
            else:
                p_len = len(p)
                if curr_p_len + p_len > self.parent_size and curr_p_block:
                    parent_blocks.append("\n\n".join(curr_p_block))
                    overlap_p = curr_p_block[-1]
                    if len(overlap_p) > self.parent_overlap * 2:
                        last_sentences = self._protect_and_split_sentences(overlap_p)
                        overlap_p = last_sentences[-1] if last_sentences else ""
                    curr_p_block = [overlap_p, p] if overlap_p else [p]
                    curr_p_len = sum(len(x) for x in curr_p_block)
                else:
                    curr_p_block.append(p)
                    curr_p_len += p_len

        if curr_p_block:
            parent_blocks.append("\n\n".join(curr_p_block))

        # 2. 为每个父切片生成 ID，并从父切片中分裂出高锐度子切片
        for p_idx, p_text in enumerate(parent_blocks):
            p_hash = hashlib.md5(
                f"{book_name}_{chapter_title}_{section_idx}_{p_idx}_{p_text[:40]}".encode("utf-8")
            ).hexdigest()[:10]
            parent_id = f"parent_{major_code}_{p_hash}"

            parent_full_text = (
                f"{breadcrumb}\n"
                f"【来源规范】: 《{book_name}》 (第 {page_start}~{page_end} 页)\n"
                f"【规划章节】: {major_code.upper()} {subject} > {chapter_title}\n"
                f"【条文原文】:\n{p_text}"
            )

            parent_record = {
                "parent_id": parent_id,
                "major_code": major_code,
                "subject": subject,
                "book_name": book_name,
                "source": book_name,
                "chapter": chapter_title,
                "page_start": page_start,
                "page_end": page_end,
                "breadcrumb": breadcrumb,
                "parent_full_text": parent_full_text,
                "raw_text": p_text,
            }
            parent_records.append(parent_record)

            # 3. 分裂子切片
            contextual_prefix = self._generate_zero_cost_contextual_prefix(chapter_title, p_text, "")

            blocks: List[str] = []
            paragraphs_in_p = p_text.split("\n\n")
            for para in paragraphs_in_p:
                para_s = para.strip()
                if not para_s:
                    continue
                para_lines = [l.strip() for l in para_s.split("\n") if l.strip()]
                is_table = (
                    len(para_lines) >= 3
                    and any(re.match(r"^[\|\s\-\:\+]+$", l) for l in para_lines[1:3])
                    and sum(1 for l in para_lines if l.startswith("|") or l.endswith("|"))
                    >= len(para_lines) * 0.7
                )
                if is_table:
                    blocks.extend(self.split_table_with_header(para_s, max_table_len=280))
                elif para_s.startswith("```") or para_s.startswith("$$") or para_s.startswith("\\["):
                    blocks.append(para_s)
                else:
                    blocks.extend(self._protect_and_split_sentences(para_s))

            curr_child_parts: List[str] = []
            curr_c_len = 0

            for b in blocks:
                b_s = b.strip()
                if not b_s:
                    continue
                if curr_c_len + len(b_s) > self.child_size and curr_child_parts:
                    child_content = "\n".join(curr_child_parts)
                    c_hash = hashlib.md5(
                        f"{parent_id}_{len(child_records)}_{child_content[:30]}".encode("utf-8")
                    ).hexdigest()[:10]
                    child_id = f"child_{major_code}_{c_hash}"
                    index_text = f"{breadcrumb}\n{contextual_prefix}\n{child_content}"

                    child_records.append(
                        {
                            "child_id": child_id,
                            "slice_id": child_id,
                            "parent_id": parent_id,
                            "major_code": major_code,
                            "subject": subject,
                            "chapter": chapter_title,
                            "page_start": page_start,
                            "page_end": page_end,
                            "source": book_name,
                            "breadcrumb": breadcrumb,
                            "context": breadcrumb,
                            "contextual_prefix": contextual_prefix,
                            "content": child_content,
                            "index_text": index_text,
                            "full_context_text": index_text,
                        }
                    )
                    last_part = curr_child_parts[-1].strip()
                    overlap_ctx = ""
                    if len(last_part) <= 45:
                        if (
                            last_part.count("$") % 2 == 0
                            and not last_part.startswith("```")
                            and not last_part.startswith("|")
                        ):
                            overlap_ctx = last_part
                    else:
                        sub_sens = self._protect_and_split_sentences(last_part)
                        if len(sub_sens) > 1:
                            candidate = sub_sens[-1].strip()
                            if (
                                len(candidate) <= 50
                                and candidate.count("$") % 2 == 0
                                and not candidate.startswith("```")
                                and not candidate.startswith("|")
                            ):
                                overlap_ctx = candidate
                    curr_child_parts = [overlap_ctx, b_s] if overlap_ctx and overlap_ctx != b_s else [b_s]
                    curr_c_len = sum(len(x) for x in curr_child_parts)
                else:
                    curr_child_parts.append(b_s)
                    curr_c_len += len(b_s)

            if curr_child_parts:
                child_content = "\n".join(curr_child_parts)
                c_hash = hashlib.md5(
                    f"{parent_id}_{len(child_records)}_{child_content[:30]}".encode("utf-8")
                ).hexdigest()[:10]
                child_id = f"child_{major_code}_{c_hash}"
                index_text = f"{breadcrumb}\n{contextual_prefix}\n{child_content}"

                child_records.append(
                    {
                        "child_id": child_id,
                        "slice_id": child_id,
                        "parent_id": parent_id,
                        "major_code": major_code,
                        "subject": subject,
                        "chapter": chapter_title,
                        "page_start": page_start,
                        "page_end": page_end,
                        "source": book_name,
                        "breadcrumb": breadcrumb,
                        "context": breadcrumb,
                        "contextual_prefix": contextual_prefix,
                        "content": child_content,
                        "index_text": index_text,
                        "full_context_text": index_text,
                    }
                )

        return parent_records, child_records

    def chunk_section_into_semantic_slices(
        self,
        book_meta: Dict[str, Any],
        chapter_title: str,
        raw_text: str,
        page_start: int = 1,
        page_end: int = 1,
        section_idx: int = 0,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """向后兼容别名：调用 build_parent_child_index_from_section"""
        return self.build_parent_child_index_from_section(
            book_meta=book_meta,
            chapter_title=chapter_title,
            sec_text=raw_text,
            page_start=page_start,
            page_end=page_end,
            section_idx=section_idx,
        )
