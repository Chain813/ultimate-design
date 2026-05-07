"""Batch exporter for generating and saving full atlas."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from src.engines.drawing_pipeline import DrawingPipeline
from src.engines.drawing_prompt_engine import flatten_chapter_drawings
from src.engines.version_store import VersionStore

logger = logging.getLogger("ultimateDESIGN")


@dataclass
class ExportReport:
    total: int
    success: int
    skipped: int
    failed: int
    errors: List[str] = field(default_factory=list)


class BatchExporter:
    def __init__(self, pipeline: DrawingPipeline, store: VersionStore,
                 drawing_names: List[str] = None):
        self.pipeline = pipeline
        self.store = store
        self.drawing_names = drawing_names or flatten_chapter_drawings()

    def export_full_atlas(self, skip_existing: bool = True,
                          quality_loop: bool = False,
                          max_retries: int = 2,
                          on_progress: Optional[Callable] = None) -> ExportReport:
        total = len(self.drawing_names)
        success = skipped = failed = 0
        errors = []

        for i, name in enumerate(self.drawing_names):
            if on_progress:
                on_progress(current=i, total=total, drawing_name=name)

            if skip_existing:
                existing = self.store.get_latest(name)
                if existing is not None:
                    skipped += 1
                    continue

            try:
                if quality_loop:
                    result = self.pipeline.generate_with_quality_loop(name, max_retries=max_retries)
                else:
                    result = self.pipeline.generate_single(name, mode="auto")

                if result.success and result.image:
                    metadata = {
                        "prompt": result.prompt,
                        "chapter": self._infer_chapter(name),
                        "rating": result.quality_report.rating if result.quality_report else None,
                    }
                    self.store.save(name, result.image, metadata)
                    success += 1
                else:
                    failed += 1
                    errors.append(f"{name}: {result.error}")
            except Exception as e:
                failed += 1
                errors.append(f"{name}: {e}")

        if on_progress:
            on_progress(current=total, total=total, drawing_name="完成")

        return ExportReport(total=total, success=success, skipped=skipped,
                           failed=failed, errors=errors)

    def export_chapter(self, chapter: str, **kwargs) -> ExportReport:
        from src.engines.drawing_prompt_engine import BOOK_CHAPTERS
        chapter_drawings = BOOK_CHAPTERS.get(chapter, [])
        old_names = self.drawing_names
        self.drawing_names = chapter_drawings
        try:
            return self.export_full_atlas(**kwargs)
        finally:
            self.drawing_names = old_names

    def export_selected(self, drawing_names: List[str], **kwargs) -> ExportReport:
        old_names = self.drawing_names
        self.drawing_names = drawing_names
        try:
            return self.export_full_atlas(**kwargs)
        finally:
            self.drawing_names = old_names

    def _infer_chapter(self, drawing_name: str) -> str:
        from src.engines.drawing_prompt_engine import BOOK_CHAPTERS
        for chapter, drawings in BOOK_CHAPTERS.items():
            if drawing_name in drawings:
                return chapter
        return "未分类"
