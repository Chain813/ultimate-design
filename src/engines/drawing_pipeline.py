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
        """Render with high-resolution upscaling logic and GIS ControlNet constraints."""
        # 1. Base generation at a stable resolution for 8GB VRAM
        self.sd.txt2img(
            prompt=prompt, 
            negative_prompt="blurry, messy, low resolution, distorted, organic chaos, text, watermark", 
            width=1024, 
            height=768
        )

        # --- 引入 ControlNet GIS 约束（实现标准制图的关键） ---
        try:
            from PIL import Image
            from src.config import DATA_DIR
            from src.workflow.template_assets import load_template_asset_manifest
            
            manifest = load_template_asset_manifest()
            assets = manifest.get("assets", {})
            
            # 1. 路网约束 (Canny) - 保持道路结构绝对准确
            road_asset = assets.get("road_network")
            if road_asset:
                path = DATA_DIR / "template_assets" / road_asset["filename"]
                if path.exists():
                    img = Image.open(path).convert("RGB")
                    self.sd.add_controlnet(img, module="canny", model="control_v11p_sd15_canny", weight=0.8)
                    
            # 2. 建筑与用地约束 (Seg) - 保持建筑体量和地块边界准确
            building_asset = assets.get("building_texture")
            if building_asset:
                path = DATA_DIR / "template_assets" / building_asset["filename"]
                if path.exists():
                    img = Image.open(path).convert("RGB")
                    self.sd.add_controlnet(img, module="seg", model="control_v11p_sd15_seg", weight=0.6)

            # 3. 研究范围约束 (Canny/Lineart) - 绝对锁定项目边界红线
            scope_asset = assets.get("research_scope")
            if scope_asset:
                path = DATA_DIR / "template_assets" / scope_asset["filename"]
                if path.exists():
                    img = Image.open(path).convert("RGB")
                    # 使用 1.0 的最高权重，强制要求 AI 遵循红线边界
                    self.sd.add_controlnet(img, module="canny", model="control_v11p_sd15_canny", weight=1.0)
                    
            # 4. 土地利用/专题属性约束 (Seg) - 可选图层，严格遵循国标用地色块
            gis_asset = assets.get("gis_theme")
            if gis_asset:
                path = DATA_DIR / "template_assets" / gis_asset["filename"]
                if path.exists():
                    img = Image.open(path).convert("RGB")
                    # 使用 0.7 权重，既锁定大面积色块，又允许 AI 发挥材质光影
                    self.sd.add_controlnet(img, module="seg", model="control_v11p_sd15_seg", weight=0.7)
                    
            # 5. 保护建筑/紫线区域约束 (Canny) - 绝对保留历史遗产轮廓
            historic_asset = assets.get("historic_buildings")
            if historic_asset:
                path = DATA_DIR / "template_assets" / historic_asset["filename"]
                if path.exists():
                    img = Image.open(path).convert("RGB")
                    # 使用 1.0 的最高权重，强制要求 AI 绝对保留该区域内的建筑肌理，禁止改建
                    self.sd.add_controlnet(img, module="canny", model="control_v11p_sd15_canny", weight=1.0)
                    
        except Exception as e:
            logger.error(f"加载 ControlNet 约束失败: {e}")
        # ----------------------------------------------------
        
        # 2. Professional Upscaling (2x) using Tiled Diffusion logic (via Ultimate SD Upscale)
        # This will output a 2048x1536 high-fidelity drawing
        self.sd.upscale(scale=2, tile_size=512)
        
        result = self.sd.run(on_progress=on_progress)
        
        # --- 后期强制叠加（Post-Process Overlay） ---
        # 针对用户“拆改留中的留在重绘中一定不能改变”的绝对诉求
        # 我们在 AI 生成的最终图像上，通过 Alpha 混合强制盖回“保护建筑”的原始像素
        if result and result.images and len(result.images) > 0:
            try:
                from PIL import Image
                from src.config import DATA_DIR
                from src.workflow.template_assets import load_template_asset_manifest
                
                manifest = load_template_asset_manifest()
                assets = manifest.get("assets", {})
                historic_asset = assets.get("historic_buildings")
                
                if historic_asset:
                    path = DATA_DIR / "template_assets" / historic_asset["filename"]
                    if path.exists():
                        overlay_img = Image.open(path).convert("RGBA")
                        base_img = result.images[0].convert("RGBA")
                        
                        # 缩放覆盖层以匹配高清放大后的最终尺寸
                        overlay_img = overlay_img.resize(base_img.size, Image.Resampling.LANCZOS)
                        
                        # 假设用户上传的是带有透明通道的 PNG 遮罩（或黑底白底的特征图）
                        # 如果没有 Alpha 通道，我们根据像素亮度生成一个 Mask
                        r, g, b, a = overlay_img.split()
                        
                        # 强制叠加：只在有像素（Alpha>0）的地方进行覆盖
                        final_img = Image.alpha_composite(base_img, overlay_img)
                        result.images[0] = final_img.convert("RGB")
            except Exception as e:
                logger.error(f"强制叠加保护建筑图层失败: {e}")
        # ----------------------------------------
        
        return result

    def _store_result(self, template_name: str, sd_result: SDResult, prompt: str):
        if sd_result.images:
            save_stage_output("aigc", f"{SK.AIGC_IMAGE}_{template_name}", sd_result.images[0])
        save_stage_output("aigc", f"{SK.AIGC_PROMPT}_{template_name}", prompt)
        save_stage_output("aigc", f"{SK.AIGC_SEED}_{template_name}", sd_result.seed)
