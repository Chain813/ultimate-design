import os
import glob
from pypdf import PdfReader
from docx import Document

def extract_pdf_txt(path, max_pages=10):
    text = ""
    try:
        reader = PdfReader(path)
        for i in range(min(max_pages, len(reader.pages))):
            text += reader.pages[i].extract_text() + "\n"
    except Exception as e:
        text = f"Error reading PDF {path}: {str(e)}"
    return text

def extract_docx_txt(path):
    text = ""
    try:
        doc = Document(path)
        for p in doc.paragraphs:
            text += p.text + "\n"
    except Exception as e:
        text = f"Error reading DOCX {path}: {str(e)}"
    return text

keywords = ["容积率", "建筑高度", "高度限制", "红线", "留改拆", "任务书", "基础设施", "水电", "管线", "MPI", "用地属性", "层数"]

docs_dir = "docs"
output_file = "extracted_constraints.txt"

with open(output_file, "w", encoding="utf-8") as out:
    # Process PDFs
    for pdf_path in glob.glob(os.path.join(docs_dir, "*.pdf")):
        out.write(f"=== FILE: {os.path.basename(pdf_path)} ===\n")
        txt = extract_pdf_txt(pdf_path)
        for line in txt.split("\n"):
            if any(kw in line for kw in keywords):
                out.write(f"MATCH: {line.strip()}\n")
        out.write("\n")

    # Process DOCX
    for docx_path in glob.glob(os.path.join(docs_dir, "*.docx")):
        out.write(f"=== FILE: {os.path.basename(docx_path)} ===\n")
        txt = extract_docx_txt(docx_path)
        for line in txt.split("\n"):
            if any(kw in line for kw in keywords):
                out.write(f"MATCH: {line.strip()}\n")
        out.write("\n")

print(f"Extraction complete. Results saved to {output_file}")
