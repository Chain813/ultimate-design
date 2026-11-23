"""Comprehensive FastAPI TestClient Integration Suite for UltimateDESIGN v7.0 Desktop Backend.

Verifies all 7 domain routers:
1. `/api/v1/system`: health, engines, projects (list/create/switch/delete)
2. `/api/v1/assets`: catalog, quality-check, streetview/points
3. `/api/v1/diagnosis`: fused-plots, mpi/compute, spatial-syntax/run, tiles/buildings/14/14011/6018.pbf, binary/gvi, datav/payload
4. `/api/v1/strategy`: stage06/state, stage06/generate/stream, stage07/negotiate/stream (SSE), stage07/matrix, stage08/landuse-sandbox
5. `/api/v1/aigc`: stage10/profile, stage10/before-after, stage15/config, stage15/depth-preview, stage15/polish-prompt, stage15/render
6. `/api/v1/delivery`: stage09/state, stage11/phasing, stage12/export-docx, stage13/drawings, stage13/export-dxf, stage16/skills, stage16/hearing/stream
7. `/api/v1/copilot`: chat/stream (SSE), history

Also asserts `SKILLS.md` Part 9: `data/rag_knowledge.json` exists and is 100% byte-for-byte unmodified after all API operations.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT))
if "desktop" in sys.modules:
    _d_mod = sys.modules["desktop"]
    _d_loc = str(getattr(_d_mod, "__file__", "") or getattr(_d_mod, "__path__", ""))
    if "tests" in _d_loc:
        del sys.modules["desktop"]

from fastapi.testclient import TestClient
import pytest

from desktop.backend.main import app
from src.config.paths import DATA_FILES, ROOT_DIR


def _compute_file_sha256(path: Path) -> str:
    assert path.exists(), f"Critical file missing: {path}"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_sse_events(raw_text: str) -> list[dict]:
    """Parse SSE response body into a list of JSON payloads from `data: ...` lines."""
    events: list[dict] = []
    for line in raw_text.splitlines():
        s = line.strip()
        if s.startswith("data:"):
            payload_str = s[len("data:") :].strip()
            if payload_str and payload_str != "[DONE]":
                try:
                    obj = json.loads(payload_str)
                    if isinstance(obj, dict):
                        events.append(obj)
                except Exception:
                    pass
    return events


@pytest.fixture(scope="module")
def rag_baseline_state() -> dict[str, object]:
    rag_path = Path(DATA_FILES["rag"])
    assert rag_path.exists(), "data/rag_knowledge.json must exist before running API tests"
    raw = rag_path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    return {
        "path": rag_path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size": len(raw),
        "count": len(data) if isinstance(data, dict) else 0,
    }


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as tc:
        yield tc


def test_01_system_health_engines_and_projects(client: TestClient, rag_baseline_state: dict) -> None:
    # 1. /api/v1/system/health
    r_health = client.get("/api/v1/system/health")
    assert r_health.status_code == 200
    h_data = r_health.json()
    assert h_data["status"] == "ok"
    assert h_data["version"] == "7.0.0"
    assert h_data["rag_protected"] is True

    # 2. /api/v1/system/engines
    r_eng = client.get("/api/v1/system/engines")
    assert r_eng.status_code == 200
    e_data = r_eng.json()
    assert e_data["status"] == "ok"
    assert e_data["rag_protected"] is True
    assert e_data["rag_chunks"] == rag_baseline_state["count"]
    assert "stages" in e_data and len(e_data["stages"]) == 17

    # 3. /api/v1/system/projects (GET -> POST -> switch back -> DELETE)
    r_proj = client.get("/api/v1/system/projects")
    assert r_proj.status_code == 200
    p_data = r_proj.json()
    assert p_data["status"] == "ok"
    assert isinstance(p_data["projects"], list)
    assert any((p.get("project_id") or p.get("id")) == "changchun_default" for p in p_data["projects"])

    # Create temporary project, verify RAG untouched, then switch back & delete
    temp_pid = "pytest_temp_urban_proj"
    r_create = client.post(
        "/api/v1/system/projects",
        json={"project_id": temp_pid, "name": "自动化测试更新基地", "city": "测试市", "switch": True},
    )
    assert r_create.status_code == 200
    assert r_create.json()["rag_protected"] is True

    r_switch_back = client.post("/api/v1/system/projects/changchun_default/switch")
    assert r_switch_back.status_code == 200
    assert r_switch_back.json()["active_project_id"] == "changchun_default"

    r_del = client.delete(f"/api/v1/system/projects/{temp_pid}")
    assert r_del.status_code == 200
    assert r_del.json()["rag_protected"] is True


def test_02_assets_catalog_quality_and_streetview(client: TestClient) -> None:
    # 1. /api/v1/assets/catalog
    r_cat = client.get("/api/v1/assets/catalog")
    assert r_cat.status_code == 200
    cat_data = r_cat.json()
    assert cat_data["status"] == "ok"
    assert len(cat_data["categories"]) == 16
    assert "readiness" in cat_data

    # 2. /api/v1/assets/quality-check
    r_qc = client.post("/api/v1/assets/quality-check")
    assert r_qc.status_code == 200
    qc_data = r_qc.json()
    assert qc_data["status"] == "ok"
    assert qc_data["total"] == 16
    assert isinstance(qc_data["items"], list)

    # 3. /api/v1/assets/streetview/points
    r_sv = client.get("/api/v1/assets/streetview/points")
    assert r_sv.status_code == 200
    sv_data = r_sv.json()
    assert sv_data["status"] == "ok"
    assert sv_data["count"] > 0
    first_pt = sv_data["points"][0]
    assert "gvi" in first_pt and "svf" in first_pt and "image_urls" in first_pt


def test_03_diagnosis_fused_plots_mpi_syntax_mvt_binary_and_datav(client: TestClient) -> None:
    # 1. /api/v1/diagnosis/fused-plots
    r_fp = client.get("/api/v1/diagnosis/fused-plots")
    assert r_fp.status_code == 200
    fp_data = r_fp.json()
    assert fp_data["status"] == "ok"
    assert fp_data["count"] >= 1
    assert isinstance(fp_data["plots"], list)
    assert fp_data["geojson"]["type"] == "FeatureCollection"

    # 2. /api/v1/diagnosis/mpi/compute
    r_mpi = client.post(
        "/api/v1/diagnosis/mpi/compute",
        json={"weights": {"w_poi": 45.0, "w_soc": 30.0, "w_env": 25.0}},
    )
    assert r_mpi.status_code == 200
    mpi_data = r_mpi.json()
    assert mpi_data["status"] == "ok"
    assert len(mpi_data["ranking"]) >= 1
    assert mpi_data["top_score"] > 0

    # 3. /api/v1/diagnosis/spatial-syntax/run
    r_syn = client.post("/api/v1/diagnosis/spatial-syntax/run")
    assert r_syn.status_code == 200
    syn_data = r_syn.json()
    assert syn_data["status"] == "ok"
    assert "summary" in syn_data

    # 4. /api/v1/diagnosis/tiles/buildings/14/14011/6018.pbf
    r_tile = client.get("/api/v1/diagnosis/tiles/buildings/14/14011/6018.pbf")
    assert r_tile.status_code == 200
    assert "application/vnd.mapbox-vector-tile" in r_tile.headers.get("content-type", "")
    assert isinstance(r_tile.content, bytes)

    # 5. /api/v1/diagnosis/binary/gvi
    r_bin = client.get("/api/v1/diagnosis/binary/gvi")
    assert r_bin.status_code == 200
    assert "application/octet-stream" in r_bin.headers.get("content-type", "")
    assert len(r_bin.content) >= 4

    # 6. /api/v1/diagnosis/datav/payload
    r_dv = client.get("/api/v1/diagnosis/datav/payload")
    assert r_dv.status_code == 200
    dv_data = r_dv.json()
    assert isinstance(dv_data, dict)
    assert "hud" in dv_data or "status" in dv_data


def test_04_strategy_stage06_stage07_negotiate_sse_and_stage08_sandbox(client: TestClient) -> None:
    # 1. Stage 06 state & SSE generate stream
    r_s06 = client.get("/api/v1/strategy/stage06/state")
    assert r_s06.status_code == 200
    assert r_s06.json()["status"] == "ok"

    r_s06_stream = client.post(
        "/api/v1/strategy/stage06/generate/stream",
        json={"section": "design_concept"},
    )
    assert r_s06_stream.status_code == 200
    s06_events = _parse_sse_events(r_s06_stream.text)
    assert any((e.get("type") or e.get("event")) == "done" for e in s06_events)

    # 2. /api/v1/strategy/stage07/negotiate/stream (SSE)
    r_neg = client.post(
        "/api/v1/strategy/stage07/negotiate/stream",
        json={
            "topic": "长春水产大市场历史视廊控高、15分钟社区净菜配套与文商旅活化协商",
            "rounds": 3,
            "weights": {"gov": 0.4, "resident": 0.3, "dev": 0.3},
        },
    )
    assert r_neg.status_code == 200
    assert "text/event-stream" in r_neg.headers.get("content-type", "")
    events = _parse_sse_events(r_neg.text)
    event_types = {e.get("type") or e.get("event") for e in events}
    assert "round_start" in event_types
    assert "agent_speech" in event_types
    assert "round_consensus" in event_types
    assert "final_summary" in event_types

    # Verify 5D radar dimensions & RAG citations in negotiation events
    consensus_ev = next(e for e in events if (e.get("type") or e.get("event")) == "round_consensus")
    assert set(consensus_ev["dimensions"]) == {"空间品质", "经济可行", "民生保障", "历史风貌", "法规合规"}
    speech_ev = next(e for e in events if (e.get("type") or e.get("event")) == "agent_speech")
    assert len(speech_ev.get("rag_citations", [])) >= 1

    # 3. /api/v1/strategy/stage07/matrix
    r_mat = client.get("/api/v1/strategy/stage07/matrix")
    assert r_mat.status_code == 200
    assert len(r_mat.json()["rows"]) >= 3

    # 4. /api/v1/strategy/stage08/landuse-sandbox (GET & PUT)
    r_sb_get = client.get("/api/v1/strategy/stage08/landuse-sandbox")
    assert r_sb_get.status_code == 200
    assert "gfa_balance" in r_sb_get.json()

    r_sb_put = client.put(
        "/api/v1/strategy/stage08/landuse-sandbox",
        json={
            "commercial": 24.0,
            "residential": 36.0,
            "green_open": 18.0,
            "public_facility": 10.0,
            "cultural_heritage": 7.0,
            "target_far": 1.35,
        },
    )
    assert r_sb_put.status_code == 200
    sb_data = r_sb_put.json()
    assert sb_data["status"] == "ok"
    assert sb_data["compliance"]["far_compliant"] is True
    assert sb_data["compliance"]["green_compliant"] is True
    assert len(sb_data["echarts_pie"]) == 6


def test_05_aigc_stage10_and_stage15(client: TestClient) -> None:
    # 1. /api/v1/aigc/stage10/profile
    r_p10 = client.get("/api/v1/aigc/stage10/profile")
    assert r_p10.status_code == 200
    p10_data = r_p10.json()
    assert p10_data["status"] == "ok"
    assert len(p10_data["radar_metrics"]) >= 5
    assert "statutory_redlines" in p10_data
    assert "before_after" in p10_data

    # 2. /api/v1/aigc/stage15/config
    r_c15 = client.get("/api/v1/aigc/stage15/config")
    assert r_c15.status_code == 200
    c15_data = r_c15.json()
    assert c15_data["status"] == "ok"
    assert len(c15_data["styles"]) == 6
    expected_styles = {
        "历史街区修缮",
        "现代商业活力街区",
        "生态海绵绿轴",
        "工业遗产文创园",
        "混合TOD社区",
        "寒地全季漫步街区",
    }
    assert {s["name"] for s in c15_data["styles"]} == expected_styles

    # 3. /api/v1/aigc/stage15/polish-prompt
    r_pol = client.post(
        "/api/v1/aigc/stage15/polish-prompt",
        json={
            "description": "保留大跨度工业桁架，植入新中式滨水文旅客厅与全季阳光连廊",
            "strategy_styles": ["工业遗产文创园", "寒地全季漫步街区"],
        },
    )
    assert r_pol.status_code == 200
    pol_data = r_pol.json()
    assert pol_data["status"] == "ok"
    assert "masterpiece" in pol_data["prompt_en"].lower()
    assert len(pol_data["negative_prompt"]) > 20


    # 4. /api/v1/aigc/stage15/depth-preview & /render
    r_dp = client.post(
        "/api/v1/aigc/stage15/depth-preview",
        json={"mode": "white_model", "view_preset": "birdseye_sw", "width": 512, "height": 384},
    )
    assert r_dp.status_code == 200
    assert Path(r_dp.json()["file_path"]).exists()

    r_ren = client.post(
        "/api/v1/aigc/stage15/render",
        json={"prompt": pol_data["prompt_en"], "strategy_style": "工业遗产文创园", "width": 512, "height": 384},
    )
    assert r_ren.status_code == 200
    assert "job_id" in r_ren.json()
    assert Path(r_ren.json()["output_path"]).exists()


def test_06_delivery_stage11_stage12_stage13_and_stage16(client: TestClient) -> None:
    # 0. Stage 09 state & SSE stream
    r_s09 = client.get("/api/v1/delivery/stage09/state")
    assert r_s09.status_code == 200
    r_s09_stream = client.post(
        "/api/v1/delivery/stage09/generate/stream",
        json={"section": "traffic_system"},
    )
    assert r_s09_stream.status_code == 200

    # 1. /api/v1/delivery/stage11/phasing
    r_ph = client.get("/api/v1/delivery/stage11/phasing")
    assert r_ph.status_code == 200
    ph_data = r_ph.json()
    assert ph_data["status"] == "ok"
    assert len(ph_data["phases"]) == 3
    assert len(ph_data["echarts_gantt"]) >= 5
    assert len(ph_data["classification_table"]) >= 1

    # 2. /api/v1/delivery/stage12/state & /export-docx
    r_s12 = client.get("/api/v1/delivery/stage12/state")
    assert r_s12.status_code == 200
    assert len(r_s12.json()["chapters"]) == 9

    r_docx = client.post(
        "/api/v1/delivery/stage12/export-docx",
        json={"filename": "pytest_statutory_guideline.docx"},
    )
    assert r_docx.status_code == 200
    docx_data = r_docx.json()
    assert docx_data["status"] == "ok"
    docx_path = Path(docx_data["file_path"])
    assert docx_path.exists() and docx_path.stat().st_size > 1000

    # 3. /api/v1/delivery/stage13/drawings, /compose-a3, /export-dxf & /compile-report
    r_drw = client.get("/api/v1/delivery/stage13/drawings")
    assert r_drw.status_code == 200
    assert len(r_drw.json()["catalog"]) >= 15

    r_a3 = client.post(
        "/api/v1/delivery/stage13/compose-a3",
        json={"drawing_number": "DR-004", "title": "现状区位与规划范围图"},
    )
    assert r_a3.status_code == 200
    assert Path(r_a3.json()["file_path"]).exists()

    r_dxf = client.post(
        "/api/v1/delivery/stage13/export-dxf",
        json={"filename": "pytest_statutory_plan_AC1015.dxf", "max_buildings": 250},
    )
    assert r_dxf.status_code == 200
    dxf_data = r_dxf.json()
    assert dxf_data["status"] == "ok"
    assert dxf_data["acad_version"] == "AC1015"
    assert dxf_data["codepage"] == "ANSI_936"
    dxf_path = Path(dxf_data["file_path"])
    assert dxf_path.exists()
    dxf_head = dxf_path.read_text(encoding="utf-8", errors="ignore")[:1000]
    assert "AC1015" in dxf_head and "ANSI_936" in dxf_head

    r_rep = client.post(
        "/api/v1/delivery/stage13/compile-report",
        json={"mode": "light"},
    )
    assert r_rep.status_code == 200
    assert "job_id" in r_rep.json()
    assert Path(r_rep.json()["file_path"]).exists()

    # 4. /api/v1/delivery/stage16/skills & /hearing/stream
    r_sk = client.get("/api/v1/delivery/stage16/skills")
    assert r_sk.status_code == 200
    sk_data = r_sk.json()
    assert sk_data["status"] == "ok"
    assert sk_data["parts_count"] >= 12  # Parts 0 through 11
    assert len(sk_data["scenarios"]) >= 3

    r_hear = client.post("/api/v1/delivery/stage16/hearing/stream", json={})
    assert r_hear.status_code == 200
    hear_events = _parse_sse_events(r_hear.text)
    assert any((e.get("type") or e.get("event")) == "hearing_verdict" for e in hear_events)


def test_07_copilot_chat_stream_and_rag_integrity(client: TestClient, rag_baseline_state: dict) -> None:
    # 1. /api/v1/copilot/chat/stream (SSE)
    r_chat = client.post(
        "/api/v1/copilot/chat/stream",
        json={
            "message": "长春水产大市场更新项目的法定容积率、建筑限高和绿地率底线是多少？",
            "active_stage": "07",
        },
    )
    assert r_chat.status_code == 200
    assert "text/event-stream" in r_chat.headers.get("content-type", "")
    events = _parse_sse_events(r_chat.text)
    assert any(e.get("type") == "citations" for e in events)
    assert any(e.get("type") == "done" for e in events)
    done_ev = next(e for e in events if e.get("type") == "done")
    assert len(done_ev.get("content", "")) > 40

    # 2. Assert `data/rag_knowledge.json` exists and is 100% unmodified after all API tests!
    rag_path: Path = rag_baseline_state["path"]
    assert rag_path.exists(), "data/rag_knowledge.json was deleted!"
    after_sha256 = _compute_file_sha256(rag_path)
    after_size = rag_path.stat().st_size
    assert after_sha256 == rag_baseline_state["sha256"], "data/rag_knowledge.json content was modified!"
    assert after_size == rag_baseline_state["size"], "data/rag_knowledge.json file size changed!"


def test_08_spa_root_and_built_assets_return_200(client: TestClient) -> None:
    """Guard against static mount shadowing `/assets/index-*.js` or `.css`."""
    import re

    r_root = client.get("/")
    assert r_root.status_code == 200
    if "<div id=\"root\">" in r_root.text:
        js_match = re.search(r'src="([^"]+\.js)"', r_root.text)
        css_match = re.search(r'href="([^"]+\.css)"', r_root.text)
        assert js_match is not None, "Built SPA index.html missing JS bundle reference"
        assert css_match is not None, "Built SPA index.html missing CSS bundle reference"
        r_js = client.get(js_match.group(1).lstrip("."))
        r_css = client.get(css_match.group(1).lstrip("."))
        assert r_js.status_code == 200 and len(r_js.content) > 10000
        assert r_css.status_code == 200 and len(r_css.content) > 1000
