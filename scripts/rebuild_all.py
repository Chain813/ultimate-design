"""一键重新编译研究报告(Word)与演示幻灯(PowerPoint)的整合脚本。

使用规范的动态项目相对路径，解耦个人开发机绝对路径与历史临时目录。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Canonical paths from config
from src.config.paths import ROOT_DIR, STATIC_DIR

TEMP_IMG_DIR = ROOT_DIR / "output" / "temp_images"
STATIC_IMG_DIR = STATIC_DIR
SCREENSHOTS_DIR = ROOT_DIR / "assets" / "screenshots"
python_exe = sys.executable

print("=== 0. 生成技术图表与知识图谱 ===")

diagram_scripts = [
    "tools/generate_unified_landscape.py",
    "tools/generate_technology_parameters_graph.py",
    "tools/generate_technical_route.py",
    "tools/generate_all_diagrams.py"
]

for script in diagram_scripts:
    script_path = ROOT_DIR / script
    if not script_path.exists():
        print(f" ⚠️ 跳过不存在的图表脚本: {script}")
        continue

    print(f" -> 正在运行: {script}")
    res = subprocess.run(
        [python_exe, str(script_path)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if res.returncode != 0:
        print(f"❌ {script} 运行失败！错误信息：")
        print(res.stderr)
    else:
        print(f"✅ {script} 运行成功！")

print("\n=== 1. 整理与备份全部图片资源 ===")
TEMP_IMG_DIR.mkdir(parents=True, exist_ok=True)

# 映射配置
copy_jobs = [
    # 原始规划图纸
    ("atlas/DR-004_现状区位图.png", "fig_004.png"),
    ("atlas/DR-043_道路交通系统规划图.png", "fig_051.png"),
    ("atlas/DR-013_建筑高度现状图.png", "fig_017.png"),

    # 5张核心思维导图/流程图 (同时输出给 Word 和 PPT 的占位符)
    ("system_architecture_mindmap.png", "system_architecture_mindmap.png"),
    ("system_architecture_mindmap.png", "system_architecture.png"),

    ("workflow_flowchart.png", "workflow_flowchart.png"),
    ("technical_route_mindmap.png", "negotiation_workflow.png"),

    ("urban_rural_planning_mindmap.png", "urban_rural_planning_mindmap.png"),
    ("urban_rural_planning_mindmap.png", "compliance_audit_flow.png"),

    ("data_pipeline_mindmap.png", "data_pipeline_mindmap.png"),
    ("data_pipeline_mindmap.png", "fig_plotly.png"),

    ("unified_landscape_mindmap.png", "unified_landscape_mindmap.png"),
    ("03_digital_twin.png", "fig_3d.png"),

    # 智能体/合规/AIGC对齐及技术参数图表
    ("agent_negotiation_flowchart.png", "agent_negotiation_flowchart.png"),
    ("rag_compliance_flowchart.png", "rag_compliance_flowchart.png"),
    ("sd_controlnet_flowchart.png", "sd_controlnet_flowchart.png"),
    ("technology_parameters_knowledge_graph.png", "technology_parameters_knowledge_graph.png"),
]

for src_rel, dest_name in copy_jobs:
    src_path = STATIC_IMG_DIR / src_rel
    dest_path = TEMP_IMG_DIR / dest_name
    if src_path.exists():
        shutil.copy(str(src_path), str(dest_path))
        print(f" -> 复制成功: {src_rel} -> {dest_name}")
    else:
        print(f" ⚠️ 提示：未找到源文件 {src_path.name}，跳过")

# 可选截图同步（如存在）
if SCREENSHOTS_DIR.exists():
    for f in SCREENSHOTS_DIR.glob("*.png"):
        dest_path = TEMP_IMG_DIR / f.name
        shutil.copy(str(f), str(dest_path))
        print(f" -> 同步截图: {f.name}")

print("\n=== 2. 编译并输出 成果图册汇总_A3.pptx ===")
ppt_script = ROOT_DIR / "tools" / "generate_atlas_ppt.py"
if ppt_script.exists():
    res_ppt = subprocess.run(
        [python_exe, str(ppt_script)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    print(res_ppt.stdout)
    if res_ppt.returncode != 0:
        print("❌ PPT 编译失败！错误信息：")
        print(res_ppt.stderr)
    else:
        print("✅ PPT 编译成功！")
else:
    print(f"❌ 未找到 PPT 编译脚本: {ppt_script}")

print("\n=== 3. 编译并输出 项目设计报告.docx ===")
report_script = ROOT_DIR / "scripts" / "generate_report.py"
if report_script.exists():
    res_docx = subprocess.run(
        [python_exe, str(report_script)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    print(res_docx.stdout)
    if res_docx.returncode != 0:
        print("❌ Word 报告编译失败！错误信息：")
        print(res_docx.stderr)
    else:
        print("✅ Word 报告编译成功！")
else:
    print(f"❌ 未找到报告编译脚本: {report_script}")

print("\n=== 全部生成任务已完成！ ===")
