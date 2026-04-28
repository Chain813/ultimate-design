from pathlib import Path


def read_text_with_fallback(path: Path) -> str:
    """Read text files exported by mixed tools without assuming UTF-8 only."""
    if not path.exists():
        return ""

    data = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")
