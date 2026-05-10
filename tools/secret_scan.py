"""Basic secret pattern scanner for repository and local env files."""

from pathlib import Path
import re
import sys


PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{12,}"),
    re.compile(r"(?i)Baidu_Map_AK\s*=\s*(?!YOUR_)[A-Za-z0-9]{10,}"),
]
# Tutorial / documentation placeholder patterns that are safe to ignore
KNOWN_SAFE_PATTERNS = [
    re.compile(r"(?i)your_\w+_key"),
    re.compile(r"(?i)your_\w+_ak"),
    re.compile(r"(?i)YOUR_BAIDU_MAP_AK"),
    re.compile(r"(?i)YOUR_DEEPSEEK_API_KEY"),
    re.compile(r'(?i)API_KEY\s*=\s*"your_'),
    re.compile(r"(?i)ghp_xxxx"),
    re.compile(r"(?i)AIzaSyx"),
    re.compile(r"(?i)PLACEHOLDER"),
]
SCANNED_SUFFIXES = {".py", ".md", ".txt", ".yaml", ".yml", ".toml"}
SCANNED_FILENAMES = {".env"}

EXCLUDED_PARTS = {
    ".agents",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".runtime-packages",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}
EXCLUDED_PREFIXES = {
    "data/raw_images/",
    "data/streetview/",
    "docs/",
}
ALLOWED_FILES = {".env.example"}


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(part in EXCLUDED_PARTS for part in path.parts) or any(
        rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = []

    for path in root.rglob("*"):
        if not path.is_file() or should_skip(path, root):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in ALLOWED_FILES:
            continue
        if path.suffix.lower() not in SCANNED_SUFFIXES and path.name not in SCANNED_FILENAMES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in PATTERNS):
                # Skip known-safe tutorial/placeholder patterns
                if any(safe.search(line) for safe in KNOWN_SAFE_PATTERNS):
                    continue
                findings.append((rel, line_number))

    if findings:
        print("[ERROR] Potential secrets found:")
        for rel, line_number in findings:
            print(f" - {rel}:{line_number}")
        return 1

    print("[OK] No obvious secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
