"""从项目数据自动生成视频配置。

从项目的各个阶段收集数据，生成 HyperFrames 视频所需的 JSON 配置文件。

Usage:
    python scripts/generate_video_data.py
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from src.config import DATA_DIR, SHP_DIR


def load_boundary_info():
    """加载研究范围信息"""
    boundary_path = SHP_DIR / "Boundary_Scope.geojson"
    if boundary_path.exists():
        with open(boundary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        coords = data["features"][0]["geometry"]["coordinates"][0]
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return {
            "min_lng": min(lngs),
            "max_lng": max(lngs),
            "min_lat": min(lats),
            "max_lat": max(lats),
            "center_lng": sum(lngs) / len(lngs),
            "center_lat": sum(lats) / len(lats),
        }
    return None


def load_poi_stats():
    """加载 POI 统计数据"""
    poi_path = DATA_DIR / "Changchun_POI_Real.csv"
    if poi_path.exists():
        df = pd.read_csv(poi_path, encoding="utf-8-sig")
        return {
            "count": len(df),
            "types": df["Name"].value_counts().head(5).to_dict() if "Name" in df.columns else {},
        }
    return {"count": 0, "types": {}}


def load_traffic_stats():
    """加载交通数据统计"""
    traffic_path = DATA_DIR / "Changchun_Traffic_Real.csv"
    if traffic_path.exists():
        df = pd.read_csv(traffic_path, encoding="utf-8-sig")
        return {
            "count": len(df),
            "types": df["Type"].value_counts().to_dict() if "Type" in df.columns else {},
        }
    return {"count": 0, "types": {}}


def load_streetview_stats():
    """加载街景数据统计"""
    streetview_dir = DATA_DIR / "streetview"
    if streetview_dir.exists():
        point_dirs = [d for d in streetview_dir.iterdir() if d.is_dir()]
        return {
            "point_count": len(point_dirs),
            "image_count": len(point_dirs) * 4,  # 每个点 4 张图片
        }
    return {"point_count": 0, "image_count": 0}


def load_building_stats():
    """加载建筑数据统计"""
    buildings_path = SHP_DIR / "Building_Footprints.geojson"
    if buildings_path.exists():
        with open(buildings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        features = data.get("features", [])
        return {"count": len(features)}
    return {"count": 0}


def load_gvi_stats():
    """加载 GVI 数据统计"""
    gvi_path = DATA_DIR / "GVI_Results_Analysis.csv"
    if gvi_path.exists():
        df = pd.read_csv(gvi_path, encoding="utf-8-sig")
        stats = {}
        if "GVI" in df.columns:
            stats["gvi_avg"] = round(df["GVI"].mean(), 2)
            stats["gvi_max"] = round(df["GVI"].max(), 2)
        if "SVF" in df.columns:
            stats["svf_avg"] = round(df["SVF"].mean(), 2)
        return stats
    return {}


def load_nlp_stats():
    """加载 NLP 数据统计"""
    nlp_path = DATA_DIR / "CV_NLP_RawData.csv"
    if nlp_path.exists():
        df = pd.read_csv(nlp_path, encoding="utf-8-sig")
        return {"count": len(df)}
    return {"count": 0}


def load_key_plots():
    """加载重点地块信息"""
    plots_path = SHP_DIR / "Key_Plots_District.json"
    if plots_path.exists():
        with open(plots_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        features = data.get("features", [])
        plots = []
        for f in features:
            props = f.get("properties", {})
            plots.append({
                "id": props.get("id", ""),
                "name": props.get("name", ""),
            })
        return plots
    return []


def generate_stage_data():
    """生成各阶段数据"""
    load_boundary_info()
    poi_stats = load_poi_stats()
    traffic_stats = load_traffic_stats()
    streetview_stats = load_streetview_stats()
    building_stats = load_building_stats()
    gvi_stats = load_gvi_stats()
    nlp_stats = load_nlp_stats()
    key_plots = load_key_plots()

    stages = {
        "stage_01": {
            "title": "任务解读",
            "data": {
                "summary": "研究范围由长春大街、长白路、东九条、亚泰快速路围合，总用地面积约150公顷。核心任务：街区微更新与城市设计。",
                "constraints": [
                    "容积率 ≤ 1.4",
                    "建筑限高 ≤ 24m",
                    "保护伪满皇宫核心保护区",
                    "维持铁路安全退距",
                ],
            },
        },
        "stage_02": {
            "title": "资料收集",
            "data": {
                "building_count": building_stats["count"],
                "poi_count": poi_stats["count"],
                "streetview_count": streetview_stats["point_count"],
                "traffic_count": traffic_stats["count"],
                "nlp_count": nlp_stats["count"],
            },
        },
        "stage_03": {
            "title": "现场调研",
            "data": {
                "sampling_points": streetview_stats["point_count"],
                "total_images": streetview_stats["image_count"],
                "directions": 4,
            },
        },
        "stage_04": {
            "title": "现状分析",
            "data": {
                "gvi_avg": gvi_stats.get("gvi_avg", 0),
                "gvi_max": gvi_stats.get("gvi_max", 0),
                "svf_avg": gvi_stats.get("svf_avg", 0),
                "building_count": building_stats["count"],
            },
        },
        "stage_05": {
            "title": "问题诊断",
            "data": {
                "key_plots_count": len(key_plots),
                "key_plots": [p["name"] for p in key_plots[:5]],
            },
        },
        "stage_06": {
            "title": "目标定位",
            "data": {
                "vision": "数字孪生·古今共振",
                "core_goal": "历史保护与活力再生",
            },
        },
        "stage_07": {
            "title": "设计策略",
            "data": {
                "stakeholders": ["居民", "开发商", "规划师"],
                "strategy_count": 5,
            },
        },
        "stage_08": {
            "title": "总体城市设计",
            "data": {
                "spatial_structure": "一核两轴多片多节点",
                "core": "伪满皇宫文化核心",
                "axes": ["站城活力轴", "工业遗产更新轴"],
            },
        },
        "stage_09": {
            "title": "专项系统设计",
            "data": {
                "systems": [
                    "交通系统",
                    "公共空间系统",
                    "建筑形态控制",
                    "风貌景观",
                ],
            },
        },
        "stage_10": {
            "title": "重点地段深化",
            "data": {
                "plots_count": len(key_plots),
                "plots": [p["name"] for p in key_plots[:5]],
                "plot_types": [
                    "站城门户更新地块",
                    "工业遗产活化地块",
                    "老旧社区微更新地块",
                    "历史风貌协调地块",
                    "文旅活力街巷地块",
                ],
            },
        },
        "stage_11": {
            "title": "实施路径",
            "data": {
                "phases": ["近期微更新", "中期功能置换", "远期整体提升"],
                "strategies": ["留", "改", "拆"],
            },
        },
        "stage_12": {
            "title": "城市设计导则",
            "data": {
                "controls": [
                    "用地管控",
                    "强度管控",
                    "高度管控",
                    "界面管控",
                    "风貌管控",
                    "公共空间管控",
                ],
            },
        },
        "stage_13": {
            "title": "成果表达",
            "data": {
                "deliverables": [
                    "A3图册 (≥60页)",
                    "A1展板 (≥3张)",
                    "规划文本",
                    "PPT汇报",
                ],
            },
        },
    }

    return stages


def generate_narrator_marks():
    """生成旁白时间标记"""
    return [
        {"time": "00:00", "name": "开场", "narration": "数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计"},
        {"time": "00:15", "name": "01 任务解读", "narration": "任务解读：梳理任务书红线限制，建立初始认知框架"},
        {"time": "00:45", "name": "02 资料收集", "narration": "资料收集：多源数据汇聚，建立数据中台"},
        {"time": "01:15", "name": "03 现场调研", "narration": "现场调研：实地踏勘，记录街道空间与环境问题"},
        {"time": "01:55", "name": "04 现状分析", "narration": "现状分析：3D全息数据底座，多层叠加展示空间现状"},
        {"time": "02:45", "name": "05 问题诊断", "narration": "问题诊断：MPI更新潜力排行与地块诊断雷达"},
        {"time": "03:35", "name": "06 目标定位", "narration": "目标定位：数字孪生·古今共振设计理念"},
        {"time": "04:10", "name": "07 设计策略", "narration": "设计策略：三主体博弈与多主体共识"},
        {"time": "05:00", "name": "08 总体城市设计", "narration": "总体城市设计：总平面图与空间结构推演"},
        {"time": "05:50", "name": "09 专项系统设计", "narration": "专项系统设计：道路交通、慢行系统、公共空间、绿地景观"},
        {"time": "06:35", "name": "10 重点地段深化", "narration": "重点地段深化：5个重点地块的AIGC效果图与Before/After对比"},
        {"time": "07:25", "name": "11 实施路径", "narration": "实施路径：近期微更新、中期功能置换、远期整体提升"},
        {"time": "07:55", "name": "12 城市设计导则", "narration": "城市设计导则：地块控制图则与街道断面设计"},
        {"time": "08:25", "name": "13 成果表达", "narration": "成果表达：核心指标汇总与3D全息方案回顾"},
    ]


def main():
    print("=" * 60)
    print("生成视频配置数据")
    print("=" * 60)

    # 加载项目信息
    load_boundary_info()
    poi_stats = load_poi_stats()
    streetview_stats = load_streetview_stats()

    # 生成项目数据
    project_data = {
        "project": {
            "name": "数字孪生·古今共振",
            "subtitle": "AI赋能下的伪满皇宫周边街区更新规划设计",
            "location": "中国吉林省长春市宽城区",
            "area": "约150公顷",
        },
        "stats": {
            "boundary_ha": 150,
            "poi_count": poi_stats["count"],
            "streetview_points": streetview_stats["point_count"],
            "streetview_images": streetview_stats["image_count"],
        },
        "stages": {},
        "narrator_marks": generate_narrator_marks(),
    }

    # 生成各阶段数据
    stages = generate_stage_data()

    # 保存项目数据
    output_dir = ROOT_DIR / "tools" / "video_generator" / "composer" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    project_data_path = output_dir / "project_data.json"
    with open(project_data_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
    print(f"项目数据已保存: {project_data_path}")

    # 保存各阶段数据
    stages_dir = output_dir / "stages"
    stages_dir.mkdir(parents=True, exist_ok=True)

    for stage_id, stage_data in stages.items():
        stage_path = stages_dir / f"{stage_id}.json"
        with open(stage_path, "w", encoding="utf-8") as f:
            json.dump(stage_data, f, ensure_ascii=False, indent=2)
        print(f"阶段数据已保存: {stage_path}")

    print("\n" + "=" * 60)
    print("数据生成完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
