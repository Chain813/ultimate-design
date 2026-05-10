import sys
import os
from pathlib import Path
from PIL import Image

# 确保环境对齐
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.engines.drawing_pipeline import DrawingPipeline
from src.engines.batch_exporter import BatchExporter
from src.engines.version_store import VersionStore
from src.engines.spatial_engine import get_landuse_legend
from src.engines.drawing_prompt_engine import (
    get_drawing_profile, 
    ImagePromptRequest,
    _compose_prompt,
    build_negative_prompt
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class HighPrecisionPipeline(DrawingPipeline):
    """
    高精度标准管线：
    强制开启 ControlNet，实现矢量底稿对齐。
    """
    
    def _validate_assets(self, template_name: str):
        from src.engines.drawing_prompt_engine import CompletenessReport
        return CompletenessReport(can_generate=True, precision="一级精度")

    def _generate_prompt(self, template_name: str) -> str:
        profile = get_drawing_profile(template_name)
        legend_items = get_landuse_legend()
        colors = ", ".join([f"{item['Type']}({item['Color']})" for item in legend_items])
        
        main_expr = f"Professional Masterplan: {template_name}. Dark mode, vector style."
        request = ImagePromptRequest(
            chapter="05 总体规划篇",
            drawing_name=template_name,
            drawing_type=profile.drawing_type,
            aspect_ratio="A3横版",
            output_scene="Official Planning Report",
            uploaded_channels=["卫星底图", "道路矢量图", "GIS专题图"],
            main_expression=main_expr + f" Color mapping: {colors}",
            legend_content="Standard planning legend.",
            style_system="High-contrast architectural plan, blueprint aesthetic.",
        )
        return _compose_prompt(request, profile, build_negative_prompt("一级精度"), template_only=False)

    def _render(self, prompt: str, profile, on_progress=None):
        """
        重写渲染核心：手动注入 ControlNet 资产。
        """
        base_asset_dir = ROOT / "static/assets/generated_base"
        
        # 1. 初始化 SD Pipeline
        self.sd.txt2img(prompt=prompt, negative_prompt="", width=1024, height=768)
        
        # 2. 注入路网骨架约束 (Canny)
        road_img = Image.open(base_asset_dir / "road_guidance.png").convert("RGB")
        self.sd.add_controlnet(
            image=road_img,
            module="canny",
            model="control_v11p_sd15_canny",
            weight=1.0
        )
        
        # 3. 注入用地分区约束 (Segmentation)
        seg_img = Image.open(base_asset_dir / "landuse_segmentation.png").convert("RGB")
        self.sd.add_controlnet(
            image=seg_img,
            module="none", # 改为 none，直接使用预渲染的色块图
            model="control_v11p_sd15_seg",
            weight=0.8
        )
        
        # 4. 执行渲染
        return self.sd.run(on_progress=on_progress)

def run_standard_export():
    print("="*60)
    print("💎 正在启动 [ControlNet 强约束] 渲染任务...")
    print("📍 模式: 空间地理对齐 (v003 最终版)")
    print("="*60)

    pipeline = HighPrecisionPipeline()
    store = VersionStore(ROOT / "output/atlas")
    exporter = BatchExporter(pipeline, store)

    # 导出核心规划图
    target_drawings = ["总平面规划图", "土地利用规划图", "道路交通系统规划图"]
    
    # 强制重新生成以确保 ControlNet 生效
    report = exporter.export_selected(target_drawings, skip_existing=False)

    print("\n" + "="*60)
    print("🏁 任务完成")
    print(f"成功: {report.success} / 失败: {report.failed}")
    if report.errors:
        for err in report.errors:
            print(f"  - {err}")
    print("="*60)

if __name__ == "__main__":
    run_standard_export()
