import io
import os
import shutil
import traceback
from pathlib import Path

import streamlit as st
from PIL import Image

from src.stages.common.workspace import render_stage_workspace
from src.stages.stage13_outputs.config import STAGE13_WORKSPACE
from src.ui.app_shell import (
    render_logic_chain_stepper,
    render_top_nav,
)
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.module_summary import render_stage_summary
from src.ui.persistent_outputs import register_document_output, register_report_output
from src.ui.streamlit_compat import stretch_width
from src.workflow.stage_data_bus import load_stage_output, render_evidence_chain_bar
from src.workflow.stage_keys import SK

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render_page() -> None:
    render_top_nav()

    render_page_banner(
        title="成果表达",
        description="全新工作流：1. Python 代码绘制空间规划矢量底图 -> 2. 自动化标准 A3 图框与规划指标信息卡封装。",
        eyebrow="Stage 13",
        tags=["规划图纸代码生成", "图册自动组装", "标准图签封装"],
    )
    render_evidence_chain_bar("13", ["10", "11", "12", "13"])

    active = render_stage_workspace(STAGE13_WORKSPACE)
    selected_sub = active.label
    st.markdown("---")

    ROOT = PROJECT_ROOT

    if selected_sub == "🗺️ 规划图纸代码生成":
        render_section_intro(
            "数据底图代码绘制中心",
            "使用 Python 直接从 GIS 空间数据库中进行代码绘图，绘制纯色块、线稿的高精度矢量规划底图。",
            eyebrow="Step 1: Python Maps",
        )
        st.info("此模块调用 `scripts/export_high_precision_gis.py` 基于真实的空间数据（道路、建筑、水系）进行代码绘图。")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🚀 一键运行代码绘制所有空间底图", type="primary", **stretch_width(st.button)):
                with st.spinner("正在启动 Python 空间绘图引擎..."):
                    import subprocess
                    import sys
                    script_path = ROOT / "scripts" / "export_high_precision_gis.py"
                    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, encoding="utf-8")
                    if res.returncode == 0:
                        st.success("高精度空间底图绘制完毕！存放在 `output/high_precision/` 目录中。")
                    else:
                        st.error(f"绘制失败：\n{res.stderr}")
                        
    elif selected_sub == "🖼️ 图册自动组装":
        render_section_intro(
            "图册自动组装中心",
            "直接基于真实 GIS 数据运行 Python 代码进行绘图，并自动组合 A3 标准图框、图例与规划说明卡片。",
            eyebrow="Step 2: Atlas Composer",
        )
        
        col_ctrl, col_view = st.columns([1, 1.2])
        
        with col_ctrl:
            st.markdown("### 1. 图册基础配置")
            
            # Map drawing types to codes
            drawing_type_to_code = {
                "现状区位图": "DR-004",
                "研究范围图": "DR-005",
                "卫星图": "DR-010",
                "土地利用现状图": "DR-011",
                "交通分析图": "DR-012",
                "建筑高度现状图": "DR-013",
                "建筑风貌现状图": "DR-014",
                "环境品质问题地图": "DR-015",
                "历史建筑与工业遗产分布图": "DR-017",
                "遗产价值评估热力图": "DR-019",
                "空间句法可达性分析图": "DR-022",
                "更新模式分区图": "DR-035",
                "空间结构规划图": "DR-036",
                "用地规划图": "DR-037",
                "建筑更新控制图": "DR-041",
                "建筑高度控制图": "DR-042",
                "道路交通系统规划图": "DR-043",
                "慢行系统规划图": "DR-044",
                "公共空间系统图": "DR-045",
                "绿地景观系统图": "DR-046",
                "历史文化展示系统图": "DR-047",
                "AIGC技术推演过程图": "DR-059",
                "实施分期图": "DR-060",
            }
            
            drawing_type_to_title = {
                "现状区位图": "现状区位图",
                "研究范围图": "研究范围图",
                "卫星图": "数据来源与遥感现状图",
                "土地利用现状图": "用地现状分析图",
                "交通分析图": "道路交通现状图",
                "建筑高度现状图": "建筑高度现状图",
                "建筑风貌现状图": "建筑风貌识别图",
                "环境品质问题地图": "环境品质问题地图",
                "历史建筑与工业遗产分布图": "历史建筑与工业遗产分布图",
                "遗产价值评估热力图": "遗产价值评估热力图",
                "空间句法可达性分析图": "空间句法可达性分析图",
                "更新模式分区图": "更新模式分区图",
                "空间结构规划图": "空间结构规划图",
                "用地规划图": "用地规划图",
                "建筑更新控制图": "建筑更新控制图",
                "建筑高度控制图": "建筑高度控制图",
                "道路交通系统规划图": "道路交通系统规划图",
                "慢行系统规划图": "慢行系统规划图",
                "公共空间系统图": "公共空间系统图",
                "绿地景观系统图": "绿地景观系统图",
                "历史文化展示系统图": "历史文化展示系统图",
                "AIGC技术推演过程图": "AIGC技术推演过程图",
                "实施分期图": "实施分期图",
            }
            
            drawing_type = st.selectbox("图纸类型 (主绘图区内容)", list(drawing_type_to_code.keys()))
            default_code = drawing_type_to_code.get(drawing_type, "DR-004")
            default_title = drawing_type_to_title.get(drawing_type, drawing_type)
            
            drawing_title = st.text_input("图纸标题", value=default_title)
            drawing_num = st.text_input("图纸编号", value=default_code)
            
            st.markdown("### 2. 设计说明与规划指标")
            
            # Default descriptions helper
            from src.config.site import get_site_config, get_site_name, get_site_city
            s_cfg = get_site_config()
            s_city = get_site_city() or s_cfg.get("city", "当地") or "当地"
            s_name = get_site_name() or s_cfg.get("name", "更新规划单元") or "更新规划单元"
            s_area = s_cfg.get("area_ha", 160)
            t_plot = load_stage_output("04", "target_plot", {}) or load_stage_output("07", "target_plot", {})
            t_name = t_plot.get("name", f"{s_name}重点更新地块")
            landmarks = get_landmarks()
            primary_lm = landmarks[0].get("name") if (landmarks and isinstance(landmarks[0], dict) and landmarks[0].get("name")) else f"{s_name}核心风貌区"

            default_desc = {
                "现状区位图": [
                    f"1. 地理区位：本项目位于{s_city}{s_name}核心街区，是承载历史风貌传承与现代活力提升的关键纽带地带。",
                    f"2. 规划范围：规划研究范围覆盖{s_name}及周边街区，总研究面积约 {s_area} 公顷，包含重点更新单元。",
                    f"3. 指标现状：现状建筑密度约35-45%，水绿覆盖率与慢行连续度有待提升，规划定位为因地制宜的高品质存量更新示范街区。"
                ],
                "研究范围图": [
                    f"1. 核心范围：规划确定的更新改造研究边界覆盖{s_name}，总用地面积约为 {s_area} 公顷。",
                    f"2. 重点地块：规划重点针对片区内低效存量资产地块进行城市设计与活力针灸，优先锁定【{t_name}】示范地块。",
                    f"3. 现状本底：周边路网成熟，承接城市交通与公共活力脉络，是缝合周边城市功能割裂的关键空间锁扣。"
                ],
                "卫星图": [
                    f"1. 遥感影像：本图底图采用高分辨率卫星遥感影像，直观反映项目所在{s_city}{s_name}周边区域的真实地表覆盖与建筑空间密度。",
                    f"2. 蓝绿肌理：周边生态水绿本底存在空间碎片化，街区内部绿色开敞空间较少，亟需见缝插针织补更多社区口袋公园。",
                    f"3. 建设状况：街区内现状以中低层高密度建筑群为主，局部存在低效闲置工业或仓储遗存，空间肌理需针灸式织补。"
                ],
                "土地利用现状图": [
                    f"1. 用地构成：{s_city}{s_name}项目区内以居住用地（R）和商业服务业设施用地（B）为主，工业与仓储用地多属需更新低效存量。",
                    f"2. 混合利用：规划提倡在重点更新地段发展商住混合、文创混合等多功能混合用地（M），以提升地块经济与社会活力。",
                    f"3. 用地优化：通过盘活现状低效建设用地，增加公共服务设施用地（A）与绿地广场用地（G），改善居民15分钟生活圈设施供给品质。"
                ],
                "建筑高度现状图": [
                    f"1. 高度特征：区内建筑以低层（1-3层）和多层（4-7层）为主，空间肌理紧凑，尺度宜人。",
                    f"2. 高层分布：中高层与高层建筑主要零散分布在区位外围，对核心区及{primary_lm}周边产生了一定的视线廊道压力。",
                    f"3. 管控思路：规划提出结合视线敏感度分析，严格控制核心区新建建筑高度，禁止插建超高建筑，保留原有舒缓天际线。"
                ],
                "建筑风貌现状图": [
                    f"1. 风貌构成：区内历史保护与特色风貌集中在{primary_lm}周边；普通居住与商业风貌占主导，整体风貌协调度有待提升。",
                    f"2. 界面杂乱：局部街区存在杂乱搭接及立面风貌破损，削弱了街区空间质量与文化氛围，缺乏统一的导则引导。",
                    f"3. 整治策略：实行分类整治，对保护建筑修缮复原，对普通建筑立面进行微改造协调，消除风貌冲突，营造和谐共振街区。"
                ],
                "历史建筑与工业遗产分布图": [
                    f"1. 遗产识别：片区内包含以{primary_lm}为核心的历史文化建筑群及存量工业建筑遗存，是复合型城市遗产的关键载体。",
                    f"2. 价值评估：核心风貌保护区与工业遗存具有极高的建筑质量和空间识别度，是本次更新设计中严格执行“保留与修缮”的刚性管控区域。",
                    f"3. 活化思路：保护传统街区肌理与风貌界面的连续性，打通文化展示游线，将工业遗存置换为文创、博览与青年双创等活力复合功能。"
                ],
                "交通分析图": [
                    f"1. 骨架路网：规划区内以城市主干路网为主，对外联通良好，但局部干道或高架对两侧街区存在一定的物理与视线割裂作用。",
                    f"2. 交通阻隔：外部铁路或快速干道横穿，对地块形成部分通行阻隔。规划建议在更新改造中，增设人行立体天桥或地下通道以缝合城市片区。",
                    f"3. 慢行慢游：现状支路网密度偏低且不成系统，慢行体验较差。规划提出通过微循环道路改造和TOD联动，构建高品质、步行友好的慢游交通环线。"
                ],
                "空间句法可达性分析图": [
                    f"1. 全局整合：基于路网拓扑分析发现，外围主干路网具有较高的全局可达性，构成了研究范围对外的车行主通道。",
                    f"2. 慢行渗透：街区内部由于支路网密度偏低、存在交通割裂，整合度表现出空间凹陷，步行可达性较弱，亟需细化微循环。",
                    f"3. 空间协同：协同度散点图拟合显示核心区与全域存在局部脱节，说明该地块在人流疏导与慢行连通上存在一定的孤岛效应。"
                ],
                "环境品质问题地图": [
                    f"1. 噪声干扰：干道交通与外部走廊对两侧街区产生声环境影响，最大噪声带向两侧扩散达80-120米。",
                    f"2. 绿化短板：通过街景图像量化分析发现，老社区内部多段街道的绿视率（GVI）低于15%，空间界面灰色硬质感过强。",
                    f"3. 空间割裂：大体量封闭式地块或围墙阻断了人行路径，导致周边老旧社区内部微循环不畅，慢行系统断档。"
                ],
                "遗产价值评估热力图": [
                    f"1. 价值核心：热力图呈现出显著的价值核心格局，以{primary_lm}历史保护群为绝对的遗产价值红区核心。",
                    f"2. 存量遗存：存量旧厂房及历史文化脉络带构成了次一级的文化脉络带，具有极高的重构与活化开发潜力。",
                    f"3. 空间导向：价值热力衰减直接决定了开发建设的严格风貌敏感区分区，越靠近高热力值点，新建建筑的体量与材质控制越严格。"
                ],
                "更新模式分区图": [
                    f"1. 保护修缮：针对以{primary_lm}为代表的历史风貌建筑，执行原地原风貌修缮，划定绝对保护红线，禁止任何形式的加建与插建高层。",
                    f"2. 整治提升：对风貌过渡区的老旧公建及沿街界面，统一立面风貌导则，拆除杂乱违建，使建筑色调、材质与历史保护区协调。",
                    f"3. 置换与微更新：对低效工业与商业存量进行功能重组与置换，置换为青年文创与生活服务；对老社区实施微改造，盘活边角地增加活动场地。"
                ],
                "空间结构规划图": [
                    f"1. 规划结构：形成“一核、双轴、多组团”的总体更新规划结构。一核指文化活力共振核，双轴为交通联动轴与生态延伸轴。",
                    f"2. 联动轴线：打通交通枢纽至{primary_lm}的空间轴线，利用高品质慢行商业街与视觉廊道建立两者的物理与文化强关联。",
                    f"3. 节点触媒：以多处更新活力节点为针灸触点，激活周边消极的街区本底，促进历史风貌区与现代化城市的无缝衔接。"
                ],
                "用地规划图": [
                    f"1. 规划布局：商业与文创混合区沿主要活力界面布置；老旧社区内部主要进行绿化修补与微更新，维持宜人肌理。",
                    f"2. 密路网：地块内规划小街区密路网（3.5-6米宽人行步行街/支路），将大尺度街区切碎，极大提升空间可渗透性。",
                    f"3. 景观骨架：构建环核心区的绿色开敞环线，并与生态公园绿带无缝对接，实现蓝绿网络与城市空间融合。"
                ],
                "建筑高度控制图": [
                    f"1. 核心高度：{primary_lm}周边绝对控制区内，新建建筑限高9-12米，保持原有舒缓平滑的空间天际线。",
                    f"2. 风貌协调：风貌过渡区内限高18-24米，新建建筑宜为4-6层，以多层及连续坡屋顶形式为主。",
                    f"3. 活力开发：外围城市区域限高24-36米，支持局部地块进行适当的高效率活力功能开发。"
                ],
                "建筑更新控制图": [
                    f"1. 保护修缮：对历史风貌建筑坚持最小干预，保留建筑原始结构与外墙肌理，严格控制周边景观小品色调以防风貌退化。",
                    f"2. 保留整治：对普通居住建筑以立面整治、增加外保温及整理管线为主，不破坏原格局，实施渐进式微更新。",
                    f"3. 功能置换：对大跨度存量厂房与仓储空间进行结构加固与重组，置换为高附加值的文创展厅、艺术沙龙与科技孵化园。"
                ],
                "道路交通系统规划图": [
                    f"1. 路网骨架：规划形成协同顺畅的主次干路网骨架，提升地块对外的交通联系和连通度，实现内外交通的顺畅转换。",
                    f"2. 慢行慢游：加密内部支路网，优化慢行步道，提升街区可达性，建立对行人与自行车慢行友好的漫游系统，打通微循环瓶颈。",
                    f"3. TOD 开发：依托紧邻交通枢纽与轨道站点，规划强化TOD导向型开发，引导高密度、功能混合与人流聚集。"
                ],
                "慢行系统规划图": [
                    f"1. 漫游步道：规划串联{primary_lm}、工业遗存与生态景观的文旅慢行大环线，串联沿线核心活力节点。",
                    f"2. 绿道骑行：沿滨水生态廊道及道路边界布置林荫骑行专用车道，支持共享单车与绿色健康通勤，实现人车分流安全出行。",
                    f"3. 邻里步行：老旧住宅区内增设“邻里漫步小径”，结合口袋公园布置健身设施，完善居民5分钟步行微系统。"
                ],
                "公共空间系统图": [
                    f"1. 广场节点：在{primary_lm}周边及存量改造核心区规划文化景观广场，作为城市公共活动与旅游集散的复合载体。",
                    f"2. 口袋公园：见缝插针地在居住社区内部增设多处口袋公园，确保规划区实现“300米见绿、500米见园”的服务全覆盖。",
                    f"3. 服务缓冲：为每个口袋公园划定300米服务半径分析缓冲，精准织补覆盖盲区，大幅度提升整体公共绿地均等化。"
                ],
                "绿地景观系统图": [
                    f"1. 蓝绿框架：以周边生态廊道为骨架，通过水廊与绿带将大自然引入地块深处，形成蓝绿交织的城市生态基底。",
                    f"2. 景观节点：打造核心景观广场、遗存绿地等多处景观核心节点，并对道路绿化带进行林荫化改造提升视觉体验。",
                    f"3. 织补更新：通过小微绿地口袋公园和垂直绿化织补消极灰色空间，大幅提高绿视率，实现生态宜居的城市微更新目标。"
                ],
                "历史文化展示系统图": [
                    f"1. 展示路径：以风貌核心保护区为基础，构建历史文脉游赏展示路径，采用统一的标识系统与导游导视指引系统。",
                    f"2. 遗产标示：在{primary_lm}、存量遗存等关键节点设立金属文化浮雕碑与解说板，形成“露天博物馆”体验。",
                    f"3. 视廊保护：严格保护从交通门户眺望{primary_lm}的风貌视线走廊，走廊范围内禁止超高体量阻挡与不协调色彩。"
                ],
                "AIGC技术推演过程图": [
                    "1. 数据底座：利用多源 GIS 空间图层与高分辨率街景图像建立数字底盘，通过 NLP 挖掘社交媒介情感，诊断品质痛点。",
                    "2. AIGC 生成：利用 Stable Diffusion 算法配合 ControlNet 控制网，输入手绘线稿、空间意向与提示词，自动推演 100+ 方案。",
                    "3. 智能协商：通过 LLM 智能体模拟政府、专家、居民与开发商进行决策协商，综合评选最优方案，实现全链条数字化辅助。"
                ],
                "实施分期图": [
                    f"1. 近期建设（1-3年）：优先启动【{t_name}】示范更新地块，置换低效空间并配建便民服务与慢行微循环以激活人流。",
                    "2. 中期推进（3-5年）：推进存量工业或公共空间活化项目，改建为数智文创街区，并缝合被交通阻断的路网。",
                    "3. 远期展望（5-10年）：实施周边关联片区低效用地微更新项目，全面完成全区公共绿地与设施配套。"
                ]
            }
            
            # AI generation button (DesignContext)
            if st.button("🧠 AI 智能编写说明与指标 (基于大模型)", **stretch_width(st.button)):
                with st.spinner("AI 正在结合设计纲要编写说明文字..."):
                    from src.engines.llm_engine import call_llm_engine
                    from src.workflow.design_context import build_design_context
                    ctx = build_design_context()
                    brief = ctx.design_brief or ctx.get_summary(1500)
                    sys_p = "你是一个顶级城市规划师。请为城市设计图纸编写三条精简专业的设计说明（每条50字以内），必须引用具体数据和策略依据。"
                    prompt_p = "请结合以下设计纲要，为图纸「" + drawing_type + "」（标题：「" + drawing_title + "」）编写三条专业的规划说明与指标，以1. 2. 3.的格式输出。\n\n设计纲要：\n" + brief[:1500]
                    res = call_llm_engine(prompt_p, sys_p)
                    # Parse the result into lines
                    lines = [line.strip() for line in res.split('\n') if line.strip() and (line.strip().startswith(('1', '2', '3', '一', '二', '三')) or len(line.strip()) > 10)]
                    # Pad or truncate
                    while len(lines) < 3:
                        lines.append(f"{len(lines)+1}. [补充指标]：请在此处输入您的规划设计内容。")
                    st.session_state[f"p13_desc_{drawing_type}"] = lines[:3]
                    st.success("AI 说明生成成功！")
            
            # Load from session state or default
            current_desc = st.session_state.get(f"p13_desc_{drawing_type}", default_desc.get(drawing_type, ["", "", ""]))
            
            desc_1 = st.text_input("说明第 1 条", value=current_desc[0])
            desc_2 = st.text_input("说明第 2 条", value=current_desc[1])
            desc_3 = st.text_input("说明第 3 条", value=current_desc[2])
            
            st.markdown("### 3. 图签与图例基本信息")
            from src.config.site import get_author_info, get_institution_info
            _cfg_author = get_author_info()
            _cfg_inst = get_institution_info()
            _default_org = f"{_cfg_inst.get('name', '')}\n{_cfg_inst.get('department', '')}".strip()
            author = st.text_input("制作人", value=_cfg_author.get("name", ""), placeholder="请输入姓名")
            author_id = st.text_input("编号", value=_cfg_author.get("id", ""), placeholder="请输入编号")
            organization = st.text_area("单位/部门", value=_default_org, height=60)
            
            if st.button("🎨 一键代码绘图并组装图纸", type="primary", **stretch_width(st.button)):
                with st.spinner("Python 代码绘图与排版卡片组装中..."):
                    import os
                    import tempfile

                    from tools.draw_scope_map import draw_spatial_map, process_a3_layout
                    
                    temp_fd, temp_map = tempfile.mkstemp(suffix=".png")
                    os.close(temp_fd)
                    
                    output_file_name = f"{drawing_num}_{drawing_title}.png"
                    output_file_path = ROOT / "static" / "atlas" / output_file_name
                    
                    try:
                        # 1. 运行代码绘制主图
                        view_w = draw_spatial_map(temp_map, drawing_type=drawing_type)
                        
                        # 2. 合成 A3 图纸、图例与说明
                        from tools.draw_scope_map import get_drawing_module
                        module = get_drawing_module(drawing_type)
                        has_no_frame = (module is not None and getattr(module, "NO_FRAME", False))
                        
                        if has_no_frame:
                            img = Image.open(temp_map)
                            img_resized = img.resize((2240, 1584), Image.Resampling.LANCZOS)
                            img_resized.save(str(output_file_path))
                        else:
                            process_a3_layout(
                                map_path=temp_map,
                                output_path=str(output_file_path),
                                view_w=view_w,
                                drawing_type=drawing_type,
                                title=drawing_title,
                                description_lines=[desc_1, desc_2, desc_3],
                                drawing_number=drawing_num,
                                author=author,
                                author_id=author_id,
                                organization=organization
                            )
                        
                        # 记录文件以供预览
                        st.session_state["p13_latest_rendered"] = str(output_file_path)
                        st.session_state["p13_latest_filename"] = output_file_name
                        st.success(f"🎉 绘图成功！图纸已保存至 static/atlas/{output_file_name}")
                    except Exception as e:
                        st.error(f"代码绘图排版失败：{e}")
                        import traceback
                        st.code(traceback.format_exc())
                    finally:
                        if os.path.exists(temp_map):
                            os.remove(temp_map)
                            
        with col_view:
            st.markdown("### 图纸实时绘制预览")
            latest_rendered = st.session_state.get("p13_latest_rendered")
            if latest_rendered and os.path.exists(latest_rendered):
                with open(latest_rendered, "rb") as f:
                    btn_bytes = f.read()
                
                # Show image
                st.image(latest_rendered, caption=st.session_state.get("p13_latest_filename"), use_container_width=True)
                
                st.download_button(
                    "📥 下载高清 A3 图纸 (PNG)",
                    btn_bytes,
                    file_name=st.session_state.get("p13_latest_filename"),
                    mime="image/png",
                    **stretch_width(st.download_button)
                )
            else:
                st.info("👈 请在左侧配置完成后，点击“一键代码绘图并组装图纸”生成预览图。")
                
                # Show an existing demo drawing if available
                demo_path = ROOT / "static" / "research_scope_2d.png"
                if demo_path.exists():
                    st.markdown("**示例参考图 (现状区位图)：**")
                    st.image(str(demo_path), use_container_width=True)

    elif selected_sub == "📤 文档导出":
        render_section_intro(
            "全案成果与工程矢量图纸导出",
            "国家标准 GB/T 城乡规划制图标准图层规范 · AutoCAD 2000 (AC1015) 纯 ASCII 矢量输出 · 米制 1:1 坐标体系 · 中文 ANSI_936 防乱码编码 · 全套法定导则与设计报告成果。",
            eyebrow="Deliverables Hub",
        )

        target_plot = load_stage_output("04", "target_plot", {}) or load_stage_output("07", "target_plot", {})
        from src.config.site import get_site_config, get_site_name, get_site_city
        s_cfg = get_site_config()
        s_name = get_site_name() or s_cfg.get("name", "示范重点片区") or "示范重点片区"
        target_name = target_plot.get("name", f"{s_name}首选更新单元")
        target_mpi = target_plot.get("mpi", 85.0)
        target_priority = target_plot.get("priority", "P1 优先更新")
        t_issues = target_plot.get("issues", [])
        issues_summary = "、".join(t_issues[:3]) if t_issues else "功能低效闲置、微循环不畅、公共空间品质不足"

        brief_text = load_stage_output("07", SK.DESIGN_BRIEF, "")
        consensus_text = brief_text[:80] + "..." if brief_text else "因地制宜空间织补、完善公服配套、严守控规底线"

        # ── 1. 端到端全业务推演链路全息看板 ──
        st.markdown("### 🔗 端到端全业务逻辑链闭环全景看板")
        st.caption("从 Stage 04 靶向诊断至 Stage 13 矢量交付，全流程业务数据总线完全贯通。")

        chain_cols = st.columns(5)
        with chain_cols[0]:
            with st.container(border=True):
                st.markdown("🎯 **Stage 04 全息诊断**")
                st.markdown(f"**靶向地块：** {target_name}")
                st.caption(f"MPI: {target_mpi} · {target_priority}")
                st.caption(f"诊断短板：{issues_summary}")
        with chain_cols[1]:
            with st.container(border=True):
                st.markdown("🤝 **Stage 07 多主体博弈**")
                st.markdown("**设计纲要共识**")
                st.caption("居民/使用者 · 投资/运营 · 规划/法定义务人")
                st.caption(f"共识：{consensus_text}")
        with chain_cols[2]:
            with st.container(border=True):
                st.markdown("🗺️ **Stage 08 空间结构**")
                st.markdown("**总体空间结构**")
                st.caption("一核两轴多片多节点")
                st.caption(f"以【{target_name}】为针灸触媒节点，辐射带动周边更新")
        with chain_cols[3]:
            with st.container(border=True):
                st.markdown("🏗️ **Stage 10/12 深化与导则**")
                st.markdown("**控规指标与导则**")
                st.caption(f"FAR ≤ {target_plot.get('far_max', 1.4)} · 密度 ≤ {target_plot.get('density_max', 35)}% · 限高 ≤ {target_plot.get('height_max', 18)}m")
                st.caption("9大章节法定导则严格约束空间形态与风貌指标")
        with chain_cols[4]:
            with st.container(border=True):
                st.markdown("📐 **Stage 13 矢量交付**")
                st.markdown("**AutoCAD 2000 DXF**")
                st.caption("GB/T 规划图层规范 5 层")
                st.caption("1:1 米制投影，可直接指导施工图与法定报批")

        st.markdown("---")

        # ── 2. AutoCAD DXF 矢量工程图纸导出 ──
        st.markdown("### 📐 AutoCAD 2000 DXF 矢量工程图纸导出")
        st.caption("基于 GB/T 城乡规划制图标准图层规范（01_BOUNDARY, 02_EXISTING_BLDG, 03_PROPOSED_BLDG, 04_ROAD_CENTER, 05_GREEN_SPACE）。")

        render_summary_cards([
            {"value": "01_BOUNDARY", "title": "规划红线图层", "desc": "ACI 1 红色 (RGB 255,0,0) · 研究范围闭合多边形"},
            {"value": "02_EXISTING_BLDG", "title": "保留现状建筑", "desc": "ACI 8 浅灰 (RGB 200,200,200) · 现状建筑基底"},
            {"value": "03_PROPOSED_BLDG", "title": "更新示范建筑", "desc": "ACI 2 暖黄 (RGB 255,215,0) · 靶向地块更新方案"},
            {"value": "04_ROAD_CENTER", "title": "道路交通中心线", "desc": "ACI 5 蓝色 (RGB 30,144,255) · 拓扑连通轴线"},
            {"value": "05_GREEN_SPACE", "title": "公园绿地景观", "desc": "ACI 3 绿色 (RGB 34,139,34) · 伊通河滨水生态绿网"},
        ])

        st.markdown("<br>", unsafe_allow_html=True)

        col_exec, col_info = st.columns([1.2, 1])
        with col_exec:
            target_crs = st.selectbox(
                "坐标投影系统",
                ["CGCS2000 / 3度分带 38度 (EPSG:4526, 米制)", "WGS 84 / Pseudo-Mercator (EPSG:3857, 米制)", "原始经纬度 (EPSG:4326)"],
                index=0,
                key="p13_cad_crs",
            )
            from src.config.site import get_site_name, get_site_center
            from src.engines.context_adaptive_engine import get_utm_epsg_for_coordinates
            site_name = get_site_name() or "城市更新示范区"
            site_center = get_site_center() or [125.34064, 43.90095]
            auto_epsg = get_utm_epsg_for_coordinates(site_center[0], site_center[1])
            crs_code = f"EPSG:{auto_epsg}" if ("米制" in target_crs or "UTM" in target_crs) else ("EPSG:4526" if "4526" in target_crs else None)

            if st.button("📐 一键生成 AutoCAD DXF 矢量图纸", type="primary", key="btn_gen_cad_dxf", **stretch_width(st.button)):
                with st.spinner("正在加载 GIS 空间图层并构建标准 AutoCAD DXF (AC1015)..."):
                    try:
                        import geopandas as gpd
                        from src.config import GIS_FILES, resolve_path
                        from src.utils.vector_exporter import export_multi_layer_dxf

                        cad_dir = ROOT / "output" / "cad"
                        cad_dir.mkdir(parents=True, exist_ok=True)
                        dxf_file = cad_dir / "statutory_plan.dxf"

                        layers_dict = {}

                        # 1. 规划边界
                        b_path = resolve_path(str(GIS_FILES["boundary"]))
                        if b_path.exists():
                            gdf_b = gpd.read_file(str(b_path))
                            layers_dict["01_BOUNDARY"] = gdf_b

                        # 2. 现状建筑
                        bldg_path = resolve_path(str(GIS_FILES["buildings"]))
                        if bldg_path.exists():
                            gdf_bldg = gpd.read_file(str(bldg_path))
                            layers_dict["02_EXISTING_BLDG"] = gdf_bldg

                        # 3. 重点更新建筑 / 靶向地块
                        plots_path = resolve_path(str(GIS_FILES["plots"]))
                        if plots_path.exists():
                            gdf_plots = gpd.read_file(str(plots_path))
                            layers_dict["03_PROPOSED_BLDG"] = gdf_plots

                        # 4. 道路拓扑中心线
                        roads_path = resolve_path(str(GIS_FILES["roads"]))
                        if roads_path.exists():
                            gdf_roads = gpd.read_file(str(roads_path))
                            layers_dict["04_ROAD_CENTER"] = gdf_roads

                        # 5. 公园绿地
                        landuse_path = resolve_path(str(GIS_FILES["landuse"]))
                        if landuse_path.exists():
                            gdf_lu = gpd.read_file(str(landuse_path))
                            gdf_green = gdf_lu[gdf_lu["Type"].str.contains("绿地|公园|景观", na=False)] if "Type" in gdf_lu.columns else gdf_lu.head(5)
                            if not gdf_green.empty:
                                layers_dict["05_GREEN_SPACE"] = gdf_green

                        out_path = export_multi_layer_dxf(
                            gdfs=layers_dict,
                            output_dxf_path=str(dxf_file),
                            to_metric=True,
                            target_crs=crs_code,
                        )

                        st.session_state["p13_cad_dxf_ready"] = str(out_path)
                        st.session_state["p13_cad_layer_count"] = len(layers_dict)
                        st.success(f"🎉 AutoCAD DXF 矢量工程图纸导出成功！包含 {len(layers_dict)} 个国家标准图层。")
                    except Exception as e:
                        st.error(f"DXF 导出失败：{e}")
                        import traceback
                        st.code(traceback.format_exc())

            cad_dxf_ready = st.session_state.get("p13_cad_dxf_ready")
            if cad_dxf_ready and os.path.exists(cad_dxf_ready):
                with open(cad_dxf_ready, "rb") as f_dxf:
                    dxf_bytes = f_dxf.read()
                file_size_kb = len(dxf_bytes) / 1024.0
                st.success(f"✅ 图纸已就绪：`statutory_plan.dxf`（文件大小：{file_size_kb:.1f} KB）")
                st.download_button(
                    label="📥 下载 AutoCAD DXF 矢量工程图纸 (.dxf)",
                    data=dxf_bytes,
                    file_name=f"{site_name}_法定规划图纸_AC1015.dxf",
                    mime="application/dxf",
                    **stretch_width(st.download_button)
                )

        with col_info:
            st.markdown("### 🛠️ 导出技术规范对账")
            st.markdown(
                """
                - **CAD 规格版本：** AutoCAD 2000 / AC1015 标准规范；
                - **编码格式：** ANSI_936 (GBK) 纯 ASCII 配对组码，杜绝天正建筑与 AutoCAD 中文乱码；
                - **图元支持：** `LWPOLYLINE` (二维轻量多段线)、`POINT`、`TEXT` 严格成对配对；
                - **工程尺度：** 1:1 真实米制世界坐标系，载入 CAD 后可直接进行距离标注与面积测量。
                """
            )

        st.markdown("---")

        # ── 3. 全套法定设计文本与报告成果导出 ──
        st.markdown("### 📄 全案规划文本与法定导则导出")
        render_section_intro("全案文档导出", "导出前期分析诊断、总体设计导则以及全阶段生成汇总报告文本。", eyebrow="Document Export")

        col1, col2, col3 = st.columns(3)
        with col1:
            guideline = load_stage_output("12", SK.DESIGN_GUIDELINE, "")
            if guideline:
                register_report_output(
                    label="城市设计导则",
                    content=guideline,
                    stage_code="12",
                    key="design_guideline",
                )
                st.download_button("📥 下载城市设计导则 (Markdown)", guideline, file_name="城市设计导则.md", **stretch_width(st.download_button))
            else:
                st.info("暂无导则数据，请在 Stage 12 生成。")

        with col2:
            diagnosis = load_stage_output("05", SK.DIAGNOSIS_REPORT, "")
            if diagnosis:
                register_report_output(
                    label="前期诊断报告",
                    content=diagnosis,
                    stage_code="05",
                    key="diagnosis_report",
                )
                st.download_button("📥 下载前期诊断报告 (Markdown)", diagnosis, file_name="诊断报告.md", **stretch_width(st.download_button))
            else:
                st.info("暂无诊断数据，请在 Stage 05 生成。")

        with col3:
            report_file_path = ROOT / "output" / "stage_generation_report.md"
            if report_file_path.exists():
                try:
                    with open(report_file_path, "r", encoding="utf-8") as f:
                        report_content = f.read()
                    register_report_output(
                        label="全阶段生成汇总报告",
                        content=report_content,
                        stage_code="13",
                        key="stage_generation_report",
                    )
                    st.download_button(
                        "📥 下载全阶段生成汇总报告 (Markdown)",
                        report_content,
                        file_name="全阶段生成汇总报告.md",
                        **stretch_width(st.download_button)
                    )
                except Exception as e:
                    st.error(f"读取全阶段汇总报告失败：{e}")
            else:
                st.info("暂无汇总报告，请先运行其他阶段的生成模块以生成本底数据。")

        # Row 2: 设计纲要, 设计策略矩阵
        col4, col5 = st.columns(2)
        with col4:
            design_brief = load_stage_output("07", SK.DESIGN_BRIEF, "")
            if design_brief:
                register_report_output(
                    label="设计纲要",
                    content=design_brief,
                    stage_code="07",
                    key="design_brief",
                )
                st.download_button("📥 下载设计纲要 (Markdown)", design_brief, file_name="设计纲要.md", **stretch_width(st.download_button))
            else:
                st.info("暂无设计纲要数据。")
                if st.button("⚡ 立即从上下文自动合成设计简报", key="btn_s13_auto_brief", **stretch_width(st.button)):
                    with st.spinner("正在从全域规划上下文自动合成设计简报..."):
                        try:
                            from src.workflow.design_context import ensure_design_brief
                            brief_res = ensure_design_brief(force=True)
                            if brief_res:
                                st.success("✅ 设计简报已成功合成并持久化！")
                                st.rerun()
                            else:
                                st.warning("当前上下文信息不足，建议先运行前期规划推演。")
                        except Exception as e:
                            st.error(f"合成设计简报失败: {e}")

        with col5:
            strategy_matrix = load_stage_output("07", SK.STRATEGY_MATRIX, "")
            if strategy_matrix:
                register_report_output(
                    label="设计策略矩阵",
                    content=strategy_matrix,
                    stage_code="07",
                    key="strategy_matrix",
                )
                st.download_button("📥 下载设计策略矩阵 (Markdown)", strategy_matrix, file_name="设计策略矩阵.md", **stretch_width(st.download_button))
            else:
                st.info("暂无设计策略矩阵数据，请在 Stage 07 生成。")


    elif selected_sub == "📝 项目设计报告":
        render_section_intro(
            "项目设计报告生成",
            "自动汇编各阶段成果为结构化项目设计报告，严格遵循标准章节结构和格式化排版。",
            eyebrow="Project Report Composer",
        )

        from src.engines.document_composer import (
            REPORT_CHAPTERS,
            AuthorInfo,
            assemble_report_docx,
            build_document_context,
            generate_single_section,
        )

        # ── 学生信息 ──
        st.markdown("### 👤 学籍信息")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            author_name = st.text_input("作者姓名", value="", key="report_name", placeholder="请输入姓名")
            author_id = st.text_input("编号", value="", key="report_id", placeholder="请输入学号")
        with col_s2:
            author_reviewer = st.text_input("审核人", value="", key="report_reviewer")
            author_date = st.text_input("完成日期", value="2026年6月", key="report_date")
        with col_s3:
            author_org = st.text_input("单位", value="", key="report_org")
            author_field = st.text_input("方向", value="", key="report_field")

        student = AuthorInfo(
            name=author_name,
            author_id=author_id,
            advisor=author_reviewer,
            college=author_org,
            major=author_field,
            date=author_date,
        )

        st.markdown("---")

        # ══════════════════════════════════════
        # 一键生成管道
        # ══════════════════════════════════════
        st.markdown("### 🚀 一键生成管道")

        from src.engines.document_pipeline import run_full_pipeline, run_light_pipeline

        # ── 降 AI 率选项 ──
        if "report_enable_deai" not in st.session_state:
            st.session_state["report_enable_deai"] = True
        if "report_deai_intensity" not in st.session_state:
            st.session_state["report_deai_intensity"] = 0.7

        col_deai_opt, col_deai_int = st.columns([3, 1])
        with col_deai_opt:
            st.session_state["report_enable_deai"] = st.checkbox(
                "🧬 启用 AI 率优化（降 AIGC 检测率）",
                value=st.session_state["report_enable_deai"],
                help="启用后管道会自动对生成的文本进行降 AI 处理：规则打散 + LLM 风格扰动 + 个人观察注入。可显著降低知网 AIGC 检测率。",
            )
        with col_deai_int:
            if st.session_state["report_enable_deai"]:
                st.session_state["report_deai_intensity"] = st.slider(
                    "处理强度", 0.3, 1.0, st.session_state["report_deai_intensity"], 0.1,
                    help="越高改动越多，AI 痕迹越少，但可能与原文差异越大。建议 0.5-0.7。",
                )

        col_a, col_b = st.columns(2)

        # ── 管道 A: 轻量 ──
        with col_a, st.container(border=True):
            st.markdown("#### ⚡ 轻量管道")
            st.caption("基于各阶段**已生成**的 AI 报告，快速产出设计报告。适用于各阶段已运行过的场景。")
            st.caption("约 36 步 · 预计 1-3 分钟")

            if st.button("🚀 一键生成设计报告（轻量）", key="pipeline_light", type="primary",
                         **stretch_width(st.button)):
                with st.status("轻量管道运行中...", expanded=True) as status:
                    log_lines = []
                    progress_bar = st.progress(0, text="准备中...")

                    def pc(cur, tot, label):
                        progress_bar.progress(cur / tot, text=f"{label} ({cur}/{tot})")

                    def lc(msg):
                        log_lines.append(msg)
                        # 只显示最后 8 行避免刷屏
                        st.text("\n".join(log_lines[-8:]))

                    try:
                        chapters, buf = run_light_pipeline(
                            student=student,
                            progress_callback=pc,
                            log_callback=lc,
                            enable_deai=st.session_state["report_enable_deai"],
                            deai_intensity=st.session_state["report_deai_intensity"],
                        )
                        st.session_state["report_chapters"] = chapters
                        st.session_state["report_docx_buf"] = buf
                        register_document_output(buf, author_name, author_id, chapters)
                        status.update(label="✅ 轻量管道执行完毕！", state="complete")
                    except Exception as e:
                        status.update(label=f"❌ 管道执行失败: {e}", state="error")
                        st.error(traceback.format_exc())

        # ── 管道 B: 全流程 ──
        with col_b, st.container(border=True):
            st.markdown("#### 🔄 全流程管道")
            st.caption("**从零开始**自动生成所有阶段报告，无需任何已有数据。适用于全新项目。")
            st.caption("约 50+ 步 · 50+ 次 LLM 调用 · 预计 5-10 分钟")

            if st.button("🚀 全流程自动生成（从零开始）", key="pipeline_full", type="primary",
                         **stretch_width(st.button)):
                with st.status("全流程管道运行中...", expanded=True) as status:
                    log_lines = []
                    progress_bar = st.progress(0, text="准备中...")

                    def pc(cur, tot, label):
                        progress_bar.progress(cur / tot, text=f"{label} ({cur}/{tot})")

                    def lc(msg):
                        log_lines.append(msg)
                        st.text("\n".join(log_lines[-8:]))

                    try:
                        chapters, buf = run_full_pipeline(
                            student=student,
                            progress_callback=pc,
                            log_callback=lc,
                            enable_deai=st.session_state["report_enable_deai"],
                            deai_intensity=st.session_state["report_deai_intensity"],
                        )
                        st.session_state["report_chapters"] = chapters
                        st.session_state["report_docx_buf"] = buf
                        register_document_output(buf, author_name, author_id, chapters)
                        status.update(label="✅ 全流程管道执行完毕！", state="complete")
                    except Exception as e:
                        status.update(label=f"❌ 管道执行失败: {e}", state="error")
                        st.error(traceback.format_exc())

        # ── 管道完成后自动显示下载按钮 ──
        if "report_docx_buf" in st.session_state and st.session_state["report_docx_buf"] is not None:
            st.success("✅ 设计报告已就绪，点击下方按钮下载：")
            st.download_button(
                "💾 下载项目设计报告.docx",
                st.session_state["report_docx_buf"],
                file_name=f"项目设计报告_{author_name}_{author_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                **stretch_width(st.download_button),
            )

        st.markdown("---")

        # ── 章节生成面板 ──
        st.markdown("### 📝 章节生成")

        # 初始化 session state
        if "report_chapters" not in st.session_state:
            st.session_state["report_chapters"] = {}
        if "report_generating" not in st.session_state:
            st.session_state["report_generating"] = False

        report_chapters = st.session_state["report_chapters"]

        # 分组展示按章节
        for ch in range(1, 6):
            ch_sections = [s for s in REPORT_CHAPTERS if s.chapter == ch]
            ch_names = {
                1: "第1章 项目背景与概况",
                2: "第2章 现状调查与分析",
                3: "第3章 设计理念与构思",
                4: "第4章 总体方案设计",
                5: "第5章 重点地块设计",
            }

            any_generated = any(s.section_id in report_chapters for s in ch_sections)
            with st.expander(
                f"{ch_names[ch]} （{len([s for s in ch_sections if s.section_id in report_chapters])}/{len(ch_sections)} 节已生成）",
                expanded=any_generated or (ch == 1)
            ):
                for sec in ch_sections:
                    generated = sec.section_id in report_chapters
                    status = "✅" if generated else "⏳"
                    col_sec, col_btn = st.columns([5, 1])
                    with col_sec:
                        st.markdown(f"{status} **{sec.section_id} {sec.title}** — 约{sec.word_count}字")
                        if generated:
                            st.markdown(report_chapters[sec.section_id])
                    with col_btn:
                        if st.button("🔄 重新生成" if generated else "🧠 生成", key=f"report_gen_{sec.section_id}"):
                            with st.spinner(f"生成 {sec.section_id} {sec.title}..."):
                                ctx_data = build_document_context()
                                text = generate_single_section(sec, ctx_data)
                                report_chapters[sec.section_id] = text
                                st.session_state["report_chapters"] = report_chapters
                                st.rerun()

        # ── 一键生成全部 ──
        st.markdown("---")
        col_all, col_clear = st.columns([3, 1])
        with col_all:
            if st.button("🚀 一键生成全部章节", type="primary", disabled=st.session_state["report_generating"],
                         **stretch_width(st.button)):
                st.session_state["report_generating"] = True
                st.rerun()

        with col_clear:
            if st.button("🗑️ 清空已生成", **stretch_width(st.button)):
                st.session_state["report_chapters"] = {}
                st.rerun()

        # 执行批量生成
        if st.session_state["report_generating"]:
            ctx_data = build_document_context()
            all_sections = REPORT_CHAPTERS
            total = len(all_sections)
            progress_bar = st.progress(0, text="准备生成...")
            status_text = st.empty()

            for i, sec in enumerate(all_sections):
                progress_bar.progress((i) / total, text=f"生成 {sec.section_id} {sec.title}...")
                status_text.info(f"⏳ 正在生成：{sec.section_id} {sec.title} （{i+1}/{total}）")

                if sec.section_id not in report_chapters:
                    try:
                        text = generate_single_section(sec, ctx_data)
                        report_chapters[sec.section_id] = text
                        st.session_state["report_chapters"] = report_chapters
                    except Exception as e:
                        report_chapters[sec.section_id] = f"[生成异常] {e}"
                        st.session_state["report_chapters"] = report_chapters

            progress_bar.progress(1.0, text="全部生成完成!")
            status_text.success(f"✅ 全部 {total} 节生成完毕！")
            st.session_state["report_generating"] = False
            st.rerun()

        # ── 统计 ──
        generated_count = len(report_chapters)
        total_count = len(REPORT_CHAPTERS)
        if generated_count > 0:
            total_chars = sum(len(v) for v in report_chapters.values())
            st.info(f"已生成 {generated_count}/{total_count} 节，共 {total_chars} 字")

        # ── 导出面板 ──
        st.markdown("---")
        st.markdown("### 📥 导出设计报告")

        if generated_count == total_count:
            if st.button("📥 导出项目设计报告 (.docx)", type="primary", **stretch_width(st.button)):
                with st.spinner("正在组装 Word 文档（严格按模板格式）..."):
                    try:
                        buf = assemble_report_docx(
                            chapters=report_chapters,
                            student=student,
                        )
                        st.session_state["report_docx_buf"] = buf
                        register_document_output(buf, author_name, author_id, report_chapters)
                        st.success("✅ 设计报告生成成功！请点击下方按钮下载。")
                        st.download_button(
                            "💾 下载项目设计报告.docx",
                            buf,
                            file_name=f"项目设计报告_{author_name}_{author_id}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            **stretch_width(st.download_button),
                        )
                    except Exception as e:
                        st.error(f"文档组装失败：{e}")
                        import traceback
                        st.code(traceback.format_exc())
        else:
            pct = generated_count / total_count * 100 if total_count else 0
            st.warning(f"⏳ 已完成 {pct:.0f}%（{generated_count}/{total_count} 节），全部生成后方可导出。")


    st.markdown("---")
    render_stage_summary(
        stage_code="13",
        title="全栈闭环重构完备度",
        findings=[
            {"point": "完全放弃外部渲染管线", "evidence": "极大提升出图速度，消除崩溃隐患，提高可重现度"},
            {"point": "直接代码级空间制图", "evidence": "数据图 Python 直出，保障地理定位与线条的绝对精确性"},
            {"point": "自动化的工程排版引擎", "evidence": "内置 A3 工程图框与排版美学，实现工业级出图标准"},
        ],
        methodology="轻量化 Python GIS 制图引擎 + Python PIL 自动化图签、图例与规划说明组装",
        implication="彻底打通城乡规划专业级展板自动排版与汇报图册生产线",
    )

    # 业务逻辑主线推进导航
    render_logic_chain_stepper("13")

