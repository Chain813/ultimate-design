"""Geographic site configurations loader — 从 project.yaml 和 config.yaml 读取

读取优先级: config/project.yaml > config/config.yaml > 空字符串/零值
project.yaml 由项目配置 UI 面板自动生成，config.yaml 由开发者维护。

Usage:
    from src.config.site import (
        get_site_config, get_site_name, get_site_city,
        get_site_center, get_map_viewport, get_local_crs,
        get_landmarks, get_project_info, get_institution_info,
        get_author_info,
    )
"""

from __future__ import annotations

import logging
import yaml
from pathlib import Path

from src.config.loader import load_global_config

logger = logging.getLogger("ultimateDESIGN")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_YAML = PROJECT_ROOT / "config" / "project.yaml"


def _load_project_yaml() -> dict:
    """加载 config/project.yaml"""
    if not PROJECT_YAML.exists():
        return {}
    try:
        with open(PROJECT_YAML, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        logger.warning("Failed to load project.yaml", exc_info=True)
        return {}


# project.yaml (新) → config.yaml (旧) 键名映射
_KEY_MAP = {
    "name": "site_name",
    "city": "city_name",
    "district": "district_name",
    "description": "description",
    "center": "map.center",
    "viewport": "map",  # viewport 字段 map 到 config.yaml 的 map 段
    "landmarks": "landmarks",
    "area_ha": None,  # config.yaml 无对应字段
    "adjacent_features": "adjacent_features",
    "policies": "policies",
}

def _get_merged(key: str, default=None):
    """project.yaml 优先，否则回退到 config.yaml"""
    py = _load_project_yaml()
    if key in ("project", "institution", "author"):
        val = py.get(key)
        if val and isinstance(val, dict):
            return val
        return {}

    site_py = py.get("site", {})
    site_cfg = load_global_config().get("site", {})

    # 尝试从 project.yaml → site 获取
    result = _nested_get(site_py, key)
    if result is not None:
        return result

    # 回退 config.yaml — 需要键名映射
    cfg_key = _KEY_MAP.get(key, key)
    if cfg_key:
        result = _nested_get(site_cfg, cfg_key)
        if result is not None:
            return result
    return default


def _nested_get(d: dict, key: str):
    """支持嵌套键如 'map.center'，空值视为未设置"""
    keys = key.split(".")
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return None
    # 空字符串、空列表、空字典、0 都视为有效值（仅 None 视为未设置）
    if d is None:
        return None
    if isinstance(d, str) and d.strip() == "":
        return None
    if isinstance(d, (list, dict)) and len(d) == 0:
        return None
    return d


# ═══════════════════════════════════════════════════════════════
# 项目/机构/作者（来自 project.yaml）
# ═══════════════════════════════════════════════════════════════

def get_project_info() -> dict:
    """返回 {'name': str, 'subtitle': str}"""
    return _get_merged("project") or {}

def get_institution_info() -> dict:
    """返回 {'name': str, 'department': str}"""
    return _get_merged("institution") or {}

def get_author_info() -> dict:
    """返回 {'name': str, 'id': str}"""
    return _get_merged("author") or {}


# ═══════════════════════════════════════════════════════════════
# 场地信息（project.yaml > config.yaml > fallback）
# ═══════════════════════════════════════════════════════════════

def get_site_config() -> dict:
    """返回合并后的 site 配置"""
    site_cfg = load_global_config().get("site", {})
    py = _load_project_yaml().get("site", {})
    merged = dict(site_cfg)
    # project.yaml 的值覆盖 config.yaml
    for k, v in py.items():
        if v not in (None, "", [], {}):
            merged[k] = v
    return merged

def get_site_name() -> str:
    return _get_merged("name") or ""

def get_site_city() -> str:
    return _get_merged("city") or ""

def get_site_district() -> str:
    return _get_merged("district") or ""

def get_site_center() -> list[float]:
    c = _get_merged("center")
    if c and len(c) == 2:
        return [float(c[0]), float(c[1])]
    # fallback to config.yaml map.center
    map_cfg = load_global_config().get("site", {}).get("map", {})
    return map_cfg.get("center", [0.0, 0.0])

def get_map_viewport() -> dict:
    """返回地图视口参数"""
    vp = _get_merged("viewport") or {}
    map_cfg = load_global_config().get("site", {}).get("map", {})
    center = vp.get("center") or map_cfg.get("center", [0.0, 0.0])
    return {
        "center": center,
        "zoom": vp.get("zoom") or map_cfg.get("zoom", 14.0),
        "pitch": vp.get("pitch") or map_cfg.get("pitch", 65.0),
        "bearing": vp.get("bearing") or map_cfg.get("bearing", 30.0),
        "min_zoom": map_cfg.get("min_zoom", 10.0),
        "max_zoom": map_cfg.get("max_zoom", 18.0),
    }

def get_local_crs() -> str:
    return load_global_config().get("site", {}).get("local_crs", "EPSG:32650")

def get_landmarks() -> list[dict]:
    lm = _get_merged("landmarks")
    if lm:
        return lm
    return load_global_config().get("site", {}).get("landmarks", [])

def get_site_desc() -> str:
    return _get_merged("description") or ""

def get_site_adjacent() -> str:
    return _get_merged("adjacent_features") or load_global_config().get("site", {}).get("adjacent_features", "")

def get_site_policies() -> list[str]:
    p = _get_merged("policies")
    if p:
        return p
    return load_global_config().get("site", {}).get("policies", [])
