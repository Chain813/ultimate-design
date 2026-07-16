# -*- coding: utf-8 -*-
"""Regenerate report with AI-focused abstract, using existing chapters where possible."""
import os, sys, io
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

# Force UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load .env
env_path = project_root / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

from src.engines.document_composer import (
    assemble_report_docx, AuthorInfo,
    _generate_abstract_from_chapters, _generate_english_abstract,
    _extract_keywords_from_chapters, _extract_english_keywords,
    _generate_references_from_chapters, _generate_acknowledgments,
    REPORT_CHAPTERS, load_author_info_json,
)
from src.engines.document_pipeline import run_light_pipeline

student = load_author_info_json()

print("Regenerating report with AI/AIGC-focused abstract...")
print("This will regenerate all 27 chapters + de-AI processing + new abstract")
print("=" * 60)

chapters, buf = run_light_pipeline(
    student=student,
    progress_callback=lambda cur, tot, label: print(f"[{cur}/{tot}] {label}"),
    log_callback=lambda msg: print(f"  {msg}"),
    model='deepseek-v4-pro',
    enable_deai=True,
    deai_intensity=0.7,
)

# Save
fname = f'项目设计报告_{student.name}_{student.student_id}.docx'
outpath = Path('output') / fname
try:
    with open(outpath, 'wb') as f:
        f.write(buf.getvalue())
except PermissionError:
    fname = f'项目设计报告_{student.name}_{student.student_id}_new.docx'
    outpath = Path('output') / fname
    with open(outpath, 'wb') as f:
        f.write(buf.getvalue())

total_chars = sum(len(v) for v in chapters.values())
print(f'\n{"=" * 60}')
print(f'DONE! Output: {outpath} ({len(buf.getvalue())/1024:.1f} KB)')
print(f'Chapters: {len(chapters)}/27 | Total chars: {total_chars}')
