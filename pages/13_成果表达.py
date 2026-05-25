import streamlit as st
import shutil
import io
from pathlib import Path
from PIL import Image
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.ui.module_summary import render_stage_summary
from src.workflow.stage_data_bus import load_stage_output, render_evidence_chain_bar
from src.workflow.stage_keys import SK
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="13 成果表达", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="成果表达",
    description="全新工作流：1. Python 代码绘制空间规划矢量底图 -> 2. 自动化标准 A3 图框与规划指标信息卡封装。",
    eyebrow="Stage 13",
    tags=["规划图纸代码生成", "图册自动组装", "标准图签封装"],
)
render_evidence_chain_bar("13", ["10", "11", "12", "13"])

SUB_OPTIONS = ["🗺️ 规划图纸代码生成", "🖼️ 标准图册自动组装", "📤 文档导出"]
selected_sub = st.radio("工作流步骤", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

ROOT = Path(__file__).resolve().parent.parent

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
        drawing_type = st.selectbox("图纸类型 (主绘图区内容)", ["现状区位图", "卫星图", "土地利用现状图", "交通分析图", "历史建筑与工业遗产分布图", "建筑高度现状图", "建筑风貌现状图"])
        drawing_title = st.text_input("图纸标题", value=drawing_type)
        drawing_num = st.text_input("图纸编号", value="DR-001")
        
        st.markdown("### 2. 设计说明与规划指标")
        
        # Default descriptions helper
        default_desc = {
            "现状区位图": [
                "1. 地理区位：本项目位于吉林省长春市宽城区历史文化核心街区，紧邻长春火车站与伪满皇宫博物院，是连接历史风貌区与现代城市中心的关键枢纽地带。",
                "2. 规划范围：规划研究范围东至伊通河、西至亚泰大街、南至长通路、北至京哈铁路，总规划研究面积约150公顷。包含5大重点更新地块。",
                "3. 指标现状：核心区现状路网密度6.2km/km²，建筑密度42%，水绿覆盖率约12.4%。规划定位为“数字孪生·古今共振”的历史风貌与双创活力街区。"
            ],
            "卫星图": [
                "1. 遥感影像：本图底图采用高分辨率 Google Earth 卫星遥感影像（2024年最新数据），直观反映项目所在长春市宽城区伪满皇宫周边区域的真实地表覆盖与建筑空间密度。",
                "2. 蓝绿肌理：东侧伊通河生态廊道水体形态完整，但街区内部绿色开敞空间较少，植被覆盖主要呈线性分布在铁路线及道路两侧，亟需引入更多社区口袋公园。",
                "3. 建设状况：街区内现状以中低层高密度建筑群为主，东北侧存在大面积中车低效工业遗存与厂房，南侧及西侧以商旧住宅为主，空间肌理较为拥挤。"
            ],
            "土地利用现状图": [
                "1. 用地构成：项目区内以居住用地（R）和商业服务业设施用地（B）为主，主要分布在亚泰大街及长通路两侧。工业与仓储用地占比较低且多属需更新工业遗存。",
                "2. 混合利用：规划提倡在轨道站点及重点更新地段发展商住混合、文创混合等多功能混合用地（M），以提升地块经济与社会活力。",
                "3. 用地优化：通过盘活现状低效建设用地，增加公共服务设施用地（A） and 绿地与广场用地（G），改善居民 15 分钟生活圈的公共服务供给与空间品质。"
            ],
            "交通分析图": [
                "1. 骨架路网：规划区内以亚泰大街快速路和长通路、凯旋路为主干路网，南北向贯穿良好，但高架道路对两侧街区存在一定的物理与视线割裂作用。",
                "2. 铁路线路：北部京哈铁路横穿，对地块形成严重的南北向交通阻隔。规划建议在更新改造中，增设跨铁人行天桥或地下通道以缝合城市南北片区。",
                "3. 慢行慢游：现状支路网密度偏低且不成系统，慢行体验较差。规划提出通过微循环道路改造和TOD联动，构建高品质、步行友好的慢游交通环线。"
            ],
            "历史建筑与工业遗产分布图": [
                "1. 遗产识别：片区内包含以伪满皇宫为核心的近代历史建筑群，以及东北侧中车长客厂区的大跨度工业厂房和铁轨遗存，是复合型城市遗产的关键载体。",
                "2. 价值评估：历史风貌核心保护区与中车厂区具有极高的建筑质量和空间识别度，是本次更新设计中严格执行“保留与修缮”的刚性管控区域。",
                "3. 活化思路：保护传统街区肌理与风貌界面的连续性，打通历史文化展示游线，将工业遗存置换为文创、博览和青年双创等活力复合功能。"
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
            ]
        }
        
        # AI generation button
        if st.button("🧠 AI 智能编写说明与指标 (基于大模型)", **stretch_width(st.button)):
            with st.spinner("AI 正在结合规划定位编写说明文字..."):
                from src.engines.llm_engine import call_llm_engine
                sys_p = "你是一个顶级城市规划师。请为城市设计图纸编写三条精简专业的设计说明（每条50字以内）。"
                prompt_p = f"请结合本项目“长春伪满皇宫周边街区微更新”及图纸类型“{drawing_type}”（图纸标题：“{drawing_title}”），编写三条专业的规划说明与指标，以1. 2. 3.的格式输出。"
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
        author = st.text_input("制作人", value="陈礼冲")
        author_id = st.text_input("学号", value="202111003")
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
    render_section_intro("全案文档导出", "导出前期分析诊断与总体设计导则文本。", eyebrow="Document Export")
    
    col1, col2 = st.columns(2)
    with col1:
        guideline = load_stage_output("12", SK.DESIGN_GUIDELINE, "")
        if guideline:
            st.download_button("📥 下载城市设计导则 (Markdown)", guideline, file_name="城市设计导则.md", **stretch_width(st.download_button))
        else:
            st.info("暂无导则数据，请在 Stage 12 生成。")
            
    with col2:
        diagnosis = load_stage_output("05", SK.DIAGNOSIS_REPORT, "")
        if diagnosis:
            st.download_button("📥 下载前期诊断报告 (Markdown)", diagnosis, file_name="诊断报告.md", **stretch_width(st.download_button))
        else:
            st.info("暂无诊断数据，请在 Stage 05 生成。")

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

