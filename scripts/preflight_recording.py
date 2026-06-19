#!/usr/bin/env python
"""录屏前环境检查脚本。

在启动 OBS 录制前运行此脚本，确保：
1. Streamlit 平台可访问
2. 核心数据资产就绪
3. 静态资源完整（atlas图纸、架构图等）
4. OBS 推荐配置提示

Usage:
    python scripts/preflight_recording.py
    python scripts/preflight_recording.py --verbose
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── 检查项 ──

def check_streamlit_port():
    """检查 Streamlit 默认端口 8501"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', 8501))
        s.close()
        return result == 0
    except Exception:
        return False


def check_data_assets():
    """检查核心数据资产"""
    from src.config import DATA_DIR

    checks = {}
    # GIS 数据
    gis_files = {
        "研究范围红线": "Boundary_Scope.geojson",
        "建筑基底": "Building_Footprints.geojson",
        "用地分类": "landuse_clipped.geojson",
        "道路网络": "road_clipped.geojson",
        "重点地块": "Key_Plots_District.json",
    }
    gis_dir = DATA_DIR / "gis"
    for label, fname in gis_files.items():
        path = gis_dir / fname
        checks[f"GIS/{label}"] = path.exists()

    # CSV 数据
    csv_files = {
        "POI数据": "Changchun_POI_Real.csv",
        "交通设施": "Changchun_Traffic_Real.csv",
        "GVI指标": "GVI_Results_Analysis.csv",
        "NLP舆情": "CV_NLP_RawData.csv",
        "建筑年代": "Building_Years.csv",
        "房价数据": "House_Prices.csv",
        "交通流量": "Traffic_Flow.csv",
    }
    csv_dir = DATA_DIR / "csv"
    for label, fname in csv_files.items():
        path = csv_dir / fname
        checks[f"CSV/{label}"] = path.exists()

    # 街景数据
    streetview_dir = DATA_DIR / "streetview"
    if streetview_dir.exists():
        points = [d for d in streetview_dir.iterdir() if d.is_dir()]
        checks["街景采样点"] = len(points) > 0
        checks["街景采样点数量"] = len(points)

    # RAG 知识库
    rag_path = DATA_DIR / "rag_knowledge.json"
    checks["RAG/政策知识库"] = rag_path.exists()

    return checks


def check_static_assets():
    """检查静态资源（atlas图纸、架构图等）"""
    static_dir = ROOT / "static"
    checks = {}

    # 关键架构图
    key_diagrams = [
        "system_architecture_mindmap.png",
        "technical_route_diagram.png",
        "workflow_flowchart.png",
        "sd_controlnet_flowchart.png",
        "agent_negotiation_flowchart.png",
        "rag_compliance_flowchart.png",
        "research_scope_2d_cropped.png",
    ]
    for fname in key_diagrams:
        path = static_dir / fname
        checks[f"架构图/{fname}"] = path.exists()

    # Atlas 图纸数量
    atlas_dir = static_dir / "atlas"
    if atlas_dir.exists():
        atlas_files = list(atlas_dir.glob("DR-*.png"))
        checks["Atlas图纸总数"] = len(atlas_files)
        # 关键图纸
        key_atlas = [
            "DR-001_规划设计图册封面.png",
            "DR-005_研究范围图.png",
            "DR-024_MPI更新潜力评估图.png",
            "DR-036_空间结构规划图.png",
            "DR-037_用地规划图.png",
            "DR-057_公众参与与博弈协商成果图.png",
            "DR-059_AIGC技术推演过程图.png",
            "DR-060_实施分期图.png",
        ]
        for fname in key_atlas:
            path = atlas_dir / fname
            checks[f"Atlas/{fname}"] = path.exists()

    return checks


def check_env_config():
    """检查环境配置"""
    checks = {}
    env_path = ROOT / ".env"
    checks[".env 文件"] = env_path.exists()

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
        checks["DEEPSEEK_API_KEY"] = "DEEPSEEK_API_KEY" in content

    config_path = ROOT / "config" / "config.yaml"
    checks["config.yaml"] = config_path.exists()

    return checks


def check_pages():
    """检查页面文件完整性"""
    pages_dir = ROOT / "pages"
    expected_pages = [
        "00_数据准备与任务解读.py",
        "02_资料收集与现场调研.py",
        "04_现状分析与问题诊断.py",
        "06_目标定位.py",
        "07_设计策略.py",
        "08_总体城市设计.py",
        "09_专项系统设计.py",
        "10_重点地段深化.py",
        "11_实施路径.py",
        "12_城市设计导则.py",
        "13_成果表达.py",
        "15_AIGC设计推演.py",
        "16_制图与设计智能体Skill手册.py",
    ]
    checks = {}
    for page in expected_pages:
        path = pages_dir / page
        checks[f"页面/{page}"] = path.exists()
    return checks


def estimate_video_size():
    """估算录像文件大小"""
    # CQP 15, 2560x1440, 60fps, 约10分钟
    # 经验值：约 500-800 MB
    return "预估 500-800 MB（CQP 15, 1440p, 60fps, 10分钟）"


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("=" * 66)
    print("  🎬 UltimateDESIGN 答辩录屏 - 环境就绪检查")
    print("=" * 66)
    print()

    all_ok = True

    # 1. Streamlit 端口
    print("─" * 50)
    print("1. Streamlit 服务检查")
    port_ok = check_streamlit_port()
    status = "✅ 就绪 (port 8501)" if port_ok else "❌ 未启动"
    if not port_ok:
        all_ok = False
        status += " — 请运行: streamlit run app.py"
    print(f"   {status}")

    # 2. 数据资产
    print("\n─" * 50)
    print("2. 核心数据资产")
    data_checks = check_data_assets()
    for name, ok in data_checks.items():
        if isinstance(ok, bool):
            if ok:
                print(f"   ✅ {name}")
            else:
                all_ok = False
                print(f"   ❌ {name} — 缺失")
        elif isinstance(ok, int):
            print(f"   📊 {name}: {ok}")

    # 3. 静态资源
    print("\n─" * 50)
    print("3. 静态资源（图纸 & 架构图）")
    static_checks = check_static_assets()
    for name, ok in static_checks.items():
        if isinstance(ok, bool):
            if ok:
                print(f"   ✅ {name}")
            else:
                all_ok = False
                print(f"   ⚠️  {name} — 缺失（不影响核心演示）")
        elif isinstance(ok, int):
            print(f"   📊 {name}: {ok} 张")

    # 4. 环境配置
    print("\n─" * 50)
    print("4. 环境配置")
    env_checks = check_env_config()
    for name, ok in env_checks.items():
        if ok:
            print(f"   ✅ {name}")
        else:
            print(f"   ⚠️  {name} — 缺失（演示模式可忽略）")

    # 5. 页面文件
    print("\n─" * 50)
    print("5. 页面文件完整性")
    page_checks = check_pages()
    for name, ok in page_checks.items():
        if ok:
            if verbose:
                print(f"   ✅ {name}")
        else:
            all_ok = False
            print(f"   ❌ {name} — 缺失！")

    if not verbose:
        page_ok = all(page_checks.values())
        print(f"   {'✅' if page_ok else '❌'} 页面文件: {sum(page_checks.values())}/{len(page_checks)} 就绪")

    # 6. 估算
    print("\n─" * 50)
    print("6. 录像文件估算")
    print(f"   💾 {estimate_video_size()}")

    # ── OBS 配置提示 ──
    print("\n" + "=" * 66)
    print("  🛠️  OBS 关键配置提醒")
    print("=" * 66)
    print("""
   设置 → 高级 → 视频:
      ✅ 色彩格式: I444 (不是 NV12！)
      ✅ 色彩空间: Rec. 709
      ✅ 色彩范围: 全部 (Full)

   设置 → 视频:
      ✅ 基础分辨率 = 输出分辨率 (1:1 像素)
      ✅ FPS: 60

   设置 → 输出 → 录像:
      ✅ 编码器: NVIDIA NVENC H.264
      ✅ 速率控制: CQP, CQ Level = 15
      ✅ 预设: P6: Slower
      ✅ 调优: High Quality

   采集源:
      ✅ 窗口采集 (不要用显示器采集！)
      ✅ 方法: Windows 图形采集 (WGC)
""")

    # ── 总结 ──
    print("=" * 66)
    if all_ok:
        print("  ✅ 全部就绪！可以开始录制。")
        print()
        print("  操作流程:")
        print("  1. 浏览器打开 http://localhost:8501")
        print("  2. F11 全屏 → 侧边栏开启演示模式 → 收起侧边栏")
        print("  3. 按 H 隐藏所有 HUD")
        print("  4. OBS 开始录制")
        print("  5. 按 T 启动自动导览")
        print("  6. 录制完成后 OBS 停止 → 复用转 MP4")
    else:
        print("  ⚠️  部分检查未通过，请先修复上述 ❌ 项。")
        print("  （⚠️ 标记的项可忽略，演示模式仍可运行）")
    print("=" * 66)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
