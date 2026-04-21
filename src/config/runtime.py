from pathlib import Path


def project_root() -> Path:
    """Return the repository root regardless of current working directory."""
    return Path(__file__).resolve().parents[2]


def resolve_path(path_str: str) -> Path:
    """Resolve an absolute/relative path against project root."""
    path = Path(path_str)
    if path.is_absolute():
        return path
    return project_root() / path
