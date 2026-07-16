"""一键重新编译研究报告(Word)与演示幻灯(PowerPoint)的整合脚本"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

TEMP_IMG_DIR = Path(os.path.expanduser("~")) / "Desktop" / "城环杯" / "temp_images"
STATIC_IMG_DIR = Path(r"e:\AI-based-project\urban-platform\static")
BRAIN_PREV_DIR = Path(os.path.expanduser("~")) / ".gemini" / "antigravity" / "brain" / "a7a0a585-8fe2-47a0-8b18-0be8b3147e91"
python_exe = sys.executable

print("=== 0. 生成技术图表与知识图谱 ===")

diagram_scripts = [
    "tools/generate_unified_landscape.py",
    "tools/generate_technology_parameters_graph.py",
    "tools/generate_technical_route.py",
    "tools/generate_all_diagrams.py"
]

for script in diagram_scripts:
    print(f" -> 正在运行: {script}")
    res = subprocess.run([python_exe, script], capture_output=True, text=True, encoding='utf-8')
    if res.returncode != 0:
        print(f"❌ {script} 运行失败！错误信息：")
        print(res.stderr)
    else:
        print(f"✅ {script} 运行成功！")

print("\n=== 1. 整理与备份全部图片资源 ===")
os.makedirs(str(TEMP_IMG_DIR), exist_ok=True)

# 映射配置
copy_jobs = [
    # 原始规划图纸
    ("atlas/DR-004_现状区位图.png", "fig_004.png"),
    ("atlas/DR-051_道路交通系统规划图.png", "fig_051.png"),
    ("atlas/DR-017_建筑高度现状图.png", "fig_017.png"),
    
    # 5张核心思维导图/流程图 (同时输出给 Word 和 PPT 的占位符)
    ("system_architecture_mindmap.png", "system_architecture_mindmap.png"),
    ("system_architecture_mindmap.png", "system_architecture.png"), # PPT 匹配名称
    
    ("workflow_flowchart.png", "workflow_flowchart.png"),
    ("technical_route_mindmap.png", "negotiation_workflow.png"), # PPT 匹配名称
    
    ("urban_rural_planning_mindmap.png", "urban_rural_planning_mindmap.png"),
    ("urban_rural_planning_mindmap.png", "compliance_audit_flow.png"), # PPT 匹配名称
    
    ("data_pipeline_mindmap.png", "data_pipeline_mindmap.png"),
    ("data_pipeline_mindmap.png", "fig_plotly.png"), # PPT 匹配名称
    
    ("unified_landscape_mindmap.png", "unified_landscape_mindmap.png"),
    ("03_digital_twin.png", "fig_3d.png"),

    # 新增的4个智能体/合规/AIGC对齐及技术参数图表
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
        print(f" ⚠️ 警告：未找到源文件 {src_path}")

# 从大模型 brain 文件夹中提取交互截图
screenshots = [
    ("stage07_radar_chart_1779851862153.png", "fig_radar.png"),
    ("stage12_gis_compliance_1779851923612.png", "fig_compliance.png"),
]

for src_name, dest_name in screenshots:
    src_path = BRAIN_PREV_DIR / src_name
    dest_path = TEMP_IMG_DIR / dest_name
    if src_path.exists():
        shutil.copy(str(src_path), str(dest_path))
        print(f" -> 复制成功: {src_name} -> {dest_name}")
    else:
        print(f" ⚠️ 警告：未找到历史截图 {src_name}")

python_exe = sys.executable

print("\n=== 2. 编译并输出 附件4 成果演示幻灯.pptx ===")
res_ppt = subprocess.run([python_exe, "tools/generate_pptx_slides.py"], capture_output=True, text=True, encoding='utf-8')
print(res_ppt.stdout)
if res_ppt.returncode != 0:
    print("❌ PPT 编译失败！错误信息：")
    print(res_ppt.stderr)
else:
    print("✅ PPT 编译成功！")

print("\n=== 3. 编译并输出 附件3 成果研究报告.docx ===")
res_docx = subprocess.run([python_exe, "scripts/build_final_report_strict_v3.py"], capture_output=True, text=True, encoding='utf-8')
print(res_docx.stdout)
if res_docx.returncode != 0:
    print("❌ Word 报告编译失败！错误信息：")
    print(res_docx.stderr)
else:
    print("✅ Word 报告编译成功！")

print("\n=== 全部生成任务已完成！ ===")
