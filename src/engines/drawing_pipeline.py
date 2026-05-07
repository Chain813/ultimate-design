"""End-to-end drawing pipeline: asset validation -> prompt generation -> SD rendering -> result storage."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional


from src.engines.drawing_prompt_engine import (
    CompletenessReport,
    ImagePromptRequest,
    TemplateNotFoundError,
    check_prompt_completeness,
    get_drawing_profile,
    revise_prompt_by_rating,
)
from src.engines.quality_assessor import QualityAssessor
from src.engines.drawing_prompt_templates import (
    build_drawing_prompt,
    generate_drawing_prompt_with_llm,
    get_or_create_template,
)
from src.engines.stable_diffusion_engine import SDPipeline, SDResult
from src.workflow.stage_data_bus import save_stage_output
from src.workflow.stage_keys import SK

logger = logging.getLogger("ultimateDESIGN")


@dataclass
class PipelineResult:
    """Result from a single drawing pipeline execution."""
    template_name: str
    success: bool
    prompt: str = ""
    image: Any = None
    error: str = ""
    report: CompletenessReport = None
    quality_report: Any = None


class DrawingPipeline:
    """End-to-end orchestrator: asset validation -> prompt generation -> SD rendering -> result storage."""

    def __init__(self, sd_pipeline: SDPipeline = None):
        self.sd = sd_pipeline or SDPipeline()

    def generate_single(self, template_name: str, mode: str = "auto",
                        on_progress: Optional[Callable] = None) -> PipelineResult:
        """Generate a single drawing end-to-end."""
        report = self._validate_assets(template_name)
        if not report.can_generate:
            return PipelineResult(
                template_name=template_name,
                success=False,
                error=f"资产验证失败（{report.precision}）：{'、'.join(report.missing)}",
                report=report,
            )

        try:
            prompt = self._generate_prompt(template_name)
        except TemplateNotFoundError:
            return PipelineResult(
                template_name=template_name,
                success=False,
                error=f"模板未找到：{template_name}",
                report=report,
            )
        except Exception as e:
            return PipelineResult(
                template_name=template_name,
                success=False,
                error=f"提示词生成失败：{e}",
                report=report,
            )

        if mode == "confirm":
            return PipelineResult(
                template_name=template_name,
                success=True,
                prompt=prompt,
                report=report,
            )

        try:
            profile = get_drawing_profile(template_name)
            sd_result = self._render(prompt, profile, on_progress)
        except Exception as e:
            return PipelineResult(
                template_name=template_name,
                success=False,
                prompt=prompt,
                error=f"SD 渲染失败：{e}",
                report=report,
            )

        self._store_result(template_name, sd_result, prompt)

        return PipelineResult(
            template_name=template_name,
            success=True,
            prompt=prompt,
            image=sd_result.images[0] if sd_result.images else None,
            report=report,
        )

    def generate_batch(self, template_names: list[str], mode: str = "auto",
                       on_progress: Optional[Callable] = None) -> list[PipelineResult]:
        """Generate multiple drawings sequentially."""
        results = []
        total = len(template_names)

        for i, name in enumerate(template_names):
            if on_progress:
                on_progress(current=i, total=total, template_name=name)
            result = self.generate_single(name, mode=mode, on_progress=on_progress)
            results.append(result)

        return results

    def render_only(self, template_name: str, prompt: str,
                    on_progress: Optional[Callable] = None) -> PipelineResult:
        """Render a pre-confirmed prompt (for confirm mode)."""
        try:
            profile = get_drawing_profile(template_name)
            sd_result = self._render(prompt, profile, on_progress)
        except Exception as e:
            return PipelineResult(
                template_name=template_name,
                success=False,
                prompt=prompt,
                error=f"SD 渲染失败：{e}",
            )

        self._store_result(template_name, sd_result, prompt)

        return PipelineResult(
            template_name=template_name,
            success=True,
            prompt=prompt,
            image=sd_result.images[0] if sd_result.images else None,
        )

    def generate_with_quality_loop(
        self,
        template_name: str,
        max_retries: int = 2,
        on_progress: Optional[Callable] = None,
    ) -> PipelineResult:
        """Generate -> assess -> revise -> regenerate until A/B or max retries."""
        assessor = QualityAssessor()

        for _attempt in range(max_retries + 1):
            result = self.generate_single(template_name, mode="auto", on_progress=on_progress)
            if not result.success:
                return result

            report = assessor.assess(result.image, result.prompt, template_name)

            if report.rating in ("A", "B"):
                result.quality_report = report
                return result

            revised = revise_prompt_by_rating(
                result.prompt, report.rating, report.issue_types
            )
            result = self.render_only(template_name, revised, on_progress)
            result.quality_report = report

        return result

    def _validate_assets(self, template_name: str) -> CompletenessReport:
        profile = get_drawing_profile(template_name)
        tmpl = get_or_create_template(template_name)
        request = ImagePromptRequest(
            chapter=tmpl.chapter if tmpl else "",
            drawing_name=template_name,
            drawing_type=profile.drawing_type,
            aspect_ratio="A3横版",
            output_scene="毕业设计图册 / A1 展板 / 方案汇报",
            uploaded_channels=[],
            main_expression=tmpl.description if tmpl else "",
        )
        return check_prompt_completeness(request, profile)

    def _generate_prompt(self, template_name: str) -> str:
        prompt, sys_prompt = build_drawing_prompt(template_name)
        if not prompt:
            raise TemplateNotFoundError(f"Template not found: {template_name}")
        if "暂不生成最终 Image 2.0 提示词" in prompt:
            return prompt
        try:
            return generate_drawing_prompt_with_llm(template_name)
        except Exception as e:
            logger.warning("LLM review failed, using raw prompt: %s", e)
            return prompt

    def _render(self, prompt: str, profile, on_progress=None) -> SDResult:
        self.sd.txt2img(prompt=prompt, negative_prompt="", width=1024, height=768)
        return self.sd.run(on_progress=on_progress)

    def _store_result(self, template_name: str, sd_result: SDResult, prompt: str):
        if sd_result.images:
            save_stage_output("aigc", f"{SK.AIGC_IMAGE}_{template_name}", sd_result.images[0])
        save_stage_output("aigc", f"{SK.AIGC_PROMPT}_{template_name}", prompt)
        save_stage_output("aigc", f"{SK.AIGC_SEED}_{template_name}", sd_result.seed)
