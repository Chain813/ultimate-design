"""Reusable prompt panel for the locked-asset image output workflow."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import pandas as pd
import streamlit as st

from src.ui.design_system import render_summary_cards
from src.workflow.template_assets import (
    get_template_asset_rows,
    load_template_asset_manifest,
    summarize_template_assets_for_prompt,
)


def build_output_flow_prompt(manifest: Optional[Dict] = None) -> str:
    """Build the canonical final-output workflow prompt shown in the UI."""
    manifest = manifest or load_template_asset_manifest()
    rows = get_template_asset_rows(manifest)
    required_rows = [row for row in rows if row["必备"] == "是"]
    required_ready = sum(1 for row in required_rows if row["状态"] == "已上传")
    optional_ready = sum(1 for row in rows if row["必备"] != "是" and row["状态"] == "已上传")
    required_status = _format_rows(required_rows)
    optional_status = _format_rows(row for row in rows if row["必备"] != "是")
    asset_context = summarize_template_assets_for_prompt(manifest)

    return f"""固定资产出图流程提示词

当前状态：
- 必备固定资产：{required_ready}/{len(required_rows)}
- 建议扩展资产：{optional_ready}/{len(rows) - len(required_rows)}

必备资产状态：
{required_status}

建议资产状态：
{optional_status}

固定资产约束：
{asset_context}

最终出图流程：
1. 在 Stage 02 上传固定底图、研究范围红线、重点地块边界和固定图框。
2. 选择图纸类型，由 Prompt Compiler 检查精度等级和资产完整性。
3. 一级精度图纸缺少任一必备资产时，停止生成最终 Image 2.0 提示词。
4. 资产齐全后，LLM 只生成制图指令和分析覆盖层要求，不重新解释空间边界。
5. Image 2.0 或 SD 只生成研究范围内的覆盖层、符号、箭头、半透明色块和少量标注。
6. 程序按固定顺序合成：固定底图 -> AI 覆盖层 -> 研究范围红线 -> 重点地块边界 -> 固定图框。
7. 导出前检查尺寸、图框、红线、重点地块、范围外像素和图例一致性。

硬性规则：
- 不允许 AI 缩放、旋转、裁切、重绘或改写固定底图。
- 不允许 AI 移动研究范围红线、重点地块边界和图框。
- 不允许 AI 虚构道路、用地分类、热力等级、面积、指标或不存在的数据结论。
- 图纸缺少真实数据时，只能生成示意模板或占位符，不输出伪精确结论。
- 最终成果以程序合成为准，AI 图像模型只承担覆盖层和表现风格。"""


def render_output_flow_prompt_panel(manifest: Optional[Dict] = None, expanded: bool = False) -> str:
    """Render the final-output prompt panel and return the prompt text."""
    manifest = manifest or load_template_asset_manifest()
    rows = get_template_asset_rows(manifest)
    required_rows = [row for row in rows if row["必备"] == "是"]
    required_ready = sum(1 for row in required_rows if row["状态"] == "已上传")
    uploaded_count = sum(1 for row in rows if row["状态"] == "已上传")
    prompt_text = build_output_flow_prompt(manifest)

    with st.expander("最终出图流程提示面板", expanded=expanded):
        render_summary_cards(
            [
                {"value": f"{required_ready}/{len(required_rows)}", "title": "必备资产", "desc": "底图、红线、地块、图框"},
                {"value": f"{uploaded_count}/{len(rows)}", "title": "资产通道", "desc": "可注入 Prompt Compiler"},
                {"value": "锁定合成", "title": "出图模式", "desc": "AI 只生成覆盖层"},
            ]
        )
        if required_ready < len(required_rows):
            st.warning("必备固定资产未齐全。一级精度图纸会停止生成最终 Image 2.0 提示词。")
        else:
            st.success("必备固定资产已齐全。可生成带底图、范围、地块和图框约束的最终提示词。")

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.text_area("可复制的最终出图流程提示词", value=prompt_text, height=360)
        st.download_button(
            "下载流程提示词",
            prompt_text,
            file_name="固定资产出图流程提示词.md",
            mime="text/markdown",
            use_container_width=True,
        )

    return prompt_text


def _format_rows(rows: Iterable[Dict[str, str]]) -> str:
    formatted: List[str] = []
    for row in rows:
        formatted.append(f"- {row['资产']}：{row['状态']}；用途：{row['用途']}")
    return "\n".join(formatted) if formatted else "- 无"
