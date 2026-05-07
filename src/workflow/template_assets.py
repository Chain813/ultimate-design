"""Project-level fixed drawing assets for map/image generation workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.config import DATA_DIR, META_DIR, ROOT_DIR


TEMPLATE_ASSET_DIR = DATA_DIR / "template_assets"
TEMPLATE_ASSET_MANIFEST = META_DIR / "template_assets.json"


@dataclass(frozen=True)
class TemplateAssetSpec:
    asset_id: str
    label: str
    prompt_channel: str
    required: bool
    accepted_types: tuple[str, ...]
    description: str
    generation_rule: str


TEMPLATE_ASSET_SPECS: tuple[TemplateAssetSpec, ...] = (
    TemplateAssetSpec(
        asset_id="fixed_base_map",
        label="固定底图 / 正射影像",
        prompt_channel="卫星底图",
        required=True,
        accepted_types=("png", "jpg", "jpeg", "webp", "tif", "tiff"),
        description="统一裁切后的卫星图、航拍图或无纹理 2D 底图，是后续所有分析图的锁定底图。",
        generation_rule="作为 locked background 使用，不允许 SD 或 Image 2.0 缩放、旋转、重绘或改动原始像素。",
    ),
    TemplateAssetSpec(
        asset_id="research_scope",
        label="研究范围红线 / Mask",
        prompt_channel="红线边界图",
        required=True,
        accepted_types=("geojson", "json", "svg", "png", "jpg", "jpeg", "pdf", "zip"),
        description="研究范围边界，建议优先上传 GeoJSON/SVG；若使用 PNG，请使用透明或黑白 mask。",
        generation_rule="研究范围边界必须固定，范围外默认锁定，不能被 AI 生成内容覆盖。",
    ),
    TemplateAssetSpec(
        asset_id="key_plots",
        label="重点地块边界 / Mask",
        prompt_channel="红线边界图",
        required=True,
        accepted_types=("geojson", "json", "svg", "png", "jpg", "jpeg", "pdf", "zip"),
        description="五个重点地块或重点更新单元的边界/编号/mask，用于定位深化设计对象。",
        generation_rule="重点地块位置、形状、编号和边界必须固定，最终成图阶段应重新叠加清晰边界。",
    ),
    TemplateAssetSpec(
        asset_id="fixed_frame",
        label="固定图框 / 出图版式",
        prompt_channel="固定图框模板",
        required=True,
        accepted_types=("png", "jpg", "jpeg", "svg", "pdf"),
        description="A3/A1/PPT 的图框、标题栏、比例尺、指北针、图例区和信息栏模板。",
        generation_rule="图框作为最终合成层，固定画幅、标题栏、图例区和安全边距，AI 不负责重新设计图框。",
    ),
    TemplateAssetSpec(
        asset_id="building_texture",
        label="建筑肌理 / 建筑轮廓",
        prompt_channel="建筑肌理图",
        required=False,
        accepted_types=("geojson", "json", "svg", "png", "jpg", "jpeg", "pdf", "zip"),
        description="建筑轮廓、建筑高度、肌理密度或总平面底座，用于约束建筑相关图纸。",
        generation_rule="建筑轮廓和街区肌理应作为约束参考，不允许 AI 随意改变建筑边界。",
    ),
    TemplateAssetSpec(
        asset_id="road_network",
        label="道路矢量 / 交通底图",
        prompt_channel="道路矢量图",
        required=False,
        accepted_types=("geojson", "json", "svg", "png", "jpg", "jpeg", "pdf", "zip"),
        description="道路中心线、道路等级、轨道站点、慢行系统或交通专题图。",
        generation_rule="道路走向、交叉口和交通节点固定，AI 只允许做符号、箭头和透明分析覆盖层。",
    ),
    TemplateAssetSpec(
        asset_id="gis_theme",
        label="GIS 专题底图 / 用地图",
        prompt_channel="GIS专题图",
        required=False,
        accepted_types=("geojson", "json", "svg", "png", "jpg", "jpeg", "pdf", "zip"),
        description="用地现状、控规、更新潜力、热力、生态或公共空间等专题底图。",
        generation_rule="专题分类和图例逻辑必须来自上传文件，不能虚构不存在的用地或评价等级。",
    ),
    TemplateAssetSpec(
        asset_id="legend_reference",
        label="图例 / 色彩 / 风格参考",
        prompt_channel="图例参考图",
        required=False,
        accepted_types=("png", "jpg", "jpeg", "webp", "svg", "pdf"),
        description="图例样式、色彩体系、符号系统或既有图册参考页。",
        generation_rule="仅参考图例、配色和版式气质，不借用其中的空间边界或地名。",
    ),
)


def get_template_asset_specs() -> List[TemplateAssetSpec]:
    return list(TEMPLATE_ASSET_SPECS)


def get_template_asset_spec(asset_id: str) -> TemplateAssetSpec:
    for spec in TEMPLATE_ASSET_SPECS:
        if spec.asset_id == asset_id:
            return spec
    raise ValueError(f"Unknown template asset id: {asset_id}")


def load_template_asset_manifest(manifest_path: Optional[Path] = None) -> Dict:
    path = manifest_path or TEMPLATE_ASSET_MANIFEST
    if not path.exists():
        return {"version": 1, "assets": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "assets": {}}
    if not isinstance(data, dict):
        return {"version": 1, "assets": {}}
    data.setdefault("version", 1)
    data.setdefault("assets", {})
    return data


def save_template_asset(
    asset_id: str,
    original_name: str,
    content: bytes,
    note: str = "",
    asset_dir: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
) -> Dict:
    spec = get_template_asset_spec(asset_id)

    # Validate file type
    suffix = Path(original_name).suffix.lower().lstrip(".")
    if suffix not in spec.accepted_types:
        raise ValueError(
            f"File type '.{suffix}' not accepted for {spec.label}. "
            f"Accepted: {spec.accepted_types}"
        )

    storage_dir = asset_dir or TEMPLATE_ASSET_DIR
    manifest_file = manifest_path or TEMPLATE_ASSET_MANIFEST
    storage_dir.mkdir(parents=True, exist_ok=True)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_name).suffix.lower() or ".bin"
    filename = f"{asset_id}{suffix}"
    target_path = storage_dir / filename
    target_path.write_bytes(content)

    manifest = load_template_asset_manifest(manifest_file)
    relative_path = _relative_to_root(target_path)
    entry = {
        "asset_id": asset_id,
        "label": spec.label,
        "prompt_channel": spec.prompt_channel,
        "original_name": original_name,
        "filename": filename,
        "relative_path": relative_path,
        "size_bytes": len(content),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "required": spec.required,
        "note": note.strip(),
    }
    manifest["assets"][asset_id] = entry
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def remove_template_asset(
    asset_id: str,
    asset_dir: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
) -> bool:
    storage_dir = asset_dir or TEMPLATE_ASSET_DIR
    manifest_file = manifest_path or TEMPLATE_ASSET_MANIFEST
    manifest = load_template_asset_manifest(manifest_file)
    entry = manifest.get("assets", {}).pop(asset_id, None)
    if not entry:
        return False

    file_path = storage_dir / entry.get("filename", "")
    if file_path.exists() and file_path.is_file():
        file_path.unlink()
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def get_uploaded_prompt_channels(manifest: Optional[Dict] = None) -> List[str]:
    manifest = manifest or load_template_asset_manifest()
    channels = [entry.get("prompt_channel") for entry in manifest.get("assets", {}).values()]
    return _dedupe(channel for channel in channels if channel)


def get_template_asset_rows(manifest: Optional[Dict] = None) -> List[Dict[str, str]]:
    manifest = manifest or load_template_asset_manifest()
    uploaded = manifest.get("assets", {})
    rows = []
    for spec in TEMPLATE_ASSET_SPECS:
        entry = uploaded.get(spec.asset_id)
        rows.append(
            {
                "资产": spec.label,
                "必备": "是" if spec.required else "建议",
                "状态": "已上传" if entry else "缺失",
                "文件": entry.get("original_name", "") if entry else "",
                "约束通道": spec.prompt_channel,
                "用途": spec.generation_rule,
            }
        )
    return rows


def summarize_template_assets_for_prompt(manifest: Optional[Dict] = None) -> str:
    manifest = manifest or load_template_asset_manifest()
    uploaded = manifest.get("assets", {})
    if not uploaded:
        return "固定制图模板资产：尚未上传；涉及真实空间边界的图纸只能生成版式模板，不能生成最终可用图。"

    lines = ["固定制图模板资产："]
    missing_required = []
    for spec in TEMPLATE_ASSET_SPECS:
        entry = uploaded.get(spec.asset_id)
        if entry:
            lines.append(f"- {spec.label}：已上传 {entry.get('original_name', entry.get('filename', ''))}；{spec.generation_rule}")
        elif spec.required:
            missing_required.append(spec.label)

    if missing_required:
        lines.append(f"缺失必备固定资产：{'、'.join(missing_required)}。缺失前不要输出最终 Image 2.0 成图提示词。")
    else:
        lines.append("底图、研究范围、重点地块和图框已具备固定约束；生成时只允许输出研究范围内的分析覆盖层。")
        lines.append("最终合成顺序：固定底图 -> AI 覆盖层 -> 研究范围红线 -> 重点地块边界 -> 固定图框。")
    return "\n".join(lines)


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT_DIR.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def _dedupe(items: Iterable[str]) -> List[str]:
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result
