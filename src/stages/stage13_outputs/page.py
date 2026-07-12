import streamlit as st
import shutil
import io
import os
import traceback
from pathlib import Path
from PIL import Image
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.ui.module_summary import render_stage_summary
from src.workflow.stage_data_bus import load_stage_output, render_evidence_chain_bar
from src.workflow.stage_keys import SK
from src.ui.streamlit_compat import stretch_width
from src.ui.persistent_outputs import register_thesis_output, register_report_output

from src.stages.common.workspace import render_stage_workspace
from src.stages.stage13_outputs.config import STAGE13_WORKSPACE

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
            default_desc = {
                "现状区位图": [
                    "1. 地理区位：本项目位于吉林省长春市宽城区历史文化核心街区，紧邻长春火车站与伪满皇宫博物院，是连接历史风貌区与现代城市中心的关键枢纽地带。",
                    "2. 规划范围：规划研究范围东至伊通河、西至亚泰大街、南至长通路、北至京哈铁路，总规划研究面积约160公顷。包含5大重点更新地块。",
                    "3. 指标现状：核心区现状路网密度6.2km/km²，建筑密度42%，水绿覆盖率约12.4%。规划定位为“数字孪生·古今共振”的历史风貌与双创活力街区。"
                ],
                "研究范围图": [
                    "1. 核心范围：规划确定的更新改造研究边界西起亚泰大街，东至伊通河，南至长通路，北至京哈铁路，总用地面积约为 160 公顷。",
                    "2. 重点地块：规划重点针对片区内 5 个低效国有或集体资产地块进行城市设计与活力针灸，包括老水产批发市场 and 中车旧厂区等。",
                    "3. 现状本底：周边路网成熟，紧邻长春站交通门户，是缝合老宽城铁北地区与长春历史文化中轴线的空间关键锁扣。"
                ],
                "卫星图": [
                    "1. 遥感影像：本图底图采用高分辨率 Google Earth 卫星遥感影像（2024年最新数据），直观反映项目所在长春市宽城区伪满皇宫周边区域的真实地表覆盖与建筑空间密度。",
                    "2. 蓝绿肌理：东侧伊通河生态廊道水体形态完整，但街区内部绿色开敞空间较少，植被覆盖主要呈线性分布在铁路线及道路两侧，亟需引入更多社区口袋公园。",
                    "3. 建设状况：街区内现状以中低层高密度建筑群为主，东北侧存在大面积中车低效工业遗存与厂房，南侧及西侧以商旧住宅为主，空间肌理较为拥挤。"
                ],
                "土地利用现状图": [
                    "1. 用地构成：项目区内以居住用地（R）和商业服务业设施用地（B）为主，主要分布在亚泰大街及长通路两侧。工业与仓储用地占比较低且多属需更新工业遗存。",
                    "2. 混合利用：规划提倡在轨道站点及重点更新地段发展商住混合、文创混合等多功能混合用地（M），以提升地块经济与社会活力。",
                    "3. 用地优化：通过盘活现状低效建设用地，增加公共服务设施用地（A） and 绿地与广场用地（G），改善居民 15 分钟生活圈 of 设施供给品质。"
                ],
                "建筑高度现状图": [
                    "1. 高度特征：区内建筑以低层（1-3层）和多层（4-7层）为主，集中分布在历史街区内部和老旧社区，空间肌理紧凑，尺度宜人。",
                    "2. 高层分布：中高层与高层住宅主要零散分布在区位外围，对历史街区核心区及伪满皇宫周边产生了一定的视线廊道压力。",
                    "3. 管控思路：规划提出结合视线敏感度分析，严格控制核心区新建建筑高度，禁止插建高层，保留历史空间原有的舒缓天际线。"
                ],
                "建筑风貌现状图": [
                    "1. 风貌构成：区内历史保护风貌占比约3.2%，集中在伪满皇宫周边；普通居住风貌占主导，整体风貌协调度有待提升。",
                    "2. 界面杂乱：局部街区存在杂乱搭接及立面风貌破损，严重削弱了历史文化街区的空间质量与文化氛围，缺乏统一的导则引导。",
                    "3. 整治策略：实行分类整治，对历史建筑修缮复原，对普通住宅立面进行微改造协调，消除风貌冲突，营造和谐的历史共振街区。"
                ],
                "历史建筑与工业遗产分布图": [
                    "1. 遗产识别：片区内包含以伪满皇宫为核心的近代历史建筑群，以及东北侧中车长客厂区的大跨度工业厂房 and 铁轨遗存，是复合型城市遗产的关键载体。",
                    "2. 价值评估：历史风貌核心保护区与中车厂区具有极高的建筑质量和空间识别度，是本次更新设计中严格执行“保留与修缮”的刚性管控区域。",
                    "3. 活化思路：保护传统街区肌理与风貌界面的连续性，打通历史文化展示游线，将工业遗存置换为文创、博览和青年双创等活力复合功能。"
                ],
                "交通分析图": [
                    "1. 骨架路网：规划区内以亚泰大街快速路和长通路、凯旋路为主干路网，南北向贯穿良好，但高架道路对两侧街区存在一定的物理与视线割裂作用。",
                    "2. 铁路线路：北部京哈铁路横穿，对地块形成严重的南北向交通阻隔。规划建议在更新改造中，增设跨铁人行天桥或地下通道以缝合城市南北片区。",
                    "3. 慢行慢游：现状支路网密度偏低且不成系统，慢行体验较差。规划提出通过微循环道路改造和TOD联动，构建高品质、步行友好的慢游交通环线。"
                ],
                "空间句法可达性分析图": [
                    "1. 全局整合：基于路网拓扑分析发现，亚泰大街及长通路具有极高的全局可达性（红色），构成了研究范围对外的车行主通道。",
                    "2. 慢行渗透：历史街区内部由于支路网密度偏低、被京哈线割裂，整合度表现出空间凹陷，步行可达性较弱，亟需细化微循环。",
                    "3. 空间协同：协同度散点图 $R^2$ 拟合显示历史核心区与全域存在中度脱节，说明该地块在人流疏导与慢行连通上存在明显的孤岛效应。"
                ],
                "环境品质问题地图": [
                    "1. 噪声污染：京哈铁路线和亚泰大街快速路高架段对两侧街区产生严重的声环境污染，最大噪声带向两侧扩散达 100-120 米。",
                    "2. 绿化短板：通过街景图像量化分析发现，长通路及老社区内部多段街道的绿视率（GVI）低于 10%，空间界面灰色硬质感过强。",
                    "3. 空间割裂：中车长客厂区大面积封闭式围墙阻断了南北人行路径，导致周边老旧住宅社区内部微循环不畅，慢行系统断档。"
                ],
                "遗产价值评估热力图": [
                    "1. 价值核心：热力图呈现出显著的“一核两带”格局，以伪满皇宫博物院近代历史保护群为绝对的遗产价值红区核心。",
                    "2. 工业遗存：东北侧中车长客旧厂房及历史铁轨展示线构成了次一级的工业遗产文化脉络带，具有极高的重构与活化开发潜力。",
                    "3. 空间导向：价值热力衰减直接决定了开发建设的严格风貌敏感区分区，越靠近高热力值点，新建建筑的体量与材质控制越严格。"
                ],
                "更新模式分区图": [
                    "1. 保护修缮：针对伪满皇宫等 3.2% 的历史建筑，执行原地原风貌修缮，划定绝对保护红线，禁止任何形式的加建与插建高层。",
                    "2. 整治提升：对风貌过渡区的老旧公建及沿街界面，统一立面风貌导则，拆除杂乱违建，使建筑色调、材质与历史保护区协调。",
                    "3. 置换与微更新：对中车低效工业厂房进行功能重组与置换，置换为青年文创；对老社区实施微改造，盘活边角地增加活动场地。"
                ],
                "空间结构规划图": [
                    "1. 规划结构：形成“一核、双轴、五地块”的总体更新规划结构。一核指历史文化共振核，双轴为站城联动轴与生态延伸轴。",
                    "2. 站城联动：打通长春站至伪满皇宫的空间轴线，利用高品质慢行商业街与视觉廊道建立两者的物理与文化强关联。",
                    "3. 节点触媒：以 5 个更新活力节点为针灸触点，激活周边消极的街区本底，促进历史风貌区与现代化城市的无缝衔接。"
                ],
                "用地规划图": [
                    "1. 规划布局：商业与文创混合区沿亚泰大街与长通路两侧布置；老旧社区内部主要进行绿化修补与微更新，维持低容积率肌理。",
                    "2. 密路网：地块内 proposed 规划小街区密路网（3.5-5米宽人行步行街/支路），将大尺度街区切碎，极大提升空间可渗透性。",
                    "3. 景观骨架：构建环历史核心区的绿色开敞环线，并与东侧伊通河生态公园绿带无缝对接，实现蓝绿网络与城市空间融合。"
                ],
                "建筑高度控制图": [
                    "1. 核心高度：伪满皇宫博物院周边 300 米绝对控制区内，新建建筑限高 9 米（对应红色区），保持原有舒缓平滑的空间天际线。",
                    "2. 风貌协调：300-600 米风貌过渡区内，限高 18 米（黄色区），新建建筑宜为 4-5 层，以多层及连续坡屋顶形式为主。",
                    "3. 活力开发：600 米以外 of 城市外围及亚泰大街沿线，限高 24 米（蓝色区），支持局部地块进行适当的高效率活力功能开发。"
                ],
                "建筑更新控制图": [
                    "1. 保护修缮：对历史风貌建筑坚持最小干预，保留建筑原始结构与外墙肌理，严格控制周边景观小品色调以防风貌退化。",
                    "2. 保留整治：对普通住宅以立面整治、增加外保温及整理管线为主，不破坏原住宅格局，实施渐进式微更新更新。",
                    "3. 功能置换：对中车厂房大跨度空间进行结构加固与重组，置换为高附加值的文创展厅、艺术沙龙与科技孵化园。"
                ],
                "道路交通系统规划图": [
                    "1. 路网骨架：规划形成“三横三纵”的城市主次干路网骨架，提升地块对外的交通联系和连通度，实现内外交通的顺畅转换。",
                    "2. 慢行慢游：加密内部支路网，优化慢行步道，提升街区可达性，建立对行人与自行车慢行友好的漫游系统，打通微循环瓶颈。",
                    "3. TOD 开发：紧邻长春火车站与轨道交通站点，规划强化 TOD 交通枢纽的辐射带动作用，引导高密度、功能混合 of TOD 导向型开发。"
                ],
                "慢行系统规划图": [
                    "1. 漫游步道：规划长春站-伪满皇宫-中车遗产-伊通河 the 4.2 公里文旅慢行大环线（红色），串联沿线 12 处核心文旅景点。",
                    "2. 绿道骑行：沿伊通河及铁路线边缘布置林荫骑行专用车道（绿色），支持共享单车与绿色健康通勤，实现人车分流安全出行。",
                    "3. 邻里步行：老旧住宅区内增设“邻里漫步小径”（橙色），结合口袋公园布置健身设施，完善居民 5 分钟步行微系统。"
                ],
                "公共空间系统图": [
                    "1. 广场节点：在伪满皇宫前及中车厂房东侧规划两处大型文化景观广场，作为城市大型公共活动与旅游集散的复合载体。",
                    "2. 口袋公园：见缝插针地在居住社区内部增设 6 处口袋公园，确保规划区实现“300 米见绿、500 米见园”的服务全覆盖。",
                    "3. 服务缓冲：为每个口袋公园划定 300 米服务半径分析缓冲（绿色圈），精准织补覆盖盲区，大幅度提升整体公共绿地均等化。"
                ],
                "绿地景观系统图": [
                    "1. 蓝绿框架：以东侧伊通河生态廊道为骨架，通过水廊与绿带将大自然引入地块深处，形成蓝绿交织的城市生态基底。",
                    "2. 景观节点：打造伪满皇宫前广场、中车遗产绿地等多处景观核心节点，并对道路绿化带进行林荫化改造提升视觉体验。",
                    "3. 织补更新：通过小微绿地口袋公园和垂直绿化织补消极灰色空间，大幅提高绿视率，实现生态宜居的城市微更新目标。"
                ],
                "历史文化展示系统图": [
                    "1. 展示路径：以近代风貌核心保护区为基础，构建两条历史文脉游赏展示路径，采用统一的标识系统与导游导视指引系统。",
                    "2. 遗产标示：在伪满皇宫、中车老厂房、铁路老枕木等关键节点设立金属文化浮雕碑与解说板，形成“露天博物馆”体验。",
                    "3. 视廊保护：严格保护从长春火车站、亚泰大街远眺伪满皇宫的 3 条重要风貌视线走廊，走廊范围内禁止悬挂大型广告牌。"
                ],
                "AIGC技术推演过程图": [
                    "1. 数据底座：利用多源 GIS 空间图层与高分辨率街景图像建立数字底盘，通过 NLP 挖掘微博/小红书情感，诊断品质痛点。",
                    "2. AIGC 生成：利用 Stable Diffusion 算法配合 ControlNet 控制网，输入手绘线稿、空间意向与提示词，自动推演 100+ 方案。",
                    "3. 智能协商：通过 LLM 智能体模拟政府、专家、居民与开发商进行决策协商，综合评选最优方案，实现全链条数字化辅助。"
                ],
                "实施分期图": [
                    "1. 近期建设（1-3年）：优先启动水产批发市场及食品调料市场地块（绿色区），置换为社区商业与公共停车场以疏导人流。",
                    "2. 中期推进（3-5年）：推进中车工业遗存活化项目（蓝色区），将旧厂房改建为数智文创街区，并缝合被铁路线阻断的路网。",
                    "3. 远期展望（5-10年）：实施清禾市场及石油公司周边低效住宅微更新项目（紫色区），彻底完成全区公共绿地与设施配套。"
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
            author = st.text_input("制作人", value="", placeholder="请输入姓名")
            author_id = st.text_input("学号", value="", placeholder="请输入学号")
            organization = st.text_area("学校班级", value="吉林建筑大学建筑与规划学院\n城乡规划211班", height=60)
            
            if st.button("🎨 一键代码绘图并组装图纸", type="primary", **stretch_width(st.button)):
                with st.spinner("Python 代码绘图与排版卡片组装中..."):
                    import tempfile
                    import os
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
                st.info("暂无设计纲要数据，请在 Stage 07 生成。")

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


    elif selected_sub == "📝 毕业设计答辩稿":
        render_section_intro(
            "毕业设计答辩稿生成",
            "按吉林建筑大学模板规范生成毕业设计答辩稿（设计说明），严格遵循5章结构、字数约束和格式化排版。",
            eyebrow="Graduation Thesis Composer",
        )

        from src.engines.thesis_composer import (
            THESIS_CHAPTERS, assemble_thesis_docx, StudentInfo,
            build_thesis_context, generate_single_section,
        )

        # ── 学生信息 ──
        st.markdown("### 👤 学籍信息")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            student_name = st.text_input("学生姓名", value="", key="thesis_name", placeholder="请输入姓名")
            student_id = st.text_input("学号", value="", key="thesis_id", placeholder="请输入学号")
        with col_s2:
            student_advisor = st.text_input("指导教师", value="", key="thesis_advisor")
            student_date = st.text_input("答辩日期", value="2026年6月", key="thesis_date")
        with col_s3:
            student_college = st.text_input("学院", value="建筑与规划学院", key="thesis_college")
            student_major = st.text_input("专业", value="城乡规划", key="thesis_major")

        student = StudentInfo(
            name=student_name,
            student_id=student_id,
            advisor=student_advisor,
            college=student_college,
            major=student_major,
            date=student_date,
        )

        st.markdown("---")

        # ══════════════════════════════════════
        # 一键生成管道
        # ══════════════════════════════════════
        st.markdown("### 🚀 一键生成管道")

        from src.engines.thesis_pipeline import run_light_pipeline, run_full_pipeline

        # ── 降 AI 率选项 ──
        if "thesis_enable_deai" not in st.session_state:
            st.session_state["thesis_enable_deai"] = True
        if "thesis_deai_intensity" not in st.session_state:
            st.session_state["thesis_deai_intensity"] = 0.7

        col_deai_opt, col_deai_int = st.columns([3, 1])
        with col_deai_opt:
            st.session_state["thesis_enable_deai"] = st.checkbox(
                "🧬 启用 AI 率优化（降 AIGC 检测率）",
                value=st.session_state["thesis_enable_deai"],
                help="启用后管道会自动对生成的文本进行降 AI 处理：规则打散 + LLM 风格扰动 + 个人观察注入。可显著降低知网 AIGC 检测率。",
            )
        with col_deai_int:
            if st.session_state["thesis_enable_deai"]:
                st.session_state["thesis_deai_intensity"] = st.slider(
                    "处理强度", 0.3, 1.0, st.session_state["thesis_deai_intensity"], 0.1,
                    help="越高改动越多，AI 痕迹越少，但可能与原文差异越大。建议 0.5-0.7。",
                )

        col_a, col_b = st.columns(2)

        # ── 管道 A: 轻量 ──
        with col_a:
            with st.container(border=True):
                st.markdown("#### ⚡ 轻量管道")
                st.caption("基于各阶段**已生成**的 AI 报告，快速产出答辩稿。适用于各阶段已运行过的场景。")
                st.caption("约 36 步 · 预计 1-3 分钟")

                if st.button("🚀 一键生成答辩稿（轻量）", key="pipeline_light", type="primary",
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
                                enable_deai=st.session_state["thesis_enable_deai"],
                                deai_intensity=st.session_state["thesis_deai_intensity"],
                            )
                            st.session_state["thesis_chapters"] = chapters
                            st.session_state["thesis_docx_buf"] = buf
                            register_thesis_output(buf, student_name, student_id, chapters)
                            status.update(label="✅ 轻量管道执行完毕！", state="complete")
                        except Exception as e:
                            status.update(label=f"❌ 管道执行失败: {e}", state="error")
                            st.error(traceback.format_exc())

        # ── 管道 B: 全流程 ──
        with col_b:
            with st.container(border=True):
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
                                enable_deai=st.session_state["thesis_enable_deai"],
                                deai_intensity=st.session_state["thesis_deai_intensity"],
                            )
                            st.session_state["thesis_chapters"] = chapters
                            st.session_state["thesis_docx_buf"] = buf
                            register_thesis_output(buf, student_name, student_id, chapters)
                            status.update(label="✅ 全流程管道执行完毕！", state="complete")
                        except Exception as e:
                            status.update(label=f"❌ 管道执行失败: {e}", state="error")
                            st.error(traceback.format_exc())

        # ── 管道完成后自动显示下载按钮 ──
        if "thesis_docx_buf" in st.session_state and st.session_state["thesis_docx_buf"] is not None:
            st.success("✅ 答辩稿已就绪，点击下方按钮下载：")
            st.download_button(
                "💾 下载毕业设计答辩稿.docx",
                st.session_state["thesis_docx_buf"],
                file_name=f"毕业设计答辩稿_{student_name}_{student_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                **stretch_width(st.download_button),
            )

        st.markdown("---")

        # ── 章节生成面板 ──
        st.markdown("### 📝 章节生成")

        # 初始化 session state
        if "thesis_chapters" not in st.session_state:
            st.session_state["thesis_chapters"] = {}
        if "thesis_generating" not in st.session_state:
            st.session_state["thesis_generating"] = False

        thesis_chapters = st.session_state["thesis_chapters"]

        # 分组展示按章节
        for ch in range(1, 6):
            ch_sections = [s for s in THESIS_CHAPTERS if s.chapter == ch]
            ch_names = {
                1: "第1章 项目背景与概况",
                2: "第2章 现状调查与分析",
                3: "第3章 设计理念与构思",
                4: "第4章 总体方案设计",
                5: "第5章 重点地块设计",
            }

            any_generated = any(s.section_id in thesis_chapters for s in ch_sections)
            with st.expander(
                f"{ch_names[ch]} （{len([s for s in ch_sections if s.section_id in thesis_chapters])}/{len(ch_sections)} 节已生成）",
                expanded=any_generated or (ch == 1)
            ):
                for sec in ch_sections:
                    generated = sec.section_id in thesis_chapters
                    status = "✅" if generated else "⏳"
                    col_sec, col_btn = st.columns([5, 1])
                    with col_sec:
                        st.markdown(f"{status} **{sec.section_id} {sec.title}** — 约{sec.word_count}字")
                        if generated:
                            st.markdown(thesis_chapters[sec.section_id])
                    with col_btn:
                        if st.button("🔄 重新生成" if generated else "🧠 生成", key=f"thesis_gen_{sec.section_id}"):
                            with st.spinner(f"生成 {sec.section_id} {sec.title}..."):
                                ctx_data = build_thesis_context()
                                text = generate_single_section(sec, ctx_data)
                                thesis_chapters[sec.section_id] = text
                                st.session_state["thesis_chapters"] = thesis_chapters
                                st.rerun()

        # ── 一键生成全部 ──
        st.markdown("---")
        col_all, col_clear = st.columns([3, 1])
        with col_all:
            if st.button("🚀 一键生成全部章节", type="primary", disabled=st.session_state["thesis_generating"],
                         **stretch_width(st.button)):
                st.session_state["thesis_generating"] = True
                st.rerun()

        with col_clear:
            if st.button("🗑️ 清空已生成", **stretch_width(st.button)):
                st.session_state["thesis_chapters"] = {}
                st.rerun()

        # 执行批量生成
        if st.session_state["thesis_generating"]:
            ctx_data = build_thesis_context()
            all_sections = THESIS_CHAPTERS
            total = len(all_sections)
            progress_bar = st.progress(0, text="准备生成...")
            status_text = st.empty()

            for i, sec in enumerate(all_sections):
                progress_bar.progress((i) / total, text=f"生成 {sec.section_id} {sec.title}...")
                status_text.info(f"⏳ 正在生成：{sec.section_id} {sec.title} （{i+1}/{total}）")

                if sec.section_id not in thesis_chapters:
                    try:
                        text = generate_single_section(sec, ctx_data)
                        thesis_chapters[sec.section_id] = text
                        st.session_state["thesis_chapters"] = thesis_chapters
                    except Exception as e:
                        thesis_chapters[sec.section_id] = f"[生成异常] {e}"
                        st.session_state["thesis_chapters"] = thesis_chapters

            progress_bar.progress(1.0, text="全部生成完成!")
            status_text.success(f"✅ 全部 {total} 节生成完毕！")
            st.session_state["thesis_generating"] = False
            st.rerun()

        # ── 统计 ──
        generated_count = len(thesis_chapters)
        total_count = len(THESIS_CHAPTERS)
        if generated_count > 0:
            total_chars = sum(len(v) for v in thesis_chapters.values())
            st.info(f"已生成 {generated_count}/{total_count} 节，共 {total_chars} 字")

        # ── 导出面板 ──
        st.markdown("---")
        st.markdown("### 📥 导出答辩稿")

        if generated_count == total_count:
            if st.button("📥 导出毕业设计答辩稿 (.docx)", type="primary", **stretch_width(st.button)):
                with st.spinner("正在组装 Word 文档（严格按模板格式）..."):
                    try:
                        buf = assemble_thesis_docx(
                            chapters=thesis_chapters,
                            student=student,
                        )
                        st.session_state["thesis_docx_buf"] = buf
                        register_thesis_output(buf, student_name, student_id, thesis_chapters)
                        st.success("✅ 答辩稿生成成功！请点击下方按钮下载。")
                        st.download_button(
                            "💾 下载毕业设计答辩稿.docx",
                            buf,
                            file_name=f"毕业设计答辩稿_{student_name}_{student_id}.docx",
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
