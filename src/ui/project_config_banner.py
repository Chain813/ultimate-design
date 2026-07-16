"""项目配置 Banner — 首次启动时引导用户填写项目/机构/场地/API 信息

检测 config/project.yaml 是否存在且填写完整。若否，渲染配置表单。
保存后写入 project.yaml + .env，提示用户刷新页面。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import streamlit as st
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_YAML = PROJECT_ROOT / "config" / "project.yaml"
ENV_FILE = PROJECT_ROOT / ".env"


# ═══════════════════════════════════════════════════════════════
# 配置读写
# ═══════════════════════════════════════════════════════════════

def load_project_config() -> dict:
    """读取 project.yaml，不存在或为空返回 {}"""
    if not PROJECT_YAML.exists():
        return {}
    try:
        with open(PROJECT_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
    except Exception:
        return {}


def _is_filled(val) -> bool:
    """检查值是否已填写（非空）"""
    if val is None:
        return False
    if isinstance(val, str):
        return bool(val.strip())
    if isinstance(val, (list, dict)):
        return len(val) > 0
    if isinstance(val, (int, float)):
        return True  # 0 也算已设置（area_ha 等字段默认为 0）
    return bool(val)


def is_project_configured() -> bool:
    """检查 project.yaml 是否已填写完整"""
    cfg = load_project_config()
    if not cfg:
        return False
    # 检查核心必填字段
    project = cfg.get("project", {})
    institution = cfg.get("institution", {})
    site = cfg.get("site", {})
    author = cfg.get("author", {})

    required = [
        _is_filled(project.get("name")),
        _is_filled(site.get("city")),
        _is_filled(site.get("name")),
        _is_filled(site.get("center")),
    ]
    return all(required)


def _read_env() -> dict[str, str]:
    """读取 .env 文件为 dict"""
    env = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _write_env(updates: dict[str, str]):
    """将键值对合并写入 .env（保留已有内容）"""
    existing = _read_env()
    existing.update(updates)
    lines = [
        "# UltimateDESIGN 环境变量 — 由项目配置面板自动生成",
        "# 请勿手动编辑此文件",
        "",
    ]
    for k, v in existing.items():
        lines.append(f"{k}={v}")
    lines.append("")
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ═══════════════════════════════════════════════════════════════
# 配置表单渲染
# ═══════════════════════════════════════════════════════════════

def render_project_config_banner():
    """在主页顶部渲染项目配置横幅。

    如果已配置，返回 True；如果渲染了配置表单，返回 False。
    """
    if is_project_configured():
        return True

    cfg = load_project_config()
    project = cfg.get("project", {})
    institution = cfg.get("institution", {})
    site = cfg.get("site", {})
    author = cfg.get("author", {})
    env = _read_env()

    # ── 横幅头部 ──
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border: 1px solid #334155; border-radius: 16px; padding: 24px 28px; margin-bottom: 8px;">
    <h2 style="color: #f1f5f9; margin: 0 0 4px 0; font-size: 20px;">
        🏗️ 项目初始化配置</h2>
    <p style="color: #94a3b8; margin: 0; font-size: 14px;">
        首次启动需要填写项目基本信息、场地参数和 API 密钥。保存后自动生成配置文件，下次启动不再显示。</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Tab 分页 ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 项目信息", "🏛️ 机构信息", "📍 场地信息", "👤 作者信息", "🔑 API 密钥"
    ])

    # ═══ Tab 1: 项目信息 ═══
    with tab1:
        proj_name = st.text_input(
            "项目名称", value=project.get("name", ""),
            placeholder="如：城市更新空间设计智能推演平台",
            help="显示在页面标题和报告封面",
        )
        proj_subtitle = st.text_input(
            "项目副标题", value=project.get("subtitle", ""),
            placeholder="如：——以长春市宽城区伪满皇宫周边街区为例",
            help="显示在页面标题下方",
        )

    # ═══ Tab 2: 机构信息 ═══
    with tab2:
        inst_name = st.text_input(
            "单位名称", value=institution.get("name", ""),
            placeholder="如：某建筑设计研究院",
        )
        inst_dept = st.text_input(
            "部门/团队", value=institution.get("department", ""),
            placeholder="如：城市设计所",
        )

    # ═══ Tab 3: 场地信息 ═══
    with tab3:
        col_a, col_b = st.columns(2)
        with col_a:
            site_city = st.text_input(
                "城市", value=site.get("city", ""),
                placeholder="如：长春",
            )
            site_district = st.text_input(
                "行政区", value=site.get("district", ""),
                placeholder="如：宽城区",
            )
        with col_b:
            site_name = st.text_input(
                "地块名称", value=site.get("name", ""),
                placeholder="如：伪满皇宫周边街区",
            )
            site_area = st.number_input(
                "面积（公顷）", value=site.get("area_ha", 0),
                min_value=0, step=1,
            )

        st.markdown("##### 📍 中心经纬度")
        center = site.get("center", [])
        col_lng, col_lat = st.columns(2)
        with col_lng:
            site_lng = st.number_input(
                "经度", value=float(center[0]) if center else 0.0,
                format="%.6f",
                help="点击下方地图获取坐标",
            )
        with col_lat:
            site_lat = st.number_input(
                "纬度", value=float(center[1]) if len(center) > 1 else 0.0,
                format="%.6f",
            )

        # 交互地图选点（仅当经纬度有效时渲染）
        if site_lng != 0.0 and site_lat != 0.0:
            import pandas as pd
            map_df = pd.DataFrame({"lat": [site_lat], "lon": [site_lng]})
            st.map(map_df, zoom=14, height=280, use_container_width=True)
            st.caption("👆 上方地图标记了当前中心点。在浏览器中打开 Google Maps / 高德地图，右键点击目标位置获取经纬度。")

        site_desc = st.text_area(
            "场地描述", value=site.get("description", ""),
            placeholder="如：由长春大街、长白路、东九条、亚泰快速路围合而成，研究范围约160公顷。",
            height=80,
        )

        # 视口参数
        viewport = site.get("viewport", {})
        with st.expander("🗺️ 地图视口参数（可选）"):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                vp_zoom = st.number_input("默认缩放", value=viewport.get("zoom", 14), min_value=1, max_value=20)
            with col_v2:
                vp_pitch = st.number_input("倾斜角", value=viewport.get("pitch", 60), min_value=0, max_value=90)
            col_v3, _col_v4 = st.columns(2)
            with col_v3:
                vp_bearing = st.number_input("旋转角", value=viewport.get("bearing", -20), min_value=-180, max_value=180)

    # ═══ Tab 4: 作者信息 ═══
    with tab4:
        col_au1, col_au2 = st.columns(2)
        with col_au1:
            author_name = st.text_input(
                "作者姓名", value=author.get("name", ""),
                placeholder="项目负责人",
            )
        with col_au2:
            author_id = st.text_input(
                "编号", value=author.get("id", ""),
                placeholder="工号/学号",
            )

    # ═══ Tab 5: API 密钥 ═══
    with tab5:
        st.markdown("##### 🔐 LLM API")
        deepseek_key = st.text_input(
            "DEEPSEEK_API_KEY",
            value=env.get("DEEPSEEK_API_KEY", os.environ.get("DEEPSEEK_API_KEY", "")),
            type="password",
            placeholder="sk-...",
            help="必填 — 从 platform.deepseek.com 获取",
        )

        st.markdown("##### 🗺️ 地图 API（可选）")
        baidu_ak = st.text_input(
            "Baidu_Map_AK",
            value=env.get("Baidu_Map_AK", os.environ.get("Baidu_Map_AK", "")),
            type="password",
            placeholder="百度地图 AK",
            help="可选 — 用于地理编码和 POI 采集",
        )

    # ═══════════════════════════════════════
    # 保存按钮
    # ═══════════════════════════════════════
    st.markdown("---")
    col_save, _col_status = st.columns([1, 3])
    with col_save:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            # 验证必填项
            errors = []
            if not proj_name.strip():
                errors.append("项目名称")
            if not site_city.strip():
                errors.append("城市")
            if not site_name.strip():
                errors.append("地块名称")
            if not deepseek_key.strip():
                errors.append("DEEPSEEK_API_KEY")

            if errors:
                st.error(f"请填写必填项：{', '.join(errors)}")
                return False

            # 构建 project.yaml
            proj_data = {
                "project": {
                    "name": proj_name.strip(),
                    "subtitle": proj_subtitle.strip(),
                },
                "institution": {
                    "name": inst_name.strip(),
                    "department": inst_dept.strip(),
                },
                "site": {
                    "city": site_city.strip(),
                    "district": site_district.strip(),
                    "name": site_name.strip(),
                    "center": [site_lng, site_lat],
                    "area_ha": site_area,
                    "description": site_desc.strip(),
                    "viewport": {
                        "center": [site_lng, site_lat],
                        "zoom": vp_zoom,
                        "pitch": vp_pitch,
                        "bearing": vp_bearing,
                    },
                },
                "author": {
                    "name": author_name.strip(),
                    "id": author_id.strip(),
                },
            }

            # 写入 project.yaml
            config_dir = PROJECT_YAML.parent
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(PROJECT_YAML, "w", encoding="utf-8") as f:
                yaml.dump(proj_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            # 写入 .env
            env_updates = {"DEEPSEEK_API_KEY": deepseek_key.strip()}
            if baidu_ak.strip():
                env_updates["Baidu_Map_AK"] = baidu_ak.strip()
            _write_env(env_updates)

            # 同时设置当前进程环境变量
            os.environ["DEEPSEEK_API_KEY"] = deepseek_key.strip()
            if baidu_ak.strip():
                os.environ["BAIDU_MAP_AK"] = baidu_ak.strip()

            st.success("✅ 配置已保存！页面将在 2 秒后自动刷新...")
            import time
            time.sleep(2)
            st.rerun()

    # 未保存时，阻止页面其余内容加载，避免使用空配置导致报错
    st.warning("⚠️ 请先完成上方配置，否则系统功能可能无法正常运行。")
    return False
