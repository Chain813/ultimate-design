from src.workflow.template_assets import (
    get_template_asset_rows,
    get_uploaded_prompt_channels,
    load_template_asset_manifest,
    save_template_asset,
    summarize_template_assets_for_prompt,
)


def test_save_template_asset_writes_file_and_manifest(tmp_path):
    asset_dir = tmp_path / "assets"
    manifest_path = tmp_path / "manifest.json"

    entry = save_template_asset(
        "fixed_base_map",
        "base-map.png",
        b"image-bytes",
        note="A3 horizontal crop",
        asset_dir=asset_dir,
        manifest_path=manifest_path,
    )
    manifest = load_template_asset_manifest(manifest_path)

    assert (asset_dir / "fixed_base_map.png").exists()
    assert entry["prompt_channel"] == "卫星底图"
    assert manifest["assets"]["fixed_base_map"]["note"] == "A3 horizontal crop"


def test_uploaded_channels_and_rows_are_deduped(tmp_path):
    asset_dir = tmp_path / "assets"
    manifest_path = tmp_path / "manifest.json"

    save_template_asset("research_scope", "scope.geojson", b"{}", asset_dir=asset_dir, manifest_path=manifest_path)
    save_template_asset("key_plots", "plots.geojson", b"{}", asset_dir=asset_dir, manifest_path=manifest_path)
    manifest = load_template_asset_manifest(manifest_path)

    assert get_uploaded_prompt_channels(manifest) == ["红线边界图"]
    rows = get_template_asset_rows(manifest)
    assert any(row["资产"] == "研究范围红线 / Mask" and row["状态"] == "已上传" for row in rows)


def test_prompt_summary_tracks_required_assets(tmp_path):
    asset_dir = tmp_path / "assets"
    manifest_path = tmp_path / "manifest.json"

    save_template_asset("fixed_base_map", "base.png", b"1", asset_dir=asset_dir, manifest_path=manifest_path)
    partial = summarize_template_assets_for_prompt(load_template_asset_manifest(manifest_path))
    assert "缺失必备固定资产" in partial

    save_template_asset("research_scope", "scope.svg", b"2", asset_dir=asset_dir, manifest_path=manifest_path)
    save_template_asset("key_plots", "plots.svg", b"3", asset_dir=asset_dir, manifest_path=manifest_path)
    save_template_asset("fixed_frame", "frame.svg", b"4", asset_dir=asset_dir, manifest_path=manifest_path)
    complete = summarize_template_assets_for_prompt(load_template_asset_manifest(manifest_path))

    assert "最终合成顺序" in complete
    assert "固定底图 -> AI 覆盖层" in complete
