"""
rebuild_rag.py — RAG 向量知识库全量重建脚本（工业级 Contextual 语义切片版）

功能：
1. 扫描 docs/ 目录下所有 PDF/DOCX/MD 文件
2. 使用 clean_pdf_noise 清除 PDF 字体乱码（如 `_乴Ba\\x0f壛z?`）与控制字符
3. 使用 AcademicContextualChunker / recursive_character_chunking 进行双层高锐度语义切片（保护浮点数、用地代码与法条编号）
4. 自动通过 classify_chunk_scope 标记切片作用域（national / city_statute / case_thesis）
5. 输出为统一的 data/rag_knowledge.json

运行方式：
    python tools/rebuild_rag.py
"""

import glob
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.engines.contextual_chunker import (
    AcademicContextualChunker,
    clean_pdf_noise,
    recursive_character_chunking,
)
from src.engines.rag_engine import classify_chunk_scope


def extract_pdf_text(filepath, max_pages=30):
    """从 PDF 中提取文本并清洗控制字符与扫描乱码"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        text = ""
        for i in range(min(max_pages, len(reader.pages))):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text += page_text + "\n"
        return clean_pdf_noise(text)
    except Exception as e:
        print(f"  ⚠️ PDF 读取失败 {filepath}: {e}")
        return ""


def extract_docx_text(filepath):
    """从 Word 文档中提取文本"""
    try:
        from docx import Document
        doc = Document(filepath)
        raw = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return clean_pdf_noise(raw)
    except Exception as e:
        print(f"  ⚠️ DOCX 读取失败 {filepath}: {e}")
        return ""


def extract_md_text(filepath):
    """从 Markdown 文件中提取文本"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return clean_pdf_noise(f.read())
    except Exception as e:
        print(f"  ⚠️ MD 读取失败 {filepath}: {e}")
        return ""


def chunk_text(text, source_name, chunk_size=500, overlap=80):
    """使用工业级 AcademicContextualChunker 与 recursive_character_chunking 将长文本切分为高锐度语义片段"""
    cleaned = clean_pdf_noise(text)
    if not cleaned:
        return {}

    scope_meta = classify_chunk_scope(source_name, cleaned)
    chunker = AcademicContextualChunker(parent_size=1000, child_size=chunk_size, parent_overlap=overlap)
    _, child_records = chunker.build_parent_child_index_from_section(
        book_meta={
            "major_code": scope_meta["scope"],
            "subject": "城乡规划与城市更新",
            "book_name": source_name,
        },
        chapter_title=source_name,
        sec_text=cleaned,
        page_start=1,
        page_end=1,
    )

    chunks = {}
    if child_records:
        for rec in child_records:
            content_body = rec.get("content", "").strip()
            if not content_body:
                continue
            chunk_id = hashlib.md5((source_name + content_body[:100]).encode("utf-8")).hexdigest()[:12]
            chunks[chunk_id] = {
                "source": source_name,
                "content": content_body,
                "scope": scope_meta["scope"],
                "city": scope_meta["city"],
            }
    else:
        for sl in recursive_character_chunking(cleaned, chunk_size=chunk_size, chunk_overlap=overlap):
            chunk_id = hashlib.md5((source_name + sl[:100]).encode("utf-8")).hexdigest()[:12]
            chunks[chunk_id] = {
                "source": source_name,
                "content": sl,
                "scope": scope_meta["scope"],
                "city": scope_meta["city"],
            }

    return chunks


def main():
    docs_dir = "docs"
    output_path = "data/rag_knowledge.json"

    all_chunks = {}
    file_count = 0

    print("=" * 60)
    print("🔬 RAG 知识库全量重建工具 (Contextual Chunker 工业级切片版)")
    print("=" * 60)

    # 扫描所有支持的文件类型
    for ext, extractor in [
        ("*.pdf", extract_pdf_text),
        ("*.docx", extract_docx_text),
        ("*.md", extract_md_text),
    ]:
        for filepath in glob.glob(os.path.join(docs_dir, ext)):
            basename = os.path.basename(filepath)

            # 跳过项目内部文档（非政策法规类）
            skip_prefixes = ["STAGE", "DEVELOPER", "PROJECT", "cursor_"]
            if any(basename.startswith(p) for p in skip_prefixes):
                print(f"  ⏭️ 跳过内部文档: {basename}")
                continue

            print(f"  📄 正在消化: {basename}")
            text = extractor(filepath)

            if text and len(text.strip()) > 50:
                chunks = chunk_text(text, basename)
                all_chunks.update(chunks)
                file_count += 1
                print(f"     ✅ 提取 {len(chunks)} 个语义切片")
            else:
                print("     ⚠️ 内容为空或过短，已跳过")

    # 写入输出
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print("✅ 知识库重建完成！")
    print(f"   文件数: {file_count}")
    print(f"   切片数: {len(all_chunks)}")
    print(f"   输出至: {output_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
