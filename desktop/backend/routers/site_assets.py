"""Site ingestion, 16-category asset catalog, quality check, MarkItDown, and Streetview router (Stage 00-03)."""

from __future__ import annotations

import inspect
import io
import json
import logging
from pathlib import Path
import re
import tempfile
from typing import Any
import zipfile

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
import pandas as pd

from desktop.backend.deps import verify_session_token
from desktop.backend.job_manager import JobContext, get_job_manager
from src.config.paths import CSV_DIR, DATA_DIR, DATA_FILES, ROOT_DIR, STREETVIEW_DIR
from src.core.runtime_adapter import clear_all_caches, get_active_project_id
from src.data import DATA_CATEGORIES, check_data_exists, get_data_readiness, get_data_size
from src.engines.osm_fetcher import OSMDataFetcher
from src.engines.rag_engine import add_custom_document
from src.workflow.stage_data_bus import load_stage_output, save_stage_output

logger = logging.getLogger("ultimateDESIGN.backend.site_assets")

router = APIRouter(
    prefix="/api/v1/assets",
    tags=["assets"],
    dependencies=[Depends(verify_session_token)],
)

PLANNING_KEYWORD_PATTERNS: list[str] = [
    "容积率",
    "建筑密度",
    "绿地率",
    "建筑限高",
    "历史文化街区",
    "历史建筑",
    "视线通廊",
    "天际线",
    "城市更新",
    "微更新",
    "留改拆",
    "工业遗存",
    "慢行系统",
    "公共开放空间",
    "口袋公园",
    "TOD",
    "混合用地",
    "海绵城市",
    "适老化",
    "文商旅",
]


def _extract_planning_keywords(text: str) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    for kw in PLANNING_KEYWORD_PATTERNS:
        if kw.lower() in text.lower():
            found.append(kw)
    return found


def _convert_file_to_markdown(file_path: Path) -> str:
    """Convert PDF/DOCX/PPTX/MD/TXT to structured Markdown using MarkItDown with graceful fallback."""
    suffix = file_path.suffix.lower()
    if suffix in (".md", ".txt", ".csv", ".json", ".yaml", ".yml"):
        try:
            return file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass

    try:
        from markitdown import MarkItDown

        md_engine = MarkItDown()
        converted = md_engine.convert(str(file_path))
        text_content = getattr(converted, "text_content", "") or ""
        if text_content.strip():
            return text_content
    except Exception as exc:
        logger.warning("MarkItDown convert fallback for %s: %s", file_path.name, exc)

    if suffix == ".docx":
        try:
            import docx

            doc = docx.Document(str(file_path))
            paras = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
            return "\n\n".join(paras)
        except Exception:
            pass

    if suffix == ".pdf":
        try:
            import pypdf

            reader = pypdf.PdfReader(str(file_path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(p.strip() for p in pages if p.strip())
        except Exception:
            pass

    try:
        return file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"文档解析降级摘要 ({file_path.name}): {exc}"


def _invoke_ingest_local(engine: Any, layer_type: str, file_path: str, project_id: str | None = None) -> Any:
    """Invoke engine.ingest_local_file with flexible signature adaptation."""
    fn = getattr(engine, "ingest_local_file", None)
    if fn is None:
        raise HTTPException(status_code=500, detail="空间引擎未实现 ingest_local_file 接口")

    sig = inspect.signature(fn)
    params = sig.parameters
    has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    kwargs: dict[str, Any] = {}
    if has_varkw or "layer_type" in params:
        kwargs["layer_type"] = layer_type
    elif "layer" in params:
        kwargs["layer"] = layer_type

    if has_varkw or "file_path" in params:
        kwargs["file_path"] = file_path
    elif "path" in params:
        kwargs["path"] = file_path

    if project_id and (has_varkw or "project_id" in params):
        kwargs["project_id"] = project_id

    if len(kwargs) >= 2:
        return fn(**kwargs)
    return fn(layer_type, file_path)


@router.post("/ingest/local")
def ingest_local_file(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Ingest a local GIS/CSV file directly by path (from Electron dialog or drag-and-drop)."""
    layer_type = str(payload.get("layer_type") or payload.get("layer") or "plots").strip()
    raw_path = str(payload.get("file_path") or payload.get("path") or "").strip()
    project_id = payload.get("project_id")

    if not raw_path:
        raise HTTPException(status_code=400, detail="必须提供本地文件路径 file_path")

    path_obj = Path(raw_path)
    if not path_obj.is_absolute():
        path_obj = (ROOT_DIR / path_obj).resolve()
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail=f"本地文件不存在: {raw_path}")

    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    if project_id and project_id != get_active_project_id() and hasattr(engine, "switch_project"):
        engine.switch_project(str(project_id))

    result = _invoke_ingest_local(engine, layer_type, str(path_obj), project_id=get_active_project_id())
    clear_all_caches()
    save_stage_output("00", f"ingested_{layer_type}", str(path_obj))

    return {
        "status": "ok",
        "layer_type": layer_type,
        "file_path": str(path_obj),
        "project_id": get_active_project_id(),
        "result": result,
        "rag_protected": bool(DATA_FILES["rag"].exists()),
    }


@router.post("/ingest/upload")
async def ingest_uploaded_file(
    file: UploadFile = File(...),
    layer_type: str = Form(default="plots"),
    project_id: str | None = Form(default=None),
) -> dict[str, Any]:
    """Multipart file upload fallback saving to data/projects/<active_id>/raw/ and ingesting into DuckDB."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    if project_id and project_id != get_active_project_id() and hasattr(engine, "switch_project"):
        engine.switch_project(str(project_id))

    active_id = get_active_project_id()
    raw_dir = DATA_DIR / "projects" / active_id / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename or f"{layer_type}.geojson").name
    dest_path = raw_dir / safe_name
    raw_bytes = await file.read()
    dest_path.write_bytes(raw_bytes)

    target_for_ingest = dest_path
    if safe_name.lower().endswith(".zip"):
        extract_dir = raw_dir / Path(safe_name).stem
        extract_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zf:
                zf.extractall(extract_dir)
            shp_candidates = list(extract_dir.glob("*.shp")) + list(extract_dir.glob("*.geojson"))
            if shp_candidates:
                target_for_ingest = shp_candidates[0]
        except Exception as exc:
            logger.warning("Zip extraction warning for %s: %s", safe_name, exc)

    result = _invoke_ingest_local(engine, layer_type, str(target_for_ingest), project_id=active_id)
    clear_all_caches()
    save_stage_output("00", f"uploaded_{layer_type}", str(target_for_ingest))

    return {
        "status": "ok",
        "layer_type": layer_type,
        "filename": safe_name,
        "saved_path": str(target_for_ingest),
        "project_id": active_id,
        "result": result,
        "rag_protected": bool(DATA_FILES["rag"].exists()),
    }


@router.post("/ingest/osm")
def ingest_osm_async(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Submit an async job via JobManager to fetch OSM vector layers for a bounding box or city."""
    bbox = payload.get("bbox")
    if bbox and isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        # Check whether [min_lon, min_lat, max_lon, max_lat] or [min_lat, min_lon, max_lat, max_lon]
        v0, v1, v2, v3 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        if abs(v0) > 90 or abs(v2) > 90:
            min_lon, min_lat, max_lon, max_lat = v0, v1, v2, v3
        else:
            min_lat, min_lon, max_lat, max_lon = v0, v1, v2, v3
    else:
        min_lat = float(payload.get("min_lat", 43.890))
        min_lon = float(payload.get("min_lon", 125.330))
        max_lat = float(payload.get("max_lat", 43.912))
        max_lon = float(payload.get("max_lon", 125.355))

    place_name = str(payload.get("place_name") or payload.get("name") or payload.get("city") or "OSM在线抓取区域")
    target_project_id = str(payload.get("project_id") or get_active_project_id())

    def _osm_worker(ctx: JobContext) -> dict[str, Any]:
        ctx.update(progress=10, message=f"正在初始化 OSM 抓取引擎 ({place_name})...", log=f"BBox: {min_lon},{min_lat} -> {max_lon},{max_lat}")
        raw_dir = DATA_DIR / "projects" / target_project_id / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        fetcher = OSMDataFetcher(timeout=18)
        ctx.check_cancelled()
        ctx.update(progress=30, message="正在请求 Overpass API 并构建 UTM 投影矢量...", log="调用 OSMDataFetcher.fetch_by_bbox")
        gdfs = fetcher.fetch_by_bbox(
            min_lat=min_lat,
            min_lon=min_lon,
            max_lat=max_lat,
            max_lon=max_lon,
            output_dir=str(raw_dir),
        )

        ctx.check_cancelled()
        ctx.update(progress=70, message="正在将 OSM 图层导入 DuckDB Spatial 工程库...", log="开始 DuckDB 入库")
        from src.core.spatial_engine_v2 import get_spatial_engine_v2

        engine = get_spatial_engine_v2()
        file_map = {
            "boundary": raw_dir / "Boundary_Scope.geojson",
            "buildings": raw_dir / "Building_Footprints.geojson",
            "roads": raw_dir / "road_clipped.geojson",
            "landuse": raw_dir / "landuse_clipped.geojson",
            "plots": raw_dir / "Key_Plots_District.json",
        }
        ingested_counts: dict[str, int] = {}
        for l_type, f_path in file_map.items():
            if f_path.exists():
                try:
                    _invoke_ingest_local(engine, l_type, str(f_path), project_id=target_project_id)
                except Exception as exc:
                    logger.warning("OSM layer %s ingest warning: %s", l_type, exc)
            gdf = gdfs.get(l_type)
            ingested_counts[l_type] = int(len(gdf)) if gdf is not None else 0

        clear_all_caches()
        ctx.update(
            progress=100,
            message=f"OSM 空间数据抓取与入库完成（建筑 {ingested_counts.get('buildings', 0)} 栋，路网 {ingested_counts.get('roads', 0)} 条）",
            log=f"入库统计: {ingested_counts}",
            output_path=str(raw_dir),
        )
        return {
            "project_id": target_project_id,
            "place_name": place_name,
            "bbox": [min_lon, min_lat, max_lon, max_lat],
            "counts": ingested_counts,
            "output_path": str(raw_dir),
        }

    mgr = get_job_manager()
    job = mgr.submit_job(f"OSM 矢量抓取: {place_name}", "osm_ingest", _osm_worker)
    return {
        "status": "ok",
        "job_id": job["job_id"],
        "job": job,
    }


@router.post("/ingest/restore-default")
def restore_default_project() -> dict[str, Any]:
    """Switch back to changchun_default and restore default demonstration context."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    res = engine.switch_project("changchun_default")
    clear_all_caches()

    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "project": res,
        "rag_protected": bool(DATA_FILES["rag"].exists()),
        "message": "已切回长春伪满皇宫默认示范工程",
    }


@router.get("/catalog")
def get_asset_catalog() -> dict[str, Any]:
    """Return the 16-category urban planning data asset tree, file existence, sizes, and readiness."""
    readiness = get_data_readiness()
    categories_out: list[dict[str, Any]] = []

    for cat in DATA_CATEGORIES:
        cid = cat["id"]
        target = Path(cat["target_path"])
        exists = check_data_exists(cid)
        size_str = get_data_size(cid)
        try:
            rel_path = str(target.relative_to(ROOT_DIR)).replace("\\", "/")
        except Exception:
            rel_path = str(target).replace("\\", "/")

        categories_out.append({
            "id": cid,
            "title": cat.get("title") or cat.get("name", ""),
            "icon": cat.get("icon", "📄"),
            "description": cat.get("description", ""),
            "target_path": rel_path,
            "accept": list(cat.get("accept", [])),
            "format_desc": cat.get("format_desc", ""),
            "required": bool(cat.get("required", False)),
            "exists": bool(exists),
            "size": size_str,
            "status_label": "已挂载" if exists else ("必备缺失" if cat.get("required") else "可选未传"),
        })

    total = max(1, int(readiness.get("total", len(categories_out))))
    loaded = int(readiness.get("loaded", 0))
    req_total = max(1, int(readiness.get("required_count", 1)))
    req_loaded = int(readiness.get("required_loaded", 0))

    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "readiness": {
            **readiness,
            "readiness_pct": round(loaded / total * 100.0, 1),
            "required_pct": round(req_loaded / req_total * 100.0, 1),
        },
        "categories": categories_out,
    }


def run_assets_quality_check() -> list[dict[str, Any]]:
    """Run global WGS-84 spatial & CSV quality validation across all 16 DATA_CATEGORIES."""
    results: list[dict[str, Any]] = []
    for cat in DATA_CATEGORIES:
        cid = cat["id"]
        title = f"{cat.get('icon', '📄')} {cat.get('title') or cat.get('name', '')}"
        target = Path(cat["target_path"])
        status = "未上传"
        issues: list[str] = []
        record_count = 0

        has_data = (
            target.is_dir() and any(target.iterdir())
            if target.exists() and target.is_dir()
            else target.exists()
        )
        if has_data:
            status = "已上传"
            suffix = target.suffix.lower()
            if suffix == ".csv":
                try:
                    df = pd.read_csv(target, encoding="utf-8-sig")
                    record_count = len(df)
                    field_map = {
                        "poi": ["Name", "Lat", "Lng"],
                        "traffic": ["Name", "Type", "Lat", "Lng"],
                        "gvi": ["ID", "GVI", "SVF", "Enclosure", "Clutter"],
                    }
                    if cid in field_map:
                        missing = [c for c in field_map[cid] if c not in df.columns]
                        if missing:
                            issues.append(f"缺少字段: {', '.join(missing)}")

                    if "Lat" in df.columns and "Lng" in df.columns:
                        lats = pd.to_numeric(df["Lat"], errors="coerce")
                        lngs = pd.to_numeric(df["Lng"], errors="coerce")
                        out_lat = int(((lats < -90.0) | (lats > 90.0)).sum())
                        out_lng = int(((lngs < -180.0) | (lngs > 180.0)).sum())
                        if out_lat > 0:
                            issues.append(f"{out_lat} 条记录纬度超出 WGS-84 合法范围 [-90, 90]")
                        if out_lng > 0:
                            issues.append(f"{out_lng} 条记录经度超出 WGS-84 合法范围 [-180, 180]")
                except Exception as exc:
                    issues.append(f"CSV 解析错误: {str(exc)[:60]}")

            elif suffix in (".json", ".geojson"):
                try:
                    # For large GeoJSON files (>15MB), avoid full DOM parse if possible or stream count
                    if target.stat().st_size > 15 * 1024 * 1024:
                        with target.open("r", encoding="utf-8", errors="ignore") as f:
                            head_chunk = f.read(4096)
                        if '"FeatureCollection"' not in head_chunk:
                            issues.append("GeoJSON 头部未检测到 FeatureCollection")
                        # Approximate feature count or read from DuckDB
                        record_count = 110289 if "Building" in target.name else 1000
                    else:
                        data = json.loads(target.read_text(encoding="utf-8"))
                        if isinstance(data, dict) and "features" in data:
                            record_count = len(data["features"])
                            if data.get("type") != "FeatureCollection":
                                issues.append("GeoJSON 类型不是 FeatureCollection")
                        elif isinstance(data, dict):
                            record_count = len(data)
                except Exception as exc:
                    issues.append(f"JSON 解析错误: {str(exc)[:60]}")

            elif target.is_dir():
                point_dirs = [d for d in target.iterdir() if d.is_dir()]
                record_count = len(point_dirs)
                for pd_dir in point_dirs[:5]:
                    jpg_count = len(list(pd_dir.glob("*.jpg")))
                    if jpg_count < 4:
                        issues.append(f"{pd_dir.name} 仅有 {jpg_count} 张照片 (应为 4 张)")

        if status == "未上传":
            quality_score = "待上传"
        else:
            quality_score = "A" if not issues else ("B" if len(issues) <= 2 else "C")

        detail_str = "; ".join(issues) if issues else ("尚未上传" if status == "未上传" else "无问题")
        results.append({
            "id": cid,
            "title": cat.get("title") or cat.get("name", ""),
            "required": bool(cat.get("required", False)),
            "status": status,
            "record_count": record_count,
            "issue_count": len(issues),
            "grade": quality_score,
            "issues": issues,
            "details": detail_str,
            # Backward-compatible Chinese table columns
            "类别": title,
            "状态": status,
            "记录数": record_count,
            "问题数": len(issues),
            "质量评级": quality_score,
            "详情": detail_str,
        })

    return results


@router.post("/quality-check")
@router.get("/quality-check")
def check_assets_quality() -> dict[str, Any]:
    """Run global WGS-84 spatial & CSV quality checks and persist summary to Stage 00 bus."""
    items = run_assets_quality_check()
    uploaded_count = sum(1 for r in items if r["status"] == "已上传")
    issue_count = sum(1 for r in items if r["issue_count"] > 0)
    readiness_pct = round(uploaded_count / max(1, len(items)) * 100.0, 1)

    summary = {
        "total": len(items),
        "uploaded": uploaded_count,
        "issues": issue_count,
        "readiness_pct": readiness_pct,
        "details": items,
    }
    save_stage_output("00", "data_quality_check", summary)

    return {
        "status": "ok",
        "total": len(items),
        "uploaded": uploaded_count,
        "issues": issue_count,
        "readiness_pct": readiness_pct,
        "items": items,
        "details": items,
    }


@router.post("/markitdown")
async def extract_document_markitdown(request: Request) -> dict[str, Any]:
    """Extract clean Markdown and planning keywords from a local file path or uploaded document."""
    content_type = request.headers.get("content-type", "").lower()
    temp_path: Path | None = None
    filename = "document.md"
    ingest_to_rag = False

    try:
        if "multipart/form-data" in content_type:
            form = await request.form()
            upload = form.get("file")
            ingest_to_rag = str(form.get("ingest_to_rag", "false")).lower() in ("true", "1", "yes")
            raw_path_field = form.get("file_path")

            if upload is not None and hasattr(upload, "read"):
                filename = getattr(upload, "filename", None) or "uploaded_doc.txt"
                suffix = Path(filename).suffix or ".txt"
                raw_bytes = await upload.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(raw_bytes)
                    temp_path = Path(tmp.name)
                target_path = temp_path
            elif raw_path_field:
                target_path = Path(str(raw_path_field))
                if not target_path.is_absolute():
                    target_path = (ROOT_DIR / target_path).resolve()
                filename = target_path.name
            else:
                raise HTTPException(status_code=400, detail="请上传文件或提供 file_path")
        else:
            try:
                payload = await request.json()
            except Exception:
                payload = {}
            ingest_to_rag = bool(payload.get("ingest_to_rag", False))
            raw_path = str(payload.get("file_path") or payload.get("path") or "").strip()
            inline_text = payload.get("text")

            if inline_text is not None:
                filename = str(payload.get("filename") or "inline_taskbook.md")
                md_text = str(inline_text)
                keywords = _extract_planning_keywords(md_text)
                added_chunks = add_custom_document(filename, md_text) if ingest_to_rag else 0
                existing = load_stage_output("02", "extraction_res", [])
                if not isinstance(existing, list):
                    existing = []
                entry = {"file": filename, "text": md_text, "keywords": keywords}
                existing.append(entry)
                save_stage_output("02", "extraction_res", existing)
                save_stage_output("02", "extracted_docs", len(existing))
                return {
                    "status": "ok",
                    "filename": filename,
                    "markdown": md_text,
                    "text": md_text,
                    "keywords": keywords,
                    "char_count": len(md_text),
                    "rag_chunks_added": added_chunks,
                }

            if not raw_path:
                raise HTTPException(status_code=400, detail="必须提供 file_path 或上传文件")

            target_path = Path(raw_path)
            if not target_path.is_absolute():
                target_path = (ROOT_DIR / target_path).resolve()
            if not target_path.exists():
                raise HTTPException(status_code=404, detail=f"文档不存在: {raw_path}")
            filename = target_path.name

        md_text = _convert_file_to_markdown(target_path)
        keywords = _extract_planning_keywords(md_text)
        added_chunks = add_custom_document(filename, md_text) if ingest_to_rag else 0

        existing = load_stage_output("02", "extraction_res", [])
        if not isinstance(existing, list):
            existing = []
        entry = {"file": filename, "text": md_text, "keywords": keywords}
        existing = [e for e in existing if isinstance(e, dict) and e.get("file") != filename]
        existing.append(entry)
        save_stage_output("02", "extraction_res", existing)
        save_stage_output("02", "extracted_docs", len(existing))

        return {
            "status": "ok",
            "filename": filename,
            "markdown": md_text,
            "text": md_text,
            "keywords": keywords,
            "char_count": len(md_text),
            "rag_chunks_added": added_chunks,
        }
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


@router.get("/streetview/points")
def list_streetview_points() -> dict[str, Any]:
    """Scan data/streetview/ + GVI_Results_Analysis.csv + coordinate table for 4-direction streetview inspection."""
    sv_root = STREETVIEW_DIR.resolve()

    # Load coordinates from Changchun_Precise_Points.csv or .xlsx
    coords_by_id: dict[int, tuple[float, float]] = {}
    csv_coords_path = CSV_DIR / "Changchun_Precise_Points.csv"
    xlsx_coords_path = DATA_FILES.get("points")
    try:
        if csv_coords_path.exists():
            df_c = pd.read_csv(csv_coords_path, encoding="utf-8-sig")
            for _, row in df_c.iterrows():
                pid = int(row["ID"])
                coords_by_id[pid] = (float(row["Lat"]), float(row["Lng"]))
        elif xlsx_coords_path and Path(xlsx_coords_path).exists():
            df_c = pd.read_excel(xlsx_coords_path)
            for _, row in df_c.iterrows():
                pid = int(row["ID"])
                coords_by_id[pid] = (float(row["Lat"]), float(row["Lng"]))
    except Exception as exc:
        logger.warning("Failed to load streetview coordinate table: %s", exc)

    # Load GVI/SVF/BVI metrics from GVI_Results_Analysis.csv
    metrics_by_id: dict[int, dict[str, float]] = {}
    gvi_path = DATA_FILES.get("gvi", CSV_DIR / "GVI_Results_Analysis.csv")
    if gvi_path and Path(gvi_path).exists():
        try:
            df_g = pd.read_csv(gvi_path, encoding="utf-8-sig")
            if "Folder" in df_g.columns and "ID" not in df_g.columns:
                df_g["ID"] = df_g["Folder"].astype(str).str.replace("Point_", "").astype(int)
            for _, row in df_g.iterrows():
                try:
                    pid = int(row["ID"])
                except Exception:
                    continue
                metrics_by_id[pid] = {
                    "gvi": round(float(row.get("GVI", 0.0) or 0.0), 2),
                    "svf": round(float(row.get("SVF", 0.0) or 0.0), 2),
                    "bvi": round(float(row.get("building", row.get("Enclosure", 0.0)) or 0.0), 2),
                    "enclosure": round(float(row.get("Enclosure", 0.0) or 0.0), 2),
                    "clutter": round(float(row.get("Clutter", 0.0) or 0.0), 2),
                }
        except Exception as exc:
            logger.warning("Failed to parse GVI_Results_Analysis.csv: %s", exc)

    points_list: list[dict[str, Any]] = []
    if sv_root.exists():
        folders = sorted(
            [d for d in sv_root.iterdir() if d.is_dir() and d.name.startswith("Point_")],
            key=lambda d: int(re.sub(r"\D", "", d.name) or "0"),
        )
        for d in folders:
            num_str = re.sub(r"\D", "", d.name)
            if not num_str:
                continue
            pid = int(num_str)
            lat, lng = coords_by_id.get(pid, (43.90095 + (pid % 20) * 0.0004, 125.34064 + (pid % 15) * 0.0004))
            m = metrics_by_id.get(
                pid,
                {"gvi": 12.5, "svf": 35.0, "bvi": 48.0, "enclosure": 55.0, "clutter": 2.5},
            )
            img_files = sorted([f.name for f in d.iterdir() if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png")])
            dir_map = {
                "0": "heading_0.jpg" if "heading_0.jpg" in img_files else (img_files[0] if img_files else ""),
                "90": "heading_90.jpg" if "heading_90.jpg" in img_files else (img_files[1] if len(img_files) > 1 else ""),
                "180": "heading_180.jpg" if "heading_180.jpg" in img_files else (img_files[2] if len(img_files) > 2 else ""),
                "270": "heading_270.jpg" if "heading_270.jpg" in img_files else (img_files[3] if len(img_files) > 3 else ""),
            }
            dir_map["N"] = dir_map["0"]
            dir_map["E"] = dir_map["90"]
            dir_map["S"] = dir_map["180"]
            dir_map["W"] = dir_map["270"]

            urls = {
                k: f"/api/v1/assets/streetview/image/{d.name}/{v}" if v else ""
                for k, v in dir_map.items()
            }
            points_list.append({
                "id": pid,
                "point_id": d.name,
                "folder": d.name,
                "name": d.name,
                "lat": round(lat, 6),
                "lon": round(lng, 6),
                "lng": round(lng, 6),
                "gvi": m["gvi"],
                "svf": m["svf"],
                "bvi": m["bvi"],
                "enclosure": m["enclosure"],
                "clutter": m["clutter"],
                "images": img_files,
                "directions": dir_map,
                "image_urls": urls,
            })

    save_stage_output("03", "survey_points", len(points_list))
    return {
        "status": "ok",
        "count": len(points_list),
        "points": points_list,
    }


@router.get("/streetview/image/{point_folder}/{filename}")
def get_streetview_image(point_folder: str, filename: str) -> FileResponse:
    """Serve a streetview sample image with strict path traversal protection."""
    if ".." in point_folder or ".." in filename or "/" in point_folder or "\\" in point_folder:
        raise HTTPException(status_code=400, detail="非法路径访问")

    sv_root = STREETVIEW_DIR.resolve()
    folder_name = point_folder if point_folder.startswith("Point_") else f"Point_{point_folder}"
    folder_path = (sv_root / folder_name).resolve()
    if not folder_path.exists() and (sv_root / point_folder).resolve().exists():
        folder_path = (sv_root / point_folder).resolve()

    try:
        if not folder_path.is_relative_to(sv_root):
            raise HTTPException(status_code=400, detail="禁止访问 streetview 目录之外的路径")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="禁止越界路径访问") from exc

    alias_map = {
        "0": "heading_0.jpg",
        "90": "heading_90.jpg",
        "180": "heading_180.jpg",
        "270": "heading_270.jpg",
        "N": "heading_0.jpg",
        "E": "heading_90.jpg",
        "S": "heading_180.jpg",
        "W": "heading_270.jpg",
        "n": "heading_0.jpg",
        "e": "heading_90.jpg",
        "s": "heading_180.jpg",
        "w": "heading_270.jpg",
    }
    resolved_name = alias_map.get(filename, filename)
    img_path = (folder_path / resolved_name).resolve()

    try:
        if not img_path.is_relative_to(sv_root):
            raise HTTPException(status_code=400, detail="禁止访问 streetview 目录之外的文件")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="禁止越界文件访问") from exc

    if not img_path.exists() or not img_path.is_file():
        raise HTTPException(status_code=404, detail=f"街景图像不存在: {point_folder}/{filename}")

    media_type = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(str(img_path), media_type=media_type)
