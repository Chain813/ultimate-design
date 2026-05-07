"""Persistent version store for generated drawings."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

logger = logging.getLogger("ultimateDESIGN")


class VersionStore:
    """File-based version store: PNG images + JSON metadata."""

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self.output_dir / "manifest.json"

    def save(self, drawing_name: str, image, metadata: dict) -> str:
        drawing_dir = self.output_dir / drawing_name
        drawing_dir.mkdir(parents=True, exist_ok=True)

        version_id = self._next_version(drawing_dir)
        png_path = drawing_dir / f"{version_id}.png"
        json_path = drawing_dir / f"{version_id}.json"

        image.save(png_path, "PNG")

        meta = {
            "version_id": version_id,
            "drawing_name": drawing_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "png_path": str(png_path),
            **metadata,
        }
        json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        self._update_manifest(drawing_name, version_id, meta)
        return version_id

    def load(self, drawing_name: str, version_id: str = "latest") -> Optional[Tuple]:
        drawing_dir = self.output_dir / drawing_name
        if not drawing_dir.exists():
            return None

        if version_id == "latest":
            versions = self.list_versions(drawing_name)
            if not versions:
                return None
            version_id = versions[-1]["version_id"]

        png_path = drawing_dir / f"{version_id}.png"
        json_path = drawing_dir / f"{version_id}.json"

        if not png_path.exists():
            return None

        image = Image.open(png_path)
        metadata = {}
        if json_path.exists():
            metadata = json.loads(json_path.read_text(encoding="utf-8"))
        return image, metadata

    def get_latest(self, drawing_name: str) -> Optional[Tuple]:
        return self.load(drawing_name, "latest")

    def list_versions(self, drawing_name: str) -> List[Dict]:
        drawing_dir = self.output_dir / drawing_name
        if not drawing_dir.exists():
            return []
        versions = []
        for json_file in sorted(drawing_dir.glob("v*.json")):
            try:
                meta = json.loads(json_file.read_text(encoding="utf-8"))
                versions.append(meta)
            except Exception:
                continue
        return versions

    def export_chapter(self, chapter: str, output_dir) -> int:
        output_dir = Path(output_dir)
        safe_chapter = chapter.replace(" ", "_").replace("/", "_")
        chapter_dir = output_dir / safe_chapter
        chapter_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for drawing_dir in self.output_dir.iterdir():
            if not drawing_dir.is_dir() or drawing_dir.name == "manifest.json":
                continue
            latest = self.get_latest(drawing_dir.name)
            if latest is None:
                continue
            image, metadata = latest
            if metadata.get("chapter") == chapter:
                dest = chapter_dir / f"{drawing_dir.name}.png"
                image.save(dest, "PNG")
                count += 1
        return count

    def _next_version(self, drawing_dir: Path) -> str:
        existing = list(drawing_dir.glob("v*.png"))
        if not existing:
            return "v001"
        nums = []
        for f in existing:
            try:
                nums.append(int(f.stem[1:]))
            except ValueError:
                continue
        next_num = max(nums) + 1 if nums else 1
        return f"v{next_num:03d}"

    def _update_manifest(self, drawing_name: str, version_id: str, metadata: dict):
        manifest = {}
        if self._manifest_path.exists():
            try:
                manifest = json.loads(self._manifest_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        if drawing_name not in manifest:
            manifest[drawing_name] = {}
        manifest[drawing_name][version_id] = {
            "timestamp": metadata.get("timestamp"),
            "rating": metadata.get("rating"),
        }
        self._manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
