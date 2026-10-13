"""Unit tests for workbench lazy rendering and anti-nesting embedded mode."""

import unittest
from unittest.mock import MagicMock, patch
import streamlit as st

from src.ui.app_shell import render_engine_status_alert, render_top_nav
from src.ui.design_system import render_page_banner, render_workbench_subnav


def _mock_radio(label, options, index=0, **kwargs):
    return options[index] if index < len(options) else options[0]


class TestEmbeddedModeAntiNesting(unittest.TestCase):
    def setUp(self):
        st.session_state.clear()
        st.query_params.clear()

    def tearDown(self):
        st.session_state.clear()
        st.query_params.clear()

    def test_top_nav_skips_when_embedded(self):
        st.session_state["_embedded_mode"] = True
        with patch("src.ui.app_shell.load_global_css") as mock_css:
            render_top_nav()
            mock_css.assert_not_called()

    def test_engine_status_alert_skips_when_embedded(self):
        st.session_state["_embedded_mode"] = True
        with patch("src.ui.app_shell.check_engine_status") as mock_status:
            render_engine_status_alert()
            mock_status.assert_not_called()

    def test_page_banner_compacts_when_embedded(self):
        st.session_state["_embedded_mode"] = True
        with patch("src.ui.design_system.render_section_intro") as mock_intro:
            render_page_banner(title="Test Stage", description="Desc", eyebrow="Stage 01")
            mock_intro.assert_called_once_with(title="Test Stage", description="Desc", eyebrow="Stage 01")


class TestWorkbenchSegmentedSubnav(unittest.TestCase):
    def setUp(self):
        st.session_state.clear()
        st.query_params.clear()
        self.radio_patcher = patch.object(st, "radio", side_effect=_mock_radio)
        self.radio_patcher.start()

    def tearDown(self):
        self.radio_patcher.stop()
        st.session_state.clear()
        st.query_params.clear()

    def test_workbench1_subnav_default_and_query_param(self):
        options = [
            "🏢 空间诊断与 AHP-MPI 潜力沙盘",
            "📦 多源空间资产与调研资料",
            "🖥️ 全屏空间监控大屏",
        ]
        opt_to_param = {
            options[0]: "diagnosis",
            options[1]: "assets",
            options[2]: "datav",
        }
        param_to_opt = {
            "diagnosis": options[0],
            "assets": options[1],
            "datav": options[2],
        }

        # 1. Default when no query param
        selected = render_workbench_subnav(
            options=options,
            option_to_param=opt_to_param,
            param_to_option=param_to_opt,
            default_sub="diagnosis",
            widget_key="test_wb1",
        )
        self.assertEqual(selected, options[0])
        self.assertEqual(st.query_params.get("sub"), "diagnosis")

        # 2. Pre-selection via query param
        st.query_params["sub"] = "assets"
        selected = render_workbench_subnav(
            options=options,
            option_to_param=opt_to_param,
            param_to_option=param_to_opt,
            default_sub="diagnosis",
            widget_key="test_wb1",
        )
        self.assertEqual(selected, options[1])
        self.assertEqual(st.query_params.get("sub"), "assets")

        # 3. Pre-selection via query param datav
        st.query_params["sub"] = "datav"
        selected = render_workbench_subnav(
            options=options,
            option_to_param=opt_to_param,
            param_to_option=param_to_opt,
            default_sub="diagnosis",
            widget_key="test_wb1",
        )
        self.assertEqual(selected, options[2])
        self.assertEqual(st.query_params.get("sub"), "datav")

    def test_workbench2_subnav_query_params(self):
        options = [
            "🤝 多主体博弈决策与设计纲要 (Stage 07)",
            "🗺️ 总体空间结构沙盘 (Stage 08)",
            "🎨 重点地段 AIGC 生形与卷帘对比 (Stage 10/15)",
        ]
        opt_to_param = {
            options[0]: "strategy",
            options[1]: "master_plan",
            options[2]: "aigc",
        }
        param_to_opt = {
            "strategy": options[0],
            "master_plan": options[1],
            "aigc": options[2],
        }

        st.query_params["sub"] = "master_plan"
        selected = render_workbench_subnav(
            options=options,
            option_to_param=opt_to_param,
            param_to_option=param_to_opt,
            default_sub="strategy",
            widget_key="test_wb2",
        )
        self.assertEqual(selected, options[1])
        self.assertEqual(st.query_params.get("sub"), "master_plan")

        st.query_params["sub"] = "aigc"
        selected = render_workbench_subnav(
            options=options,
            option_to_param=opt_to_param,
            param_to_option=param_to_opt,
            default_sub="strategy",
            widget_key="test_wb2",
        )
        self.assertEqual(selected, options[2])
        self.assertEqual(st.query_params.get("sub"), "aigc")

    def test_workbench3_subnav_query_params(self):
        options = [
            "📐 工程图纸与 AutoCAD DXF 导出 (Stage 13)",
            "📜 城市设计数字导则 (Word 规范) (Stage 12)",
            "🔧 多专项系统空间叠合 (Stage 09)",
            "📅 留改拆实施时序总图 (Stage 11)",
        ]
        opt_to_param = {
            options[0]: "delivery",
            options[1]: "guideline",
            options[2]: "systems",
            options[3]: "timing",
        }
        param_to_opt = {
            "delivery": options[0],
            "guideline": options[1],
            "systems": options[2],
            "timing": options[3],
        }

        st.query_params["sub"] = "guideline"
        selected = render_workbench_subnav(
            options=options,
            option_to_param=opt_to_param,
            param_to_option=param_to_opt,
            default_sub="delivery",
            widget_key="test_wb3",
        )
        self.assertEqual(selected, options[1])
        self.assertEqual(st.query_params.get("sub"), "guideline")

        st.query_params["sub"] = "timing"
        selected = render_workbench_subnav(
            options=options,
            option_to_param=opt_to_param,
            param_to_option=param_to_opt,
            default_sub="delivery",
            widget_key="test_wb3",
        )
        self.assertEqual(selected, options[3])
        self.assertEqual(st.query_params.get("sub"), "timing")


class TestWorkbenchLazyExecution(unittest.TestCase):
    def setUp(self):
        st.session_state.clear()
        st.query_params.clear()
        self.radio_patcher = patch.object(st, "radio", side_effect=_mock_radio)
        self.radio_patcher.start()

    def tearDown(self):
        self.radio_patcher.stop()
        st.session_state.clear()
        st.query_params.clear()

    def test_workbench2_lazy_execution_only_runs_active_stage(self):
        from importlib import import_module
        wb2 = import_module("pages.02_多主体博弈与空间AIGC工坊")

        st.query_params["sub"] = "master_plan"

        with patch.object(wb2, "render_top_nav"), \
             patch.object(wb2, "render_engine_status_alert"), \
             patch.object(wb2, "render_page_banner"), \
             patch.object(wb2, "render_stage07_page") as mock_s7, \
             patch.object(wb2, "render_stage08_page") as mock_s8, \
             patch.object(wb2, "render_stage10_page") as mock_s10:

            wb2.main()

            mock_s7.assert_not_called()
            mock_s8.assert_called_once()
            mock_s10.assert_not_called()
            self.assertFalse(st.session_state.get("_embedded_mode", False))

    def test_workbench3_lazy_execution_only_runs_active_stage(self):
        from importlib import import_module
        wb3 = import_module("pages.03_数字图则与工程交付枢纽")

        st.query_params["sub"] = "systems"

        with patch.object(wb3, "render_top_nav"), \
             patch.object(wb3, "render_engine_status_alert"), \
             patch.object(wb3, "render_page_banner"), \
             patch.object(wb3, "render_stage13_page") as mock_s13, \
             patch.object(wb3, "render_stage12_page") as mock_s12, \
             patch.object(wb3, "render_stage09_page") as mock_s9, \
             patch.object(wb3, "render_stage11_page") as mock_s11:

            wb3.main()

            mock_s13.assert_not_called()
            mock_s12.assert_not_called()
            mock_s9.assert_called_once()
            mock_s11.assert_not_called()
            self.assertFalse(st.session_state.get("_embedded_mode", False))

    def test_workbench1_lazy_execution_only_runs_active_stage(self):
        from importlib import import_module
        wb1 = import_module("pages.01_全息空间诊断与数据沙盘")

        st.query_params["sub"] = "assets"

        with patch.object(wb1, "render_top_nav"), \
             patch.object(wb1, "render_engine_status_alert"), \
             patch.object(wb1, "render_page_banner"), \
             patch.object(wb1, "render_stage04_page") as mock_s4, \
             patch.object(wb1, "_render_wb1_assets") as mock_assets, \
             patch.object(wb1, "_render_wb1_datav") as mock_datav:

            wb1.main()

            mock_s4.assert_not_called()
            mock_assets.assert_called_once()
            mock_datav.assert_not_called()
            self.assertFalse(st.session_state.get("_embedded_mode", False))


if __name__ == "__main__":
    unittest.main()
