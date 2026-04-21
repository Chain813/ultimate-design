"""Basic secret pattern scanner for tracked files."""

from pathlib import Path
import re
import sys


PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{12,}"),
    re.compile(r"(?i)Baidu_Map_AK\s*=\s*(?!YOUR_)[A-Za-z0-9]{10,}"),
]

EXCLUDED_PARTS = {".git", ".venv", "venv", "__pycache__", "data/streetview"}
ALLOWED_FILES = {".env.example"}


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = []

    for path in root.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in ALLOWED_FILES:
            continue
        if path.suffix.lower() not in {".py", ".md", ".txt", ".yaml", ".yml", ".env", ".toml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for pattern in PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append((rel, match.group(0)[:120]))
                break

    if findings:
        print("[ERROR] Potential secrets found:")
        for rel, sample in findings:
            print(f" - {rel}: {sample}")
        return 1

    print("[OK] No obvious secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
