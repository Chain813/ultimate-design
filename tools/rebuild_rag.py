"""
rebuild_rag.py — RAG 向量知识库全量重建脚本

功能：
1. 扫描 docs/ 目录下所有 PDF/DOCX/MD 文件
2. 提取纯净文本并按段落切片
3. 输出为统一的 data/rag_knowledge.json

运行方式：
    python rebuild_rag.py
"""

import os
import json
import hashlib
import glob
from pathlib import Path


def extract_pdf_text(filepath, max_pages=30):
    """从 PDF 中提取文本"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        text = ""
        for i in range(min(max_pages, len(reader.pages))):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"  ⚠️ PDF 读取失败 {filepath}: {e}")
        return ""


def extract_docx_text(filepath):
    """从 Word 文档中提取文本"""
    try:
        from docx import Document
        doc = Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception as e:
        print(f"  ⚠️ DOCX 读取失败 {filepath}: {e}")
        return ""


def extract_md_text(filepath):
    """从 Markdown 文件中提取文本"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"  ⚠️ MD 读取失败 {filepath}: {e}")
        return ""


def chunk_text(text, source_name, chunk_size=500, overlap=80):
    """将长文本切分为可被 RAG 检索的语义片段"""
    chunks = {}
    lines = text.replace("\r", "").split("\n")
    buffer = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        buffer += line + "\n"
        
        if len(buffer) >= chunk_size:
            chunk_id = hashlib.md5((source_name + buffer[:100]).encode()).hexdigest()[:12]
            chunks[chunk_id] = {
                "source": source_name,
                "content": buffer.strip()
            }
            # 保留重叠部分以维护上下文连续性
            buffer = buffer[-overlap:] if len(buffer) > overlap else ""
    
    # 处理剩余内容
    if buffer.strip():
        chunk_id = hashlib.md5((source_name + buffer[:100]).encode()).hexdigest()[:12]
        chunks[chunk_id] = {
            "source": source_name,
            "content": buffer.strip()
        }
    
    return chunks


def main():
    docs_dir = "docs"
    output_path = "data/rag_knowledge.json"
    
    all_chunks = {}
    file_count = 0
    
    print("=" * 60)
    print("🔬 RAG 知识库全量重建工具")
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
                print(f"     ⚠️ 内容为空或过短，已跳过")
    
    # 写入输出
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"✅ 知识库重建完成！")
    print(f"   文件数: {file_count}")
    print(f"   切片数: {len(all_chunks)}")
    print(f"   输出至: {output_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
