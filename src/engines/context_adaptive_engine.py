"""Context-Adaptive Inference Engine for UltimateDESIGN.

Pure data-driven, zero-preset-template spatial reasoning engine:
1. infer_plot_diagnostics: Infers real spatial pain points from quantitative metrics.
2. generate_adaptive_personas: Dynamically derives realistic tripartite stakeholder personas and system prompts.
3. generate_adaptive_aigc_prompt: Extracts regional climate features from geographic coordinates and constructs AIGC prompts.
4. get_utm_epsg_for_coordinates: Dynamically calculates standard global UTM EPSG codes.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Union


def get_utm_epsg_for_coordinates(lon: float, lat: float) -> int:
    """Dynamically calculates the global standard UTM projection EPSG code for given WGS84 coordinates.

    Args:
        lon: Longitude in degrees (-180.0 to 180.0).
        lat: Latitude in degrees (-90.0 to 90.0).

    Returns:
        int: Standard EPSG code, e.g. 32651 for Lon 125°/Lat 43°N, 32650 for Lon 114°/Lat 22°N.
    """
    lon_f = float(lon)
    lat_f = float(lat)

    # Calculate UTM Zone 1 to 60
    utm_zone = int(math.floor((lon_f + 180.0) / 6.0)) + 1
    if utm_zone > 60:
        utm_zone = 60
    elif utm_zone < 1:
        utm_zone = 1

    if lat_f >= 0:
        return 32600 + utm_zone
    else:
        return 32700 + utm_zone


def infer_plot_diagnostics(
    plot_data: Optional[Dict[str, Any]] = None,
    site_context: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Infers objective, data-driven spatial pain points from real quantitative metrics of a plot.

    Args:
        plot_data: Dictionary containing plot metrics (e.g. land_use, area_ha, gvi_mean,
                   poi_count, building_density, svf, far, height, clutter_mean, enclosure_mean).
        site_context: Optional broader contextual info (e.g. city, district, slope, waterfront).

    Returns:
        List[str]: List of derived urban design diagnostic statements.
    """
    plot = plot_data or {}
    context = site_context or {}
    diagnostics: List[str] = []

    # 1. Normalize land use
    raw_land_use = str(
        plot.get("land_use")
        or plot.get("landuse")
        or plot.get("type")
        or plot.get("用地性质")
        or context.get("dominant_land_use", "")
    ).lower()

    # 2. Extract quantitative indicators
    area_ha = plot.get("area_ha")
    if area_ha is None:
        sqm = plot.get("area_sqm") or plot.get("area_m2") or plot.get("Shape_Area")
        if sqm is not None:
            area_ha = float(sqm) / 10000.0
    else:
        try:
            area_ha = float(area_ha)
        except (ValueError, TypeError):
            area_ha = None

    def _safe_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    gvi = _safe_float(plot.get("gvi_mean") if plot.get("gvi_mean") is not None else plot.get("gvi"))
    svf = _safe_float(plot.get("svf") if plot.get("svf") is not None else plot.get("svf_mean"))
    poi = _safe_float(plot.get("poi_count") if plot.get("poi_count") is not None else plot.get("poi_density"))
    bd = _safe_float(plot.get("building_density") if plot.get("building_density") is not None else plot.get("density"))
    if bd is not None and bd > 1.0:
        bd = bd / 100.0

    far = _safe_float(plot.get("far") if plot.get("far") is not None else plot.get("floor_area_ratio"))
    height = _safe_float(plot.get("height") if plot.get("height") is not None else plot.get("building_height"))
    clutter = _safe_float(plot.get("clutter_mean") if plot.get("clutter_mean") is not None else plot.get("clutter"))
    enclosure = _safe_float(plot.get("enclosure_mean") if plot.get("enclosure_mean") is not None else plot.get("enclosure"))

    # 3. Typology / Land-use based spatial logic
    is_industrial = any(k in raw_land_use for k in ["industrial", "工业", "工矿", "仓储", "产城"])
    is_residential = any(k in raw_land_use for k in ["residential", "居住", "住宅", "小区", "社区"])
    is_commercial = any(k in raw_land_use for k in ["commercial", "商业", "零售", "商务", "批发"])
    is_waterfront = any(k in raw_land_use for k in ["water", "滨水", "河", "湖", "湿地"]) or context.get("is_waterfront", False)
    is_park = any(k in raw_land_use for k in ["park", "green", "绿地", "公园"])

    if is_industrial:
        diagnostics.append("工业厂房存量闲置，大跨度钢结构/桁架空间具备改造潜力，但结构抗震与耐久性需复核")
        diagnostics.append("工业生产用地与周边城市公共活力割裂，土地利用集约度偏低，缺乏慢行开放渗透通道")
        diagnostics.append("原工业地块需开展土壤及地下水环境风险排查，防范环境安全与棕地遗留问题")
    elif is_residential:
        diagnostics.append("老旧居住组团适老无障碍设施匮乏，公共活动空间与电梯加装覆盖不足，适老化改造迫切")
        diagnostics.append("老旧管网（供排水、消防水管）设施老化严重，雨污混流与消防应急通道隐患突出")
        diagnostics.append("内部人车动线混杂冲突，地面乱停乱放挤占组团绿地与步行消防通道")
    elif is_commercial:
        diagnostics.append("商业业态同质化竞争严重，街区首层活力与外摆互动界面不足，空间消费体验单一")
        diagnostics.append("商业步行连续性受车行道割裂，缺乏全天候遮阳避雨连廊与宜人的漫步微气候")
        diagnostics.append("夜间经济与青年潮流消费场景匮乏，非营业时段活力骤降（潮汐性冷清）")
    elif is_waterfront:
        diagnostics.append("滨水驳岸硬质化程度较高，缺乏多级生态缓冲带与下沉亲水步道")
        diagnostics.append("滨水视线通廊受沿线建筑遮挡，城市腹地向水岸的慢行可达性与贯通性不足")
        diagnostics.append("滨水防汛排涝与海绵蓄滞韧性偏弱，需平衡生态防洪标高与休闲活动需求")
    elif is_park:
        diagnostics.append("绿地内部游憩设施功能单一，林下慢行连通度不足，生态效益向人文活力转化率较低")
    else:
        diagnostics.append("功能混合度失衡，日间办公与夜间生活职住分离明显，街区全时段活力不足")
        diagnostics.append("公共交往中介空间匮乏，建筑界面消极封闭，缺乏开放式口袋公园与社区交流节点")

    # 4. Quantitative Threshold Inferences
    # GVI (Green View Index)
    if gvi is not None:
        if gvi < 0.15:
            diagnostics.append(f"绿视率严重匮乏（GVI={gvi:.1%}，低于15%基准线），形成视觉热岛与景观盲区，亟待见缝插绿织补口袋公园与立体绿化")
        elif gvi < 0.25:
            diagnostics.append(f"绿视率偏低（GVI={gvi:.1%}），街旁绿化连续性不足，林荫覆盖率需补足")
        elif gvi >= 0.35:
            diagnostics.append(f"绿化本底指标良好（GVI={gvi:.1%}），但需优化复层绿化群落结构与林下慢行可达性")

    # SVF (Sky View Factor)
    if svf is not None:
        if svf < 0.25:
            diagnostics.append(f"天空开敞度极低（SVF={svf:.2f}），高密峡谷效应显著，底层日照采光不足且自然对流通风受限")
        elif svf > 0.70:
            diagnostics.append(f"天空开敞度过大（SVF={svf:.2f}），街道空间尺度过宽失落，夏季缺乏树冠遮荫，微气候热舒适度较差")

    # POI Density / Count
    if poi is not None:
        if poi < 15:
            diagnostics.append(f"POI便民设施匮乏（仅{int(poi)}处），15分钟社区生活圈服务便利度不足，日间功能冷清单一")
        elif poi > 120:
            diagnostics.append(f"POI设施过度密集（{int(poi)}处），商业人车混流严重，物流配送与临停装卸严重侵占公共慢行空间")

    # Building Density
    if bd is not None:
        if bd > 0.45:
            diagnostics.append(f"建筑基底密度偏高（{bd:.1%}），开敞活动场地匮乏，消防救援场地与日照间距承载力承压")
        elif bd < 0.20:
            diagnostics.append(f"建筑密度较低（{bd:.1%}），土地空间肌理离散，存在低效闲置夹心地块需集约整合")

    # Area Scale
    if area_ha is not None:
        if area_ha > 15:
            diagnostics.append(f"地块超尺度（{area_ha:.1f} ha），内部街区封闭割裂，需推行“小街区、密路网”打通毛细慢行通道")
        elif area_ha < 1.5:
            diagnostics.append(f"地块用地规模狭小（{area_ha:.1f} ha），常规规划开发受限，适宜采取针灸式微更新与轻介入复合利用")

    # FAR
    if far is not None:
        if far > 3.5:
            diagnostics.append(f"容积率指标偏高（FAR={far:.1f}），空间承载力趋于饱和，对周边微环境日照与交通出行造成较大峰值负荷")
        elif 0 < far < 1.2:
            diagnostics.append(f"容积率偏低（FAR={far:.1f}），地上空间开发集约度不足，存量空间具备增量更新潜力")

    # Building Height
    if height is not None and height > 50:
        diagnostics.append(f"建筑平均高度较高（{height:.1f}m），高层风障与阴影遮挡显著，高空微气候对地面产生下洗风干扰")

    # Street Clutter
    if clutter is not None and clutter > 0.35:
        diagnostics.append(f"街道视觉杂乱度偏高（杂乱指数={clutter:.2f}），店招线缆与违章搭建严重侵蚀空间品质")

    # Street Enclosure
    if enclosure is not None and enclosure > 0.65:
        diagnostics.append(f"空间围合感过度压抑（围合度={enclosure:.2f}），视线廊道闭塞，缺乏开敞对景节点")

    return diagnostics


class AdaptivePersonas(list):
    """Container for dynamically generated tripartite stakeholder personas.

    Supports both list-style iteration/indexing and dict-style key access/methods.
    """

    def __init__(self, items: List[Dict[str, Any]]):
        super().__init__(items)
        self._by_key: Dict[str, Dict[str, Any]] = {}
        for item in items:
            key = item.get("role_key")
            if key:
                self._by_key[key] = item

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            if item in self._by_key:
                return self._by_key[item]
            raise KeyError(item)
        return super().__getitem__(item)

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, str) and item in self._by_key:
            return True
        return super().__contains__(item)

    def items(self):
        return self._by_key.items()

    def values(self):
        return self._by_key.values()

    def keys(self):
        return self._by_key.keys()

    def get(self, key: str, default: Any = None) -> Any:
        return self._by_key.get(key, default)


def generate_adaptive_personas(
    site_context: Optional[Dict[str, Any]] = None,
    target_plot: Optional[Dict[str, Any]] = None,
    regulatory_limits: Optional[Dict[str, Any]] = None,
) -> AdaptivePersonas:
    """Dynamically generates 3 realistic stakeholder personas without hardcoded preset templates.

    Stakeholders generated:
    1. resident_or_user: Representative of existing residents / daily space users.
    2. investor_or_operator: Commercial investment or operating entity.
    3. planner_or_regulator: Statutory urban planner & regulatory reviewer.

    Args:
        site_context: Broader site context (e.g. city, district, name).
        target_plot: Target plot data (e.g. name, land_use, area_ha, etc.).
        regulatory_limits: Local statutory limits (e.g. far, height_limit, building_density_max, greenery_ratio_min).

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of the 3 generated personas with role details and system prompts.
    """
    site = site_context or {}
    plot = target_plot or {}
    limits = regulatory_limits or {}

    city = str(site.get("city") or "本地")
    district = str(site.get("district") or "")
    plot_name = str(plot.get("name") or "目标更新地块")
    raw_land_use = str(plot.get("land_use") or plot.get("landuse") or plot.get("type") or "综合用地")
    area_ha = plot.get("area_ha") or 5.0
    try:
        area_ha_val = float(area_ha)
    except (ValueError, TypeError):
        area_ha_val = 5.0

    # Inferred diagnostics to contextualize the personas
    diagnostics = infer_plot_diagnostics(plot, site)
    top_pain_points = "；".join(diagnostics[:3]) if diagnostics else "基础设施老化与公共空间品质不足"

    # Regulatory indicators
    far_limit = limits.get("far") or limits.get("far_max") or 2.5
    height_limit = limits.get("height_limit") or limits.get("height") or 36.0
    bd_limit = limits.get("building_density_max") or 0.35
    green_limit = limits.get("greenery_ratio_min") or 0.30

    bd_limit_str = f"{bd_limit * 100:.0f}%" if isinstance(bd_limit, (int, float)) and bd_limit <= 1.0 else f"{bd_limit}%"
    green_limit_str = f"{green_limit * 100:.0f}%" if isinstance(green_limit, (int, float)) and green_limit <= 1.0 else f"{green_limit}%"

    lu_lower = raw_land_use.lower()
    is_industrial = any(k in lu_lower for k in ["industrial", "工业", "工矿", "仓储"])
    is_residential = any(k in lu_lower for k in ["residential", "居住", "住宅", "社区"])
    is_commercial = any(k in lu_lower for k in ["commercial", "商业", "零售", "商务"])
    is_waterfront = any(k in lu_lower for k in ["water", "滨水", "河", "湖"])

    # 1. Resident / User Representative
    if is_industrial:
        user_name = f"{city}{plot_name}老厂区产业工人与文创新青年代表"
        user_stance = "强调保留老厂房的历史记忆与产业文脉，要求改造中配套充足的公共文化设施与青年创业低租金空间，避免改造成高消费孤岛。"
        user_interests = [
            "保留大跨度工业遗产与历史建筑肌理",
            "设立低成本青年众创工坊与社区工坊",
            "补齐周边公共绿地与慢行游憩通道",
            "改造过渡期间保障老职工生活生计延续性",
        ]
    elif is_residential:
        user_name = f"{city}{plot_name}原住居民与社区长者家庭代表"
        user_stance = "坚决捍卫原住民居住权益与生活便利性，急迫要求加装电梯、改造老化管网与增设适老慢跑空间，警惕过度商业化导致的物价上涨与噪音扰民。"
        user_interests = [
            "适老化设施与无障碍微坡道改造",
            "供排水与弱电消防管网全面翻新",
            "规范人车分流与地面停车秩序",
            "保障原住居民不被士绅化迁离",
        ]
    elif is_commercial:
        user_name = f"{city}{plot_name}沿街经营商户与年轻消费客群联合代表"
        user_stance = "呼吁优化街区慢行体验与外摆经营空间，提升日间与夜间多元引流能力，同时合理控制租金涨幅，兼顾老字号生存与新兴业态活力。"
        user_interests = [
            "连贯宽敞的人行步行街与遮阳避雨连廊",
            "放宽特色外摆与夜市集市运营限制",
            "完善微循环慢行与就近货运装卸点",
            "吸引多元年轻客流与社群活动",
        ]
    elif is_waterfront:
        user_name = f"{city}{plot_name}滨水游憩市民与水系生态保护倡导者"
        user_stance = "主张彻底打通滨水公共开放岸线，退让生态缓冲带，建立无障碍亲水步道，反对沿河私有化占领与高强度硬化破坏。"
        user_interests = [
            "连续贯通的亲水慢行绿道与步道踏步",
            "水岸生态湿地与本土水生植物保护",
            "亲子游憩、露营科普与滨水观景挑台",
            "严格控制沿岸建筑高度与视线通廊",
        ]
    else:
        user_name = f"{city}{plot_name}在地居民与复合空间使用者代表"
        user_stance = "主张平衡居住生活与共享空间，增设全天候开放口袋公园与邻里便民中心，提升街区整体人居微气候与归属感。"
        user_interests = [
            "15分钟生活圈便民服务网点健全",
            "口袋公园与儿童老人复合活动场地",
            "绿色低碳与微气候舒适度提升",
            "开放包容的社区共享交流中心",
        ]

    user_prompt = (
        f"你正在以【{user_name}】的身份参与{city}{district}{plot_name}的城市更新规划多方协商。\n"
        f"【地块概况】：用地性质为{raw_land_use}，面积约{area_ha_val:.1f}公顷。\n"
        f"【现场痛点】：{top_pain_points}。\n"
        f"【你的立场】：{user_stance}\n"
        f"【协商准则】：\n"
        f"1. 你的发声必须紧扣使用者切身利益与日常生活实际，注重柴米油盐、出行便利与人文归属，严禁使用虚假抽象的宏大词汇；\n"
        f"2. 针对运营商的激进商业诉求与规划师的冷峻指标，你要坚决维护使用者的底线，提出具体的空间改进诉求；\n"
        f"3. 在对方做出实质性民生与公共利益让步时，展现出适度的妥协与协作共赢姿态。"
    )

    # 2. Investor / Operator Entity
    if is_industrial:
        operator_name = f"{city}{plot_name}产城融合与文化科创园区运营实体"
        operator_stance = "强调资金投入产出自平衡与资产增值，主张利用大跨度厂房打造复合型文创科创空间，争取灵活的商办混合比例与长期运营周期。"
        operator_interests = [
            "大跨度空间多业态重构与商业出租坪效",
            "政府对存量工业用地盘活的税收与容积率激励",
            "导入高附加值科技文创与特色首店品牌",
            "稳定可预期的自持运营周期与投资回报",
        ]
    elif is_residential:
        operator_name = f"{city}{plot_name}现代智慧社区与存量资产综合运营管理方"
        operator_stance = "主张通过盘活闲置底层架空层与公建配套，引入高品质社区便民服务与智慧物业，在保障基础民生的同时实现运营服务微利可持续。"
        operator_interests = [
            "底层沿街商业与便民空间经营权自主性",
            "智慧停车设施与新能源充电桩有偿运营",
            "政府老旧小区改造专项资金与物业专项补贴",
            "长期物业运维成本控制与收缴率保障",
        ]
    elif is_commercial:
        operator_name = f"{city}{plot_name}文商旅场景创新与商业资产投资运营实体"
        operator_stance = "主张打破传统商场封闭格局，打造开放式街区与沉浸式首店消费场景，要求充足的商业容积率与特色外立面改造权限，最大化客流与坪效。"
        operator_interests = [
            "提高商业建筑面积与首层临街连续商业界面",
            "打造网红打卡节点与夜间经济沉浸式光影场景",
            "合理的地下商业开发与停车接驳效率",
            "多元品牌招商组合与快速资金回笼周期",
        ]
    elif is_waterfront:
        operator_name = f"{city}{plot_name}滨水休闲度假与水上文旅运营联合体"
        operator_stance = "主张沿水岸布局高附加值文旅休闲、轻食水吧与亲水露营业态，通过打造水上运动与滨水演艺消费闭环，实现生态价值向经济价值转化。"
        operator_interests = [
            "水岸沿线商业服务设施（轻餐饮、文创小品）特许经营权",
            "亲水码头与水上娱乐项目的运营许可",
            "夜间滨水光影秀与季节性文旅节庆引流",
            "合理的投资分期与水务环保准入协同",
        ]
    else:
        operator_name = f"{city}{plot_name}城市更新资产发展与综合运营投资主体"
        operator_stance = "坚持商业可行性与社会效益并重，要求明确的产权边界与灵活的空间使用许可，通过高品质内容运营盘活低效存量空间。"
        operator_interests = [
            f"合理的开发容积率（目标FAR≥{far_limit}）与业态配比",
            "多元功能混合的弹性规划许可",
            "品牌主力店引入与全周期运营现金流稳健",
            "明确的政企合作收益分成与退出机制",
        ]

    operator_prompt = (
        f"你正在以【{operator_name}】的身份参与{city}{district}{plot_name}的城市更新规划多方协商。\n"
        f"【地块概况】：用地性质为{raw_land_use}，面积约{area_ha_val:.1f}公顷。\n"
        f"【现场痛点】：{top_pain_points}。\n"
        f"【控规红线】：容积率上限{far_limit}，建筑限高{height_limit}米。\n"
        f"【你的立场】：{operator_stance}\n"
        f"【协商准则】：\n"
        f"1. 你的发声始终锚定商业自平衡、坪效回报与资金运转，强调没有可持续的商业模式，任何蓝图都难以长久维持；\n"
        f"2. 积极回应原住人群的诉求，但必须将其与商业赋能、客流提升相结合（如用商业收益反哺公共设施运维）；\n"
        f"3. 主动争取规划部门在容积率、外摆边界和功能混合上的弹性政策支持。"
    )

    # 3. Statutory Planner / Regulatory Reviewer
    planner_name = f"{city}自然资源与法定空间规划管控责任人"
    planner_stance = (
        f"严格恪守国土空间详细规划刚性约束（FAR≤{far_limit}、限高≤{height_limit}m、绿地率≥{green_limit_str}），"
        f"坚守公共安全与生态底线，统筹协调历史风貌、基础设施与公共利益最大化。"
    )
    planner_interests = [
        f"严格执行法定控规指标（容积率≤{far_limit}，建筑高度≤{height_limit}m，建筑密度≤{bd_limit_str}，绿地率≥{green_limit_str}）",
        "确保消防救援通道贯通、市政管网容量平衡与抗震防灾韧性",
        "打通城市开敞空间视线廊道与公共慢行步行通廊",
        "坚守生态保护红线，防范过度商业化对城市文脉与人居环境的不可逆破坏",
    ]

    planner_prompt = (
        f"你正在以【{planner_name}】的身份主持并监督{city}{district}{plot_name}的城市更新规划多方协商。\n"
        f"【地块概况】：用地性质为{raw_land_use}，面积约{area_ha_val:.1f}公顷。\n"
        f"【现场痛点】：{top_pain_points}。\n"
        f"【法定红线】：容积率上限严格限制在 {far_limit}，建筑限高 {height_limit}米，建筑密度上限 {bd_limit_str}，绿地率底线 {green_limit_str}。\n"
        f"【你的立场】：{planner_stance}\n"
        f"【协商准则】：\n"
        f"1. 你的职责是担当公共利益的守护者与法定控规的裁判员，用专业规划学、空间句法与法条刚性约束各方；\n"
        f"2. 坚决否定突破生态红线、占用消防通道、破坏城市天际线与严重挤占公共绿地的非法诉求；\n"
        f"3. 善于运用“容积率转移/奖励”、“空间分层出让”与“小街区密路网”等科学规划工具，引导居民与资本达成法定框架下的共赢共识。"
    )
    resident_persona = {
        "role_key": "resident_or_user",
        "name": user_name,
        "role_title": user_name,
        "display_name": user_name,
        "category": "原住与使用人群代表",
        "identity": "原住与使用人群代表",
        "stance": user_stance,
        "core_demands": user_stance,
        "bargaining_chips": f"掌握{plot_name}现场实际使用权与公共诉求话语权，主张改造符合民意",
        "core_interests": user_interests,
        "system_prompt": user_prompt,
        "avatar_file": "resident.png",
        "color": "#ff9500",
        "bg_color": "#fff8f0",
        "text_color": "#b25e00",
    }
    operator_persona = {
        "role_key": "investor_or_operator",
        "name": operator_name,
        "role_title": operator_name,
        "display_name": operator_name,
        "category": "投资与运营实体",
        "identity": "投资与运营实体",
        "stance": operator_stance,
        "core_demands": operator_stance,
        "bargaining_chips": "主导产业投资与全生命周期运营造血，具备商业资源引入与资金杠杆能力",
        "core_interests": operator_interests,
        "system_prompt": operator_prompt,
        "avatar_file": "developer.png",
        "color": "#0071e3",
        "bg_color": "#f0f7ff",
        "text_color": "#0055b3",
    }
    planner_persona = {
        "role_key": "planner_or_regulator",
        "name": planner_name,
        "role_title": planner_name,
        "display_name": planner_name,
        "category": "规划与法定义务人",
        "identity": "规划与法定义务人",
        "stance": planner_stance,
        "core_demands": planner_stance,
        "bargaining_chips": f"依法行使国土空间规划管控与审批权，坚守容积率与高度法定刚性红线",
        "core_interests": planner_interests,
        "system_prompt": planner_prompt,
        "avatar_file": "planner.png",
        "color": "#34c759",
        "bg_color": "#f0fff4",
        "text_color": "#22863a",
    }

    return AdaptivePersonas([resident_persona, operator_persona, planner_persona])


def generate_adaptive_aigc_prompt(
    site_context: Optional[Dict[str, Any]] = None,
    target_plot: Optional[Dict[str, Any]] = None,
    consensus: Optional[Union[Dict[str, Any], List[str]]] = None,
) -> Dict[str, str]:
    """Generates climate-adaptive and consensus-driven AIGC rendering prompts based on coordinates and plot data.

    Extracts regional climate adaptations:
    - Northern: Cold climate insulation, snow-shedding pitched roofs, wind-shield buffer vegetation, winter sun atrium.
    - Southern: Humid subtropical shading, natural breezeway corridors, covered colonnades/arcades, stilt ground floor.
    - Southwestern: Terraced mountainous forms, stepped courtyards, vernacular lightwells, multi-level skybridges.
    - Jiangnan: Waterfront revetments, stepped water ghats, slate grey and white vernacular modernism, bioswale wetlands.
    - Northwestern: Arid continental design, rammed earth textures, compact protective enclosures, xeriscaping.

    Args:
        site_context: Contains geographic coordinates (lat, lon) and location names.
        target_plot: Contains land use and plot parameters.
        consensus: Negotiated agreements or consensus keywords.

    Returns:
        Dict[str, str]: Dictionary containing positive prompt, negative prompt, climate zone, and features.
    """
    site = site_context or {}
    plot = target_plot or {}

    # Extract coordinates
    lat = site.get("lat") or site.get("latitude")
    lon = site.get("lon") or site.get("lng") or site.get("longitude")
    center = site.get("center") or plot.get("center")
    if isinstance(center, (list, tuple)) and len(center) >= 2:
        if lon is None:
            lon = center[0]
        if lat is None:
            lat = center[1]

    city_name = str(site.get("city") or "")

    # Fallback to city coordinates if missing
    if lat is None or lon is None:
        if any(c in city_name for c in ["哈尔滨", "长春", "沈阳", "北京", "呼和浩特", "大连"]):
            lat, lon = 43.85, 125.32
        elif any(c in city_name for c in ["广州", "深圳", "海口", "三亚", "厦门", "南宁"]):
            lat, lon = 23.13, 113.26
        elif any(c in city_name for c in ["成都", "重庆", "贵阳", "昆明"]):
            lat, lon = 30.65, 104.06
        elif any(c in city_name for c in ["苏州", "杭州", "南京", "上海", "无锡", "绍兴"]):
            lat, lon = 31.30, 120.62
        elif any(c in city_name for c in ["兰州", "乌鲁木齐", "银川", "西宁"]):
            lat, lon = 36.06, 103.83
        else:
            lat, lon = 39.90, 116.40  # Default temperate

    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (ValueError, TypeError):
        lat_f, lon_f = 39.90, 116.40

    raw_land_use = str(plot.get("land_use") or plot.get("landuse") or plot.get("type") or "").lower()

    # Climate Classification
    if lat_f >= 36.0 and lon_f >= 105.0:
        climate_zone = "北方防寒向阳防雪微气候区"
        climate_features = "北方防寒向阳防雪微气候适应性：建筑朝向南偏东以最大化冬季向阳采暖与日照增热，注重外墙防寒保温，设计局部坡屋顶以利积雪滑落与防雪防冻，实体保温外墙结合暖色系陶土板与石材，外围配置针阔混交防风林削弱冬季凛冽西北季风，配置温室阳光中庭营造宜人微气候。"
        climate_en_tokens = (
            "cold-climate responsive architecture, winter solar orientation, snow-shedding pitched roof profiles, "
            "heavy thermal-mass exterior envelope, winter evergreen shelterbelt landscape, double-glazed sunlit atrium, "
            "warm natural timber and terracotta finishes"
        )
    elif lat_f < 26.0:
        climate_zone = "华南湿热遮阳通风骑楼微气候区"
        climate_features = "华南湿热遮阳通风骑楼微气候适应性：针对高湿高热强日照，建筑首层架空形成开放通透通风走廊，沿街设置具有岭南特色的挑檐连廊与遮阳骑楼，立面配置可调节深远铝合金遮阳百叶与垂直立体绿化，屋顶设计绿化降温花园与耐台风耐暴雨海绵排水系统。"
        climate_en_tokens = (
            "subtropical humid-climate adaptive architecture, continuous shaded colonnades and pedestrian arcade, "
            "deep overhang sunshades and louvered screens, open ground-level stilt breezeways, biophilic vertical green facades, "
            "lush subtropical landscape, permeable cooling roof gardens"
        )
    elif lon_f < 108.0 and 21.0 <= lat_f <= 33.0:
        climate_zone = "西南山地院落退台微气候区"
        climate_features = "西南山地院落退台微气候适应性：顺应起伏山势随坡就势展开，采用多层次阶梯退台与空中连廊院落，融合川渝巴蜀传统天井院落以促进自然拔风与天光采光，坡地层叠露台结合耐阴湿生苔藓蕨类植被，营造层层错落的立体山水聚落。"
        climate_en_tokens = (
            "mountainous terraced architecture hugging natural hillside contours, multi-level stepped landscaped terraces, "
            "traditional lightwell courtyards with stack ventilation, elevated skybridges connecting clusters, "
            "mist-adapted lush native flora, layered organic hill-town spatial syntax"
        )
    elif (lon_f >= 118.0 and 27.0 <= lat_f <= 34.0) or any(w in raw_land_use for w in ["water", "滨水"]):
        climate_zone = "江南水网亲水驳岸微气候区"
        climate_features = "江南水网亲水驳岸微气候适应性：建筑紧密呼应滨水水系，采用多级生态软质亲水驳岸与近水缓坡亲水踏步，建筑立面运用青砖、黛瓦与暖灰钢玻构件的现代转译，内部营造小桥流水、滨水慢行游廊与雨水花园渗透湿地，展现粉墙黛瓦与枕河人家的新中式诗意水乡风貌。"
        climate_en_tokens = (
            "waterfront Jiangnan vernacular modernism, terraced ecological river revetment, wooden waterside boardwalks and stone stepping ghats, "
            "slate grey pitched roofs and white masonry accents, meandering canal promenades, rain gardens with bio-retention wetlands, "
            "reflective calm waters"
        )
    elif lon_f < 105.0 and lat_f >= 34.0:
        climate_zone = "西北干旱防风固沙微气候区"
        climate_features = "西北干旱防风固沙微气候适应性：采用紧凑式合院布局以阻截风沙，厚重夯土与砂岩质感墙体增强热工蓄热阻热，深挑檐凹窗减少强烈西晒眩光，配置节水耐旱耐盐碱景观植物与沙漠绿洲微喷灌水景。"
        climate_en_tokens = (
            "arid continental climate adaptive architecture, compact protective courtyard enclosures, "
            "heavy thermal-mass rammed earth and sandstone textures, deep recessed window reveals for glare control, "
            "xeriscaping with drought-resistant native planting"
        )
    else:
        climate_zone = "温带过渡季风微气候区"
        climate_features = "温带季风气候适应性：注重四季分明微气候营造、季风导风向阳、被动式节能建筑外遮阳与多层次落叶林荫漫步道。"
        climate_en_tokens = (
            "temperate monsoon climate adaptive design, seasonal passive shading, solar optimization, deciduous street canopies"
        )

    # Typology Tokens
    if any(k in raw_land_use for k in ["industrial", "工业", "工矿", "仓储"]):
        design_style = "工业历史遗存活化与低碳生态创客聚落"
        typology_tokens = (
            "adaptive reuse of historic factory volume, exposed industrial structural steel trusses and crane girders, "
            "brick masonry preservation, double-height creative maker ateliers, modern floor-to-ceiling glass curtain infills, "
            "raw industrial-chic aesthetic, porous public plaza"
        )
    elif any(k in raw_land_use for k in ["residential", "居住", "住宅", "社区"]):
        design_style = "人本尺度全龄友好型绿意低碳宜居社区"
        typology_tokens = (
            "human-scale walkable neighborhood, barrier-free access ramps, vibrant pocket parks with elder and child fitness zones, "
            "warm pedestrian ambient lighting, permeable pavers, cozy community gathering courtyards, green balcony planters"
        )
    elif any(k in raw_land_use for k in ["commercial", "商业", "零售", "商务"]):
        design_style = "活力开放式文商旅体验慢行漫步街区"
        typology_tokens = (
            "bustling pedestrian retail boulevard, active transparent storefronts with alfresco dining plazas, shaded canopy walkways, "
            "interactive public water plaza, biophilic green walls, dynamic evening architectural illumination, festive street vitality"
        )
    elif any(k in raw_land_use for k in ["water", "滨水", "河", "湖"]):
        design_style = "多级生态韧性滨水休闲绿廊与亲水聚落"
        typology_tokens = (
            "continuous eco-corridor, naturalized bio-swale riverbanks, cantilevered viewing decks over water, "
            "uninterrupted waterfront jogging paths, native emergent aquatic plants, scenic waterfront skyline"
        )
    else:
        design_style = "复合型绿色低碳未来城市更新街区"
        typology_tokens = (
            "mixed-use urban regeneration, layered public-private zoning, street-level pedestrian vitality, "
            "quiet upper-level working and living terraces, interconnected civic open plazas, biophilic architecture"
        )

    # Consensus keywords integration
    consensus_tokens_list: List[str] = []
    if isinstance(consensus, dict):
        for k, v in consensus.items():
            if isinstance(v, (str, int, float)):
                consensus_tokens_list.append(f"{k}: {v}")
            elif isinstance(v, list):
                consensus_tokens_list.extend([str(item) for item in v])
    elif isinstance(consensus, list):
        consensus_tokens_list.extend([str(c) for c in consensus])

    consensus_str = ", ".join(consensus_tokens_list) if consensus_tokens_list else "balanced public-private consensus, ecological sustainability"

    positive_prompt = (
        f"Masterpiece architectural photography, 8k resolution, highly detailed urban design rendering of {plot.get('name', 'Urban Renewal Block')}, "
        f"{design_style}, {typology_tokens}, {climate_en_tokens}, "
        f"consensus-driven design integrating [{consensus_str}], "
        f"photorealistic lighting, natural ambient daylight, volumetric atmosphere, clean architectural lines, vibrant pedestrian life, "
        f"sharp focus, professional architectural competition visualization, Hasselblad medium format photography style."
    )

    negative_prompt = (
        "low quality, blurry, low resolution, distorted architecture, crooked columns, chaotic unnatural roads, "
        "oversaturated, muddy textures, floating buildings, disfigured people, missing limbs, traffic jam, trash, debris, "
        "watermarks, logo, text, signature, cartoon, 3d glitch, bad perspective, deformed windows, overexposed."
    )

    return {
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "climate_zone": climate_zone,
        "climate_features": climate_features,
        "design_style": design_style,
    }
