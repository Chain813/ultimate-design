import pytest
from unittest.mock import MagicMock
from src.engines.key_plot_engine import KeyPlot
from src.engines.thesis_pipeline import _get_plot_names, run_full_pipeline


def test_get_plot_names_uses_key_plot_engine(monkeypatch):
    mock_plots = [
        KeyPlot(index=1, plot_id="1", name="地块甲", role="", area_ha=1.0, centroid=(0, 0)),
        KeyPlot(index=2, plot_id="2", name="地块乙", role="", area_ha=1.0, centroid=(0, 0)),
    ]
    monkeypatch.setattr(
        "src.engines.key_plot_engine.get_configured_key_plots",
        lambda: mock_plots
    )
    
    names = _get_plot_names()
    assert names == ["地块甲", "地块乙"]


def test_get_plot_names_fallback_on_exception(monkeypatch):
    def raise_err():
        raise RuntimeError("GIS file error")
        
    monkeypatch.setattr(
        "src.engines.key_plot_engine.get_configured_key_plots",
        raise_err
    )
    
    names = _get_plot_names()
    # Check that fallback names are returned
    assert len(names) == 5
    assert "老水产批发市场" in names


@pytest.mark.parametrize("num_plots", [1, 3, 6, 8])
def test_run_full_pipeline_dynamic_steps(monkeypatch, num_plots):
    # Mock configured key plots with varying count
    mock_plots = [
        KeyPlot(index=i, plot_id=str(i), name=f"地块-{i}", role="", area_ha=1.0, centroid=(0,0))
        for i in range(1, num_plots + 1)
    ]
    monkeypatch.setattr(
        "src.engines.key_plot_engine.get_configured_key_plots",
        lambda: mock_plots
    )
    
    # Mock all internal generator functions of thesis_pipeline to avoid actual run/LLM calls
    pipeline_module = "src.engines.thesis_pipeline"
    mocked_gens = [
        "_gen_diagnosis_report", "_gen_mpi_ranking", "_gen_case_benchmark",
        "_gen_design_concept", "_gen_strategy_matrix", "_gen_design_brief",
        "_gen_spatial_structure", "_gen_landuse_sandbox", "_gen_traffic_system",
        "_gen_public_space", "_gen_building_form", "_gen_landscape_style",
        "_gen_plot_metrics", "_gen_plot_personas", "_gen_plot_design",
        "_gen_region_phasing", "_gen_design_guideline", "_gen_supplementary"
    ]
    
    for gen in mocked_gens:
        monkeypatch.setattr(f"{pipeline_module}.{gen}", MagicMock())
        
    monkeypatch.setattr(f"{pipeline_module}.build_thesis_context", MagicMock())
    monkeypatch.setattr(f"{pipeline_module}.generate_single_section", MagicMock(return_value="mock section content"))
    
    mock_buf = MagicMock()
    mock_buf.getvalue.return_value = b"docx content"
    monkeypatch.setattr(f"{pipeline_module}.assemble_thesis_docx", lambda **kwargs: mock_buf)
    
    progress_calls = []
    def progress_callback(step, total, msg):
        progress_calls.append((step, total, msg))
        
    log_calls = []
    def log_callback(msg):
        log_calls.append(msg)
        
    run_full_pipeline(progress_callback=progress_callback, log_callback=log_callback, enable_deai=False, model="mock-model")
    
    # Verify that the reported total steps matches the calculation
    # total_steps calculation:
    # 2 (diagnosis + mpi) + 2 (case + concept) + 2 (strategy + brief) + 2 (structure + sand) +
    # 4 (traffic + public + form + landscape) + num_plots * 3 + 1 (phasing) + 1 (guideline) +
    # 8 (extra) + 27 (chapters) + 0 (deai) + 1 (docx) = 50 + num_plots * 3
    expected_total_steps = 50 + num_plots * 3
    
    assert len(progress_calls) > 0
    # Every callback should report the same total_steps
    assert all(call[1] == expected_total_steps for call in progress_calls)
    # The last callback should have step == expected_total_steps
    assert progress_calls[-1][0] == expected_total_steps
