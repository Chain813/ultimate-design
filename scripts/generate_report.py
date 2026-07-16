"""Generate complete graduation report via full pipeline + de-AI processing."""
import io
import os
import sys
import time
import traceback
from pathlib import Path

# Force UTF-8 output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load .env from project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))
env_path = project_root / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

from src.engines.document_composer import AuthorInfo, load_author_info_json
from src.engines.document_pipeline import run_light_pipeline

student = load_author_info_json()

output_dir = Path('output')
output_dir.mkdir(exist_ok=True)

start_time = time.time()

def pc(cur, tot, label):
    elapsed = time.time() - start_time
    pct = cur/tot*100 if tot else 0
    print(f'[{cur}/{tot} {pct:.0f}%] {label} ({elapsed:.0f}s)', flush=True)

def lc(msg):
    print(f'  {msg}', flush=True)

print('=' * 60, flush=True)
print('Starting report generation (light pipeline + de-AI processing)', flush=True)
print('=' * 60, flush=True)

try:
    chapters, buf = run_light_pipeline(
        student=student,
        progress_callback=pc,
        log_callback=lc,
        model='deepseek-v4-pro',
        enable_deai=True,
        deai_intensity=0.7,
    )

    # Save
    fname = f'项目设计报告_{student.name}_{student.student_id}.docx'
    outpath = output_dir / fname
    try:
        with open(outpath, 'wb') as f:
            f.write(buf.getvalue())
    except PermissionError:
        fname = f'项目设计报告_{student.name}_{student.student_id}_new.docx'
        outpath = output_dir / fname
        with open(outpath, 'wb') as f:
            f.write(buf.getvalue())

    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    total_chars = sum(len(v) for v in chapters.values())
    generated = len(chapters)

    print(f'\n{"=" * 60}', flush=True)
    print(f'DONE! Report generated successfully.', flush=True)
    print(f'Output: {outpath} ({len(buf.getvalue())/1024:.1f} KB)', flush=True)
    print(f'Chapters: {generated}/27 | Total chars: {total_chars}', flush=True)
    print(f'Time: {mins}m{secs}s', flush=True)
    print(f'{"=" * 60}', flush=True)

except Exception as e:
    elapsed = time.time() - start_time
    print(f'\nFAILED after {(elapsed//60):.0f}m{(elapsed%60):.0f}s: {e}', flush=True)
    traceback.print_exc()
    sys.exit(1)
