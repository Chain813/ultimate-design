"""跨阶段数据总线 —— 统一管理 13 阶段之间的数据传递。

所有阶段产出均存放在 ``st.session_state["stage_bus"]`` 字典中，
键名格式为 ``"{stage_code}_{key}"``。
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import streamlit as st

from src.config.runtime import resolve_path

logger = logging.getLogger("ultimateDESIGN")

# Debounce: track last-written hash to avoid redundant disk writes
_last_written_hash: str = ""


def _get_cache_path() -> Path:
    cache_path = resolve_path("output/stage_bus_cache.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    return cache_path


import time

_last_written_time: float = 0.0

# ═══════════════════════════════════════════════════════════════════
# 长春伪满皇宫基准预置数据（防崩溃与防御性降级底座）
# ═══════════════════════════════════════════════════════════════════
BASELINE_STAGE_DATA = {
    # ── Stage 04 & 05: 现状分析与问题诊断 ──
    "04_target_plot": {
        "name": "长春水产大市场",
        "mpi": 88.5,
        "priority": "P1 优先更新",
        "issues": [
            "冷链外迁导致低效闲置",
            "周边天际线杂乱与文脉割裂",
            "缺乏滨水公共开放空间"
        ]
    },
    "05_target_plot": {
        "name": "长春水产大市场",
        "mpi": 88.5,
        "priority": "P1 优先更新",
        "issues": [
            "冷链外迁导致低效闲置",
            "周边天际线杂乱与文脉割裂",
            "缺乏滨水公共开放空间"
        ]
    },
    "04_poi_count": 342,
    "04_building_count": 719,
    "04_avg_height": 11.2,
    "05_top_plot": "长春水产大市场",
    "05_top_score": 88.5,
    "05_mpi_ranking": [
        {"地块名称": "长春水产大市场", "MPI 得分": 88.5, "空间潜力原分": 0.92, "社会需求原分": 0.95, "环境现状评分": 0.28},
        {"地块名称": "中车老厂区", "MPI 得分": 84.2, "空间潜力原分": 0.89, "社会需求原分": 0.90, "环境现状评分": 0.35},
        {"地块名称": "光复路历史街区", "MPI 得分": 81.6, "空间潜力原分": 0.85, "社会需求原分": 0.88, "环境现状评分": 0.42},
    ],
    "05_diagnosis_report": (
        "【长春铁北片区微更新前期量化诊断】\n"
        "1. 靶向地块锁定：长春水产大市场地块（MPI: 88.5，紧迫度 P1 优先更新）。\n"
        "2. 核心问题诊断：\n"
        "   - 冷链物流外迁导致大跨度交易厅与仓储设施低效闲置，存在用地混杂与环境衰退；\n"
        "   - 周边天际线杂乱，破旧自建房与临时搭建物突兀，严重割裂与伪满皇宫的视廊文脉；\n"
        "   - 沿伊通河缺乏滨水公共开放空间，封闭围墙阻隔导致社区慢行无法渗透；\n"
        "   - 社区老龄化率达30%，缺少适老健身公园、日照充足的休憩场地及便民医疗配套。"
    ),
    "04_diagnosis_report": (
        "【长春铁北片区微更新前期量化诊断】\n"
        "1. 靶向地块锁定：长春水产大市场地块（MPI: 88.5，紧迫度 P1 优先更新）。\n"
        "2. 核心问题诊断：冷链外迁低效闲置、周边天际线杂乱与文脉割裂、缺乏滨水开放空间。"
    ),
    # ── Stage 06: 目标定位 ──
    "06_design_concept": (
        "数字孪生·古今共振——AI赋能下的长春伪满皇宫周边街区更新规划设计。\n"
        "以伪满皇宫国家5A级文博IP为引领，聚焦长春水产大市场与中车老厂区两大触媒节点，"
        "通过'织补肌理、活化业态、贯通慢行、缝合城铁'，打造兼具历史底蕴与创新活力的城市文旅客厅。"
    ),
    # ── Stage 07: 设计策略 ──
    "07_target_plot": {
        "name": "长春水产大市场",
        "mpi": 88.5,
        "priority": "P1 优先更新",
        "issues": [
            "冷链外迁导致低效闲置",
            "周边天际线杂乱与文脉割裂",
            "缺乏滨水公共开放空间"
        ]
    },
    "07_strategy_matrix": (
        "| 策略方向 | 具体举措 | 政策依据 | 空间落位 | 资金逻辑 | 协同度 |\n"
        "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        "| 文脉保护与风貌织补 | 严格控制限高≤9-18m，延续近代红灰砖基调，保留大跨度工业桁架 | 《长春市历史文化名城保护条例》 | 伪满皇宫风貌区及水产大市场 | 文保专项资金引导 | 95% |\n"
        "| 滨水客厅与业态活化 | 置换低效仓储为新中式滨水文旅客厅、文创街区与特色餐饮 | 《城市更新行动指导意见》 | 长春水产大市场地块 | 社会文旅资本导入 | 92% |\n"
        "| 生态绿廊与民生反哺 | 贯通伊通河滨水步道，配置口袋公园，配建适老医疗与生鲜便民服务 | 《完整居住社区建设标准》 | 沿伊通河及周边老旧社区 | 商业溢价反哺公共设施 | 90% |"
    ),
    "07_design_brief": (
        "## 靶向地块定位与更新指引\n"
        "- 靶向地块：长春水产大市场（MPI: 88.5，P1 优先更新）\n"
        "- 更新定位：新中式滨水文旅客厅与工业遗存活化\n"
        "- 容积率控制：核心区≤1.4，建筑密度≤35%，绿地率≥25%\n"
        "- 建筑风貌控制：限高9-18m，红砖与暖灰基调，保留大跨度工业桁架，人车分流生态绿廊\n\n"
        "## 核心问题与博弈共识\n"
        "- 居民诉求：解决冷链闲置异味与设施老化，争取滨水漫步绿廊与便民菜市场配套\n"
        "- 运营商诉求：导入文旅商业与沉浸式体验空间，保障投资回报率\n"
        "- 规划师底线：严守伪满皇宫视廊保护与限高刚性红线，容积率严格控制在1.4以内\n\n"
        "## 空间策略与 AIGC 控制关键词\n"
        "- 核心控制词：新中式滨水文旅客厅、保留大跨度工业桁架、红砖与暖灰基调、人车分流生态绿廊\n"
        "- 空间结构：一核两轴多片多节点，站城联动与山水连城"
    ),
    "07_voting_scores": {
        "👥 居民与使用群体代表": 85.0,
        "💰 投资与运营开发主体": 82.0,
        "📐 规划设计与法定义务人": 90.0,
        "👥 居民代表（老王）": 85.0,
        "💰 文旅运营商（赵总）": 82.0,
        "📐 规划师（李工）": 90.0
    },
    # ── Stage 08: 总体城市设计 ──
    "08_spatial_structure": (
        "【总体空间结构规划：一核两轴多片多节点】\n"
        "1. 一核：伪满皇宫历史文化共振核心。\n"
        "2. 两轴：长春站-伪满皇宫站城联动轴、伊通河滨水生态活力轴。\n"
        "3. 多片：历史保护核心片区、滨水文创示范片区（水产大市场地块）、老旧居住更新片区、TOD现代商务片区。\n"
        "4. 多节点：水产大市场文旅客厅、中车工业记忆广场、光复路文创门户节点。"
    ),
    "08_landuse_sandbox": {
        "scenario": "居住 45%, 商业 20%, 办公 8%, 绿地 15%, 公共设施 7%, 其他 5%",
        "res_pct": 45, "com_pct": 20, "off_pct": 8, "green_pct": 15, "public_pct": 7, "remain": 5,
        "evaluation": "该方案大幅补足了绿地率缺口（由 2.9% 提升至 15% 以上），提升了商业服务业占比，契合文旅客厅发展定位。"
    },
    # ── Stage 09: 专项系统 ──
    "09_traffic_system": "小街区密路网，长春站至伪满皇宫人车分流漫游大环线，打通京哈铁路慢行割裂点。",
    "09_public_space": "滨水生态绿道贯通，沿伊通河配置连续景观慢行道与6处社区口袋公园，实现300米见绿。",
    "09_building_form": "延续近代长春红灰砖立面与折衷主义风貌，保留大跨度工业厂房桁架，核心区限高9m，一般区限高18m。",
    "09_landscape_style": "新中式与近代风貌有机融合，暖色调铺装与原生树种绿化配置。",
    # ── Stage 10: 重点地块深化 ──
    "10_plot_metrics_长春水产大市场": (
        "【长春水产大市场控规详细指标建议】\n"
        "- 用地性质：商业/文创/公园绿地混合用地 (B1/B4/G1)\n"
        "- 容积率 (FAR)：1.35 (≤ 1.4)\n"
        "- 建筑密度：32.0% (≤ 35.0%)\n"
        "- 绿地率：28.5% (≥ 25.0%)\n"
        "- 建筑限高：核心区9.0m，局部一般区18.0m\n"
        "- 保留要素：原大跨度工业桁架结构与红砖山墙"
    ),
    "10_plot_personas_长春水产大市场": (
        "【长春水产大市场目标人群画像】\n"
        "1. 老城原住民老张（68岁，退休居民）：渴望干净卫生的生鲜菜市与滨水晨练绿道；\n"
        "2. 文创创客小林（28岁，设计师）：期待大跨度厂房改造的共享工作室与咖啡沙龙；\n"
        "3. 文化游客小周（24岁，研学青年）：期盼沉浸式伪满文脉与滨水打卡空间。"
    ),
    "10_plot_design_长春水产大市场": (
        "【长春水产大市场地块深化设计方案】\n"
        "一、定位：新中式滨水文旅客厅与工业遗存活化示范地块。\n"
        "二、空间布局：拆除破旧临时建筑，保留原交易大厅大跨度钢木桁架；植入新中式坡顶玻璃盒子；\n"
        "三、滨水界面：打开伊通河滨水慢行步道，设置连续挑台与亲水阶梯；\n"
        "四、业态策划：一层为新中式生鲜便民市集与文创零售，二层为青年创客工坊与特色茶咖；\n"
        "五、风貌控制：红砖与暖灰基调，人车分流生态绿廊。"
    ),
    # ── Stage 11: 实施路径 ──
    "11_region_phasing": (
        "【实施分期计划】\n"
        "1. 近期（1-2年）：率先启动长春水产大市场地块微更新与伊通河滨水绿道贯通工程；\n"
        "2. 中期（3-5年）：推进中车老厂区工业遗存活化与光复路街区风貌整治；\n"
        "3. 远期（5-8年）：全面完成铁北片区微循环缝合与全域智慧社区治理。"
    ),
    # ── Stage 12: 设计导则 ──
    "12_design_guideline": (
        "# 伪满皇宫周边街区更新规划设计·城市设计法定导则\n\n"
        "## 第一章 总则\n"
        "本导则适用于长春市宽城区伪满皇宫周边约160公顷街区更新。坚持保护优先、文脉共振、生态修复。\n\n"
        "## 第二章 靶向地块管控\n"
        "靶向地块【长春水产大市场】容积率严格控制在1.4以内，建筑密度≤35%，建筑限高9-18m，保留工业桁架，打造新中式滨水文旅客厅。"
    )
}


def _save_cache_to_disk(bus_dict: dict):
    global _last_written_hash, _last_written_time
    try:
        now = time.time()
        # Throttling: at most 1 write per second
        if now - _last_written_time < 1.0:
            return
            
        # Clean dict to ensure only JSON-serializable objects are passed
        def _sanitize_for_json(obj, visited=None):
            if visited is None:
                visited = set()

            if isinstance(obj, (str, int, float, bool)) or obj is None:
                return obj

            # Prevent circular references
            obj_id = id(obj)
            if obj_id in visited:
                return "[CircularReference]"

            # PIL.Image representation
            if hasattr(obj, "save") and hasattr(obj, "size"):
                return f"[PIL.Image: {obj.size[0]}x{obj.size[1]}]"

            # GeoDataFrame / DataFrame
            if hasattr(obj, "to_dict") and hasattr(obj, "columns"):
                try:
                    return {
                        "_type": obj.__class__.__name__,
                        "rows": len(obj),
                        "columns": [str(c) for c in obj.columns],
                        "sample": obj.head(2).to_dict(orient="records") if len(obj) > 0 else []
                    }
                except Exception:
                    return f"[{obj.__class__.__name__}: {len(obj)} rows]"

            # Series / numpy array
            if hasattr(obj, "tolist") and callable(obj.tolist):
                try:
                    visited.add(obj_id)
                    res = _sanitize_for_json(obj.tolist(), visited)
                    visited.remove(obj_id)
                    return res
                except Exception:
                    return str(obj)

            # Numpy scalar
            if hasattr(obj, "item") and callable(obj.item):
                try:
                    return obj.item()
                except Exception:
                    pass

            # Path
            if isinstance(obj, Path):
                return str(obj)

            if isinstance(obj, dict):
                visited.add(obj_id)
                res = {str(k): _sanitize_for_json(v, visited) for k, v in obj.items()}
                visited.remove(obj_id)
                return res

            if isinstance(obj, (list, tuple, set)):
                visited.add(obj_id)
                res = [_sanitize_for_json(i, visited) for i in obj]
                visited.remove(obj_id)
                return res

            try:
                json.dumps(obj)
                return obj
            except Exception:
                return str(obj)

        safe_bus = _sanitize_for_json(bus_dict)

        # Debounce: skip write if content hasn't changed
        content_hash = hashlib.md5(json.dumps(safe_bus, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if content_hash == _last_written_hash:
            return
            
        cache_path = _get_cache_path()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(safe_bus, f, ensure_ascii=False, indent=2)
            
        _last_written_hash = content_hash
        _last_written_time = now
    except Exception as e:
        logger.error(f"Failed to write stage data bus cache: {e}")


def _load_cache_from_disk() -> dict:
    try:
        cache_path = _get_cache_path()
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception as e:
        logger.warning(f"Failed to load stage data bus cache from disk: {e}")
    return {}


def _bus() -> dict:
    if "stage_bus" not in st.session_state:
        st.session_state["stage_bus"] = _load_cache_from_disk()
    return st.session_state["stage_bus"]


def save_stage_output(stage_code: str, key: str, data):
    """将本阶段的产出存入总线，供下游阶段读取。"""
    bus_dict = _bus()
    bus_dict[f"{stage_code}_{key}"] = data
    _save_cache_to_disk(bus_dict)


def _is_meaningful(val) -> bool:
    """Safe check for whether val has non-empty content without raising DataFrame truthiness errors."""
    if val is None:
        return False
    if hasattr(val, "empty"):  # pandas DataFrame, GeoDataFrame, Series
        return not bool(val.empty)
    if isinstance(val, (str, list, dict, set, tuple)):
        return len(val) > 0
    return True


def _get_adaptive_baseline_value(full_key: str):
    """根据当前激活的场地上下文动态生成/修饰基准兜底数据，杜绝全平台写死长春/水产/老王。"""
    try:
        from src.config.site import get_site_config, get_site_city, get_site_name, get_landmarks
        s_cfg = get_site_config()
        s_city = get_site_city() or s_cfg.get("city", "当地") or "当地"
        s_name = get_site_name() or s_cfg.get("name", "更新规划单元") or "更新规划单元"
        s_area = s_cfg.get("area_ha", 160)
        landmarks = get_landmarks()
        primary_lm = landmarks[0].get("name") if (landmarks and isinstance(landmarks[0], dict) and landmarks[0].get("name")) else f"{s_name}核心风貌节点"

        custom_plot = None
        raw_val = BASELINE_STAGE_DATA.get(full_key)
        if raw_val is None:
            # Check prefix matching for Stage 10 plot dynamic keys
            if full_key.startswith("10_plot_metrics_"):
                raw_val = BASELINE_STAGE_DATA.get("10_plot_metrics_长春水产大市场")
                custom_plot = full_key[len("10_plot_metrics_"):]
            elif full_key.startswith("10_plot_personas_"):
                raw_val = BASELINE_STAGE_DATA.get("10_plot_personas_长春水产大市场")
                custom_plot = full_key[len("10_plot_personas_"):]
            elif full_key.startswith("10_plot_design_"):
                raw_val = BASELINE_STAGE_DATA.get("10_plot_design_长春水产大市场")
                custom_plot = full_key[len("10_plot_design_"):]
            else:
                return None

        # 检查是否为默认的长春基准配置
        is_changchun_default = "伪满" in s_name or "长春" in s_city
        if is_changchun_default and not custom_plot:
            return raw_val

        target_name = custom_plot if custom_plot else f"{s_name}重点更新单元"

        # 对非长春自定义场地，进行动态上下文自适应适配
        if isinstance(raw_val, dict):
            if full_key.endswith("target_plot"):
                return {
                    "name": target_name,
                    "mpi": 88.5,
                    "priority": "P1 优先更新",
                    "issues": [
                        "存量功能低效利用与空间衰退",
                        "周边天际线杂乱与文脉界面割裂",
                        "缺乏高品质绿色公共开放空间"
                    ]
                }
            if "07_voting_scores" in full_key:
                return {
                    "👥 居民与使用群体代表": 85.0,
                    "💰 投资与运营开发主体": 82.0,
                    "📐 规划设计与法定义务人": 90.0,
                    "👥 居民代表（老王）": 85.0,
                    "💰 文旅运营商（赵总）": 82.0,
                    "📐 规划师（李工）": 90.0
                }
            if "05_mpi_ranking" in full_key:
                return [
                    {"地块名称": target_name, "MPI 得分": 88.5, "空间潜力原分": 0.92, "社会需求原分": 0.95, "环境现状评分": 0.28},
                    {"地块名称": f"{s_name}存量厂区", "MPI 得分": 84.2, "空间潜力原分": 0.89, "社会需求原分": 0.90, "环境现状评分": 0.35},
                    {"地块名称": f"{s_name}历史街巷", "MPI 得分": 81.6, "空间潜力原分": 0.85, "社会需求原分": 0.88, "环境现状评分": 0.42},
                ]
            return raw_val

        if isinstance(raw_val, str):
            adapted = (
                raw_val.replace("长春水产大市场", target_name)
                .replace("水产大市场", target_name)
                .replace("长春铁北片区", f"{s_city}{s_name}")
                .replace("伪满皇宫", primary_lm)
                .replace("长春伪满皇宫周边街区", f"{s_city}{s_name}")
                .replace("长春市宽城区伪满皇宫周边约160公顷街区", f"{s_city}{s_name}约{s_area}公顷街区")
                .replace("长春站", "交通枢纽")
                .replace("伊通河", "滨水绿道")
                .replace("老王", "原住居民代表")
                .replace("赵总", "投资运营主体")
                .replace("李工", "规划设计专家")
            )
            return adapted
        return raw_val
    except Exception:
        return BASELINE_STAGE_DATA.get(full_key)


def load_stage_output(stage_code: str, key: str, default=None):
    """从总线读取上游阶段的产出。
    
    具有防御性降级机制：如果请求的数据不存在或为空，
    自动回退至因地制宜自适应基准数据，确保跨阶段管线 100% 顺畅，杜绝 KeyError / AttributeError。
    """
    full_key = f"{stage_code}_{key}"
    bus_dict = _bus()

    # 1. 直接命中当前总线
    if full_key in bus_dict:
        val = bus_dict[full_key]
        if _is_meaningful(val):
            return val

    # 2. 检查跨阶段兼容别名 (如 04 与 05 互通)
    alias_codes = []
    if stage_code == "04":
        alias_codes.append("05")
    elif stage_code == "05":
        alias_codes.append("04")
    elif stage_code == "07":
        alias_codes.extend(["04", "05"])

    for ac in alias_codes:
        alt_key = f"{ac}_{key}"
        if alt_key in bus_dict:
            val = bus_dict[alt_key]
            if _is_meaningful(val):
                return val

    # 3. 如果调用方传递了有实际内容的默认值，返回默认值
    if _is_meaningful(default):
        return default

    # 4. 防御性降级到因地制宜自适应基准数据
    baseline_val = _get_adaptive_baseline_value(full_key)
    if baseline_val is None:
        for ac in alias_codes:
            baseline_val = _get_adaptive_baseline_value(f"{ac}_{key}")
            if baseline_val is not None:
                break

    if baseline_val is not None:
        logger.info(f"[StageDataBus] 数据项 {full_key} 缺失，自动防御性降级为因地制宜基准数据。")
        return baseline_val

    return default


def stage_ready(stage_code: str, key: str) -> bool:
    """判断指定阶段是否已产出某项数据。"""
    full_key = f"{stage_code}_{key}"
    if full_key in _bus():
        return True
    if stage_code in ("04", "05"):
        alt_code = "05" if stage_code == "04" else "04"
        if f"{alt_code}_{key}" in _bus():
            return True
    return False


def list_completed_stages() -> list[str]:
    """返回当前已有产出的阶段编号列表（去重排序）。"""
    codes = {k.split("_", 1)[0] for k in _bus()}
    return sorted(codes)


def require_upstream(current_stage: str, upstream_stage: str, key: str,
                     friendly_name: str = "") -> bool:
    """检查上游阶段数据是否就绪，未就绪时显示阻断提示。

    Returns True if data is available, False if missing (error shown).
    """
    if stage_ready(upstream_stage, key):
        return True

    stage_name = STAGE_MAP.get(upstream_stage, f"Stage {upstream_stage}")
    data_label = friendly_name or key
    st.error(
        f"⛔ **管线前置依赖缺失**\n\n"
        f"当前阶段 (Stage {current_stage}) 需要来自 **{stage_name}** (Stage {upstream_stage}) "
        f"的 **{data_label}** 数据。\n\n"
        f"请先完成 Stage {upstream_stage} 的量化分析，确保数据总线中存在对应产出后再返回本页面。"
    )
    return False


STAGE_MAP = {
    "00": "数据准备",
    "01": "任务解读",
    "02": "资料收集",
    "03": "现场调研",
    "04": "现状分析",
    "05": "问题诊断",
    "06": "目标定位",
    "07": "设计策略",
    "08": "总体城市设计",
    "09": "专项系统设计",
    "10": "重点地段深化",
    "11": "实施路径",
    "12": "城市设计导则",
    "13": "成果表达",
    "15": "AIGC设计推演"
}

def render_evidence_chain_bar(current_stage: str, required_stages: list[str]):
    """渲染增强型功能胶囊进度条，支持点击跳转页面。"""
    completed = list_completed_stages()
    pills = []
    for code in required_stages:
        done = code in completed
        is_current = code == current_stage
        name = STAGE_MAP.get(code, "未知阶段")
        
        # 修正：Streamlit 默认会自动剥离 "01_" 这种数字前缀
        # 所以跳转路径应直接使用阶段名称
        import urllib.parse
        page_slug = urllib.parse.quote(name)
        
        cls = "ec-current" if is_current else ("ec-done" if done else "ec-pending")
        
        # 构造 HTML
        label_html = f'<span class="ec-num">{code}</span><span class="ec-divider"></span><span class="ec-name">{name}</span>'
        
        pill_html = f'<div class="ec-pill {cls}">{label_html}</div>'
        pills.append(pill_html)

    # 构造完整的 HTML 并压缩
    html_container = f'<div class="evidence-chain">{"".join(pills)}</div>'
    style_html = """
        <style>
        .evidence-chain { 
            display: flex; 
            align-items: center; 
            gap: 12px; 
            margin: 16px 0 24px 0; 
            flex-wrap: wrap; 
        }
        .ec-pill { 
            display: flex;
            align-items: center;
            padding: 4px 12px; 
            border-radius: 100px; 
            font-size: 13px; 
            transition: all 0.2s ease;
            cursor: default;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .ec-num { 
            font-weight: 800; 
            opacity: 0.9;
        }
        .ec-divider {
            width: 1px;
            height: 12px;
            background: currentColor;
            margin: 0 8px;
            opacity: 0.3;
        }
        .ec-name { 
            font-weight: 500;
        }
        
        .ec-done { 
            background: rgba(34, 197, 94, 0.12); 
            color: #4ade80; 
            border-color: rgba(34, 197, 94, 0.3); 
        }
        
        .ec-current { 
            background: rgba(129, 140, 248, 0.2); 
            color: #a5b4fc; 
            border-color: rgba(129, 140, 248, 0.6); 
            box-shadow: 0 4px 12px rgba(129, 140, 248, 0.25);
        }
        
        .ec-pending { 
            background: rgba(148, 163, 184, 0.08); 
            color: #94a3b8; 
            border-color: rgba(148, 163, 184, 0.15); 
        }
        </style>
    """
    # 强制单行化，防止 Markdown 误解析
    full_html = "".join(line.strip() for line in (html_container + style_html).split("\n"))
    st.markdown(full_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════
    # AI 规划管线交接说明 (Stage Transition Agent)
    # ═══════════════════════════════════════════
    # 排除数据准备阶段 00
    if current_stage != "00":
        with st.expander("📋 AI 规划管线交接说明", expanded=False):
            cache_key = f"transition_summary_{current_stage}"
            if cache_key not in st.session_state:
                st.session_state[cache_key] = ""
                
            if st.session_state[cache_key] == "":
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.caption("✨ AI 正在自动分析上游所有阶段的产出数据，提炼核心结论与本阶段的设计任务红线。")
                with c2:
                    if st.button("🧠 提取并生成行动指南", key=f"btn_transition_{current_stage}", use_container_width=True):
                        with st.spinner("AI 正在深度解析上游决策链条..."):
                            summary = generate_stage_transition_summary(current_stage)
                            st.session_state[cache_key] = summary
                            st.rerun()
            else:
                st.markdown(st.session_state[cache_key])
                if st.button("🔄 重新提取生成", key=f"btn_re_transition_{current_stage}"):
                    st.session_state[cache_key] = ""
                    st.rerun()


def generate_stage_transition_summary(current_stage: str) -> str:
    """LLM 自动汇总前序阶段产出，为当前阶段生成工作交接行动指南。"""
    from src.engines.llm_engine import call_llm_engine
    
    bus_data = _bus()
    upstream_text = []
    
    # 提取所有小于当前阶段的产出
    for key, val in sorted(bus_data.items()):
        parts = key.split("_", 1)
        stage_prefix = parts[0]
        if stage_prefix.isdigit() and current_stage.isdigit() and int(stage_prefix) < int(current_stage):
            val_str = str(val)
            if len(val_str) > 1000:
                val_str = val_str[:1000] + "...(已截断)"
            key_name = parts[1] if len(parts) > 1 else key
            upstream_text.append(f"【Stage {stage_prefix} - {key_name}】:\n{val_str}")
                
    if not upstream_text:
        return "💡 **前序数据未就绪**：暂无充足的上游阶段数据产出。请先按顺序完成前序页面的量化分析以解锁智能工作衔接。"
        
    upstream_ctx = "\n\n".join(upstream_text)
    current_name = STAGE_MAP.get(current_stage, f"Stage {current_stage}")
    
    prompt = f"""
    你是一位资深的城市设计项目经理。目前项目已进行到【Stage {current_stage}: {current_name}】。
    
    以下是前序阶段的全部关键产出：
    {upstream_ctx}
    
    请根据这些上游数据，为即将开始的【Stage {current_stage}】生成一份 300 字左右的精炼工作交接及行动指南。
    
    要求：
    1. 💡 核心交接结论：从上游成果中提炼出最核心的 2-3 个对本阶段有直接指导意义的量化结论或策略决策。
    2. 🎯 本阶段核心目标：明确说明在本阶段需要达成什么空间设计或诊断指标。
    3. ⚠️ 关键约束：指出本阶段需要死守的红线（如限高、容积率或历史保护要素）。
    
    输出请使用简洁专业的规划行业术语。
    """
    
    return call_llm_engine(
        prompt=prompt, 
        system_prompt="你是一位资深的城市设计项目经理，善于跨阶段整合规划策略。", 
        model="deepseek-v4-pro"
    )


def save_stage_summary_to_file(
    stage_code: str,
    title: str,
    methodology: str,
    findings: list[dict],
    implication: str,
    ai_summary: str = ""
):
    """将当前阶段的方法论、核心发现及 AI 小结写入本地的汇总报告文档中，支持增量更新并按阶段编号排序。"""
    import os
    import re
    from pathlib import Path

    from src.config.runtime import resolve_path
    
    # 确定输出文件路径
    report_path = resolve_path("output/stage_generation_report.md")
    
    # 确保 output 目录存在
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 构建当前阶段的 Markdown 文本块
    findings_lines = []
    for idx, item in enumerate(findings):
        point = item.get("point", "").strip()
        evidence = item.get("evidence", "").strip()
        if point:
            line = f"{idx + 1}. **{point}**"
            if evidence:
                line += f" *(依据: {evidence})*"
            findings_lines.append(line)
    
    findings_str = "\n".join(findings_lines) if findings_lines else "*暂无核心发现*"
    
    ai_summary_section = ""
    if ai_summary:
        ai_summary_section = f"\n\n### 🧠 AI 阶段小结\n{ai_summary.strip()}"
        
    stage_section = f"""## 📌 Stage {stage_code}: {title}
- **方法/方法论**: {methodology or '无'}
- **后续影响**: {implication or '无'}

### 🔍 核心发现
{findings_str}{ai_summary_section}"""

    # 读取已有文档内容，解析已有的阶段数据
    sections = {}
    header_text = (
        "# UltimateDESIGN 城市设计大屏 - 阶段生成汇总报告\n\n"
        "本报告自动记录了在本次运行进程中，各个规划设计阶段所完成的完整生成内容、总结与方法论。\n\n"
        "*(注：本文件由系统自动维护，按阶段顺序增量更新)*\n"
    )
    
    if report_path.exists():
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 使用正则拆分已有的阶段块
            parts = re.split(r"\n*(?=## 📌 Stage \d+:)", content)
            
            # 保留头部
            if parts and not parts[0].startswith("## 📌 Stage"):
                header_text = parts[0].strip() + "\n\n"
                parts = parts[1:]
                
            for part in parts:
                match = re.match(r"## 📌 Stage (\d+):", part)
                if match:
                    code = match.group(1)
                    sections[code] = part.strip()
        except Exception as e:
            import logging
            logger = logging.getLogger("ultimateDESIGN")
            logger.warning("Failed to parse existing stage summaries report: %s", e)

    # 用当前阶段的最新内容覆盖或写入
    sections[stage_code] = stage_section.strip()
    
    # 按阶段编号排序重新拼接
    sorted_codes = sorted(sections.keys(), key=lambda x: int(x) if x.isdigit() else 99)
    
    full_report = header_text
    for code in sorted_codes:
        full_report += sections[code] + "\n\n"
        
    # 写入文件
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_report.strip() + "\n")
    except Exception as e:
        import logging
        logger = logging.getLogger("ultimateDESIGN")
        logger.error("Failed to write stage summaries report to file: %s", e)
