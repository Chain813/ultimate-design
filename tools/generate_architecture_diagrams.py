import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Ensure Chinese characters are rendered correctly
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

user_home = os.path.expanduser("~")
output_dir = os.path.join(user_home, ".gemini", "antigravity", "brain", "4548a8df-fff1-40c0-a394-3f74511d5d61", "scratch", "images")
os.makedirs(output_dir, exist_ok=True)

# Theme colors
C_PRIMARY = "#182B49"   # Navy
C_ACCENT = "#009688"    # Teal
C_LIGHT_BG = "#F4F7FA"  # Light gray
C_TEXT = "#3C4046"
C_WARN = "#DC3545"
C_OK = "#28A745"

def draw_system_architecture():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Title
    ax.text(5, 7.6, "ultimateDESIGN 城市更新空间设计智能推演系统架构图", 
            fontsize=15, fontweight='bold', color=C_PRIMARY, ha='center')
    
    # Layer 1: Data Input Layer (Y = 6)
    ax.text(0.5, 6, "数据输入层\n(Data Layer)", fontsize=11, fontweight='bold', color=C_PRIMARY, va='center', ha='left')
    inputs = [
        ("多源空间矢量数据", "OSM路网 / 现状建筑边界 / 规划宗地 (GeoJSON)"),
        ("城市街景多向影像", "百度全景街景样点图集 (1,788张 JPG)"),
        ("规划保护政策法规", "国家历史城区保护条例 / 控规文本 (Vector DB)")
    ]
    for idx, (title, desc) in enumerate(inputs):
        x = 2.2 + idx * 2.5
        # Box
        rect = patches.FancyBboxPatch((x, 5.4), 2.2, 1.2, boxstyle="round,pad=0.1", fc=C_LIGHT_BG, ec=C_PRIMARY, lw=1.5)
        ax.add_patch(rect)
        # Texts
        ax.text(x + 1.1, 6.2, title, fontsize=10, fontweight='bold', color=C_PRIMARY, ha='center')
        ax.text(x + 1.1, 5.7, desc, fontsize=8, color=C_TEXT, ha='center', wrap=True)

    # Layer 2: Core Engine Layer (Y = 3.2)
    ax.text(0.5, 3.2, "核心引擎层\n(Engine Layer)", fontsize=11, fontweight='bold', color=C_PRIMARY, va='center', ha='left')
    engines = [
        ("AHP-MPI 空间体检引擎", "空间潜力(S)/需求(D)/绿化(E)\n计算MPI更新潜力指数"),
        ("OSMnx/SegFormer 内核", "路网空间句法拓扑分析\n街景绿视率(GVI)语义分割"),
        ("DeepSeek 多智能体沙盘", "三方主体(居民/开发商/规划局)\n满意度博弈与共识协商")
    ]
    for idx, (title, desc) in enumerate(engines):
        x = 2.2 + idx * 2.5
        rect = patches.FancyBboxPatch((x, 2.6), 2.2, 1.2, boxstyle="round,pad=0.1", fc=C_LIGHT_BG, ec=C_ACCENT, lw=1.5)
        ax.add_patch(rect)
        ax.text(x + 1.1, 3.4, title, fontsize=10, fontweight='bold', color=C_ACCENT, ha='center')
        ax.text(x + 1.1, 2.9, desc, fontsize=8, color=C_TEXT, ha='center', wrap=True)

    # Layer 3: Output Compilation Layer (Y = 0.8)
    ax.text(0.5, 0.8, "成果输出层\n(Output Layer)", fontsize=11, fontweight='bold', color=C_PRIMARY, va='center', ha='left')
    outputs = [
        ("Streamlit 决策交互WebUI", "实时诊断结果展示 / 满意度雷达图\nRAG合规状态审查面板"),
        ("ControlNet 空间对齐制图", "矢量转光栅色彩红线硬约束\nStable Diffusion 蓝图绘制"),
        ("A3 高清图册并行编译", "Matplotlib/Pillow 自动化排版\n多进程一键编译 26 张图册")
    ]
    for idx, (title, desc) in enumerate(outputs):
        x = 2.2 + idx * 2.5
        rect = patches.FancyBboxPatch((x, 0.2), 2.2, 1.2, boxstyle="round,pad=0.1", fc=C_LIGHT_BG, ec=C_PRIMARY, lw=1.5)
        ax.add_patch(rect)
        ax.text(x + 1.1, 1.0, title, fontsize=10, fontweight='bold', color=C_PRIMARY, ha='center')
        ax.text(x + 1.1, 0.5, desc, fontsize=8, color=C_TEXT, ha='center', wrap=True)

    # Add connecting arrows
    for i in range(3):
        # Arrow from Layer 1 to Layer 2
        ax.annotate("", xy=(3.3 + i*2.5, 3.9), xytext=(3.3 + i*2.5, 5.3),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color=C_ACCENT))
        # Arrow from Layer 2 to Layer 3
        ax.annotate("", xy=(3.3 + i*2.5, 1.5), xytext=(3.3 + i*2.5, 2.5),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color=C_PRIMARY))

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "system_architecture.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated system_architecture.png")

def draw_negotiation_workflow():
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Title
    ax.text(4, 5.6, "三方主体博弈协商与共识判定思维导图", 
            fontsize=13, fontweight='bold', color=C_PRIMARY, ha='center')
    
    # Central LLM Sandbox Node
    rect_c = patches.FancyBboxPatch((3.0, 2.4), 2.0, 1.2, boxstyle="round,pad=0.1", fc=C_LIGHT_BG, ec=C_PRIMARY, lw=2)
    ax.add_patch(rect_c)
    ax.text(4.0, 3.2, "DeepSeek-V4\n多智能体博弈沙盘", fontsize=10, fontweight='bold', color=C_PRIMARY, ha='center')
    ax.text(4.0, 2.7, "实时谈判 & 策略调整", fontsize=8, color=C_TEXT, ha='center')
    
    # 3 Agent Nodes (Residents, Developers, Gov)
    # 1. Residents (Top Left)
    rect_res = patches.FancyBboxPatch((0.5, 3.8), 2.0, 1.0, boxstyle="round,pad=0.1", fc=C_LIGHT_BG, ec=C_ACCENT, lw=1.5)
    ax.add_patch(rect_res)
    ax.text(1.5, 4.5, "居民智能体 (Residents)", fontsize=9, fontweight='bold', color=C_ACCENT, ha='center')
    ax.text(1.5, 4.0, "核心诉求：绿化织补\n配套改善 / 日照保障", fontsize=8, color=C_TEXT, ha='center')
    
    # 2. Developers (Bottom Left)
    rect_dev = patches.FancyBboxPatch((0.5, 0.8), 2.0, 1.0, boxstyle="round,pad=0.1", fc=C_LIGHT_BG, ec=C_ACCENT, lw=1.5)
    ax.add_patch(rect_dev)
    ax.text(1.5, 1.5, "开发商智能体 (Developer)", fontsize=9, fontweight='bold', color=C_ACCENT, ha='center')
    ax.text(1.5, 1.0, "核心诉求：商业面积\n容积率最大化 / 经济回报", fontsize=8, color=C_TEXT, ha='center')
    
    # 3. Government Planning Bureau (Right)
    rect_gov = patches.FancyBboxPatch((5.5, 2.4), 2.0, 1.0, boxstyle="round,pad=0.1", fc=C_LIGHT_BG, ec=C_ACCENT, lw=1.5)
    ax.add_patch(rect_gov)
    ax.text(6.5, 3.1, "规划局智能体 (Gov)", fontsize=9, fontweight='bold', color=C_ACCENT, ha='center')
    ax.text(6.5, 2.6, "核心诉求：历史街区风貌\n高度限高 / 强制性指标", fontsize=8, color=C_TEXT, ha='center')
    
    # Arrows and connection labels
    # Center to/from Agents
    ax.annotate("", xy=(2.6, 3.2), xytext=(2.2, 4.0), arrowprops=dict(arrowstyle="<->", lw=1.2, color=C_PRIMARY))
    ax.annotate("", xy=(2.6, 2.8), xytext=(2.2, 1.8), arrowprops=dict(arrowstyle="<->", lw=1.2, color=C_PRIMARY))
    ax.annotate("", xy=(5.4, 2.9), xytext=(5.1, 2.9), arrowprops=dict(arrowstyle="<->", lw=1.2, color=C_PRIMARY))
    
    # Decision Evaluation Flow (Top right -> Consensus check)
    rect_eval = patches.FancyBboxPatch((4.5, 4.4), 2.5, 0.9, boxstyle="round,pad=0.08", fc=C_LIGHT_BG, ec=C_WARN, lw=1.5)
    ax.add_patch(rect_eval)
    ax.text(5.75, 5.0, "满意度效用评估 (S_role)", fontsize=9, fontweight='bold', color=C_WARN, ha='center')
    ax.text(5.75, 4.6, "共识判定：min(S_role) >= 60?", fontsize=8, color=C_TEXT, ha='center')
    
    # Connection from Center to Evaluation
    ax.annotate("", xy=(5.75, 4.3), xytext=(4.3, 3.7), arrowprops=dict(arrowstyle="->", lw=1.2, color=C_WARN))
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "negotiation_workflow.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated negotiation_workflow.png")

def draw_compliance_audit_flow():
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 5)
    ax.axis('off')
    
    # Title
    ax.text(4, 4.6, "Zoning Compliance 空间控规合规性审查流程图", 
            fontsize=13, fontweight='bold', color=C_PRIMARY, ha='center')
    
    # Step 1: Input Geometry (Y=3.5)
    rect_s1 = patches.FancyBboxPatch((0.5, 2.8), 1.8, 0.8, boxstyle="round,pad=0.08", fc=C_LIGHT_BG, ec=C_PRIMARY, lw=1.5)
    ax.add_patch(rect_s1)
    ax.text(1.4, 3.3, "1. 空间矢量输入", fontsize=9, fontweight='bold', color=C_PRIMARY, ha='center')
    ax.text(1.4, 3.0, "地块边界/更新后建筑", fontsize=7.5, color=C_TEXT, ha='center')
    
    # Step 2: Math Computation (Y=3.5)
    rect_s2 = patches.FancyBboxPatch((3.0, 2.8), 2.0, 0.8, boxstyle="round,pad=0.08", fc=C_LIGHT_BG, ec=C_PRIMARY, lw=1.5)
    ax.add_patch(rect_s2)
    ax.text(4.0, 3.3, "2. 规划指标自动演算", fontsize=9, fontweight='bold', color=C_PRIMARY, ha='center')
    ax.text(4.0, 3.0, "FAR / 建筑密度 / 高度", fontsize=7.5, color=C_TEXT, ha='center')
    
    # Step 3: Rules Validation (Y=3.5)
    rect_s3 = patches.FancyBboxPatch((5.8, 2.8), 1.8, 0.8, boxstyle="round,pad=0.08", fc=C_LIGHT_BG, ec=C_PRIMARY, lw=1.5)
    ax.add_patch(rect_s3)
    ax.text(6.7, 3.3, "3. 控规红线强校核", fontsize=9, fontweight='bold', color=C_PRIMARY, ha='center')
    ax.text(6.7, 3.0, "RAG 向量法规相似检索", fontsize=7.5, color=C_TEXT, ha='center')
    
    # Connect Y=3.5 steps
    ax.annotate("", xy=(2.9, 3.2), xytext=(2.4, 3.2), arrowprops=dict(arrowstyle="->", lw=1.2, color=C_PRIMARY))
    ax.annotate("", xy=(5.7, 3.2), xytext=(5.1, 3.2), arrowprops=dict(arrowstyle="->", lw=1.2, color=C_PRIMARY))
    
    # Decision Step (Y=1.5)
    rect_dec = patches.FancyBboxPatch((3.0, 1.2), 2.0, 0.8, boxstyle="round,pad=0.08", fc=C_LIGHT_BG, ec=C_WARN, lw=1.5)
    ax.add_patch(rect_dec)
    ax.text(4.0, 1.7, "指标判定是否超标?", fontsize=9, fontweight='bold', color=C_WARN, ha='center')
    ax.text(4.0, 1.4, "如：FAR>1.4 或 Height>18m", fontsize=7.5, color=C_TEXT, ha='center')
    
    # Arrow from Step 3 to Decision
    ax.annotate("", xy=(4.0, 2.1), xytext=(6.7, 2.7), arrowprops=dict(arrowstyle="->", lw=1.2, color=C_PRIMARY))
    
    # Yes Branch (Left)
    rect_yes = patches.FancyBboxPatch((0.5, 0.2), 1.8, 0.6, boxstyle="round,pad=0.08", fc=C_LIGHT_BG, ec=C_WARN, lw=1.5)
    ax.add_patch(rect_yes)
    ax.text(1.4, 0.6, "触发黄色/红色警告", fontsize=9, fontweight='bold', color=C_WARN, ha='center')
    ax.text(1.4, 0.35, "UI面板红牌提示并重构", fontsize=7.5, color=C_TEXT, ha='center')
    
    # No Branch (Right)
    rect_no = patches.FancyBboxPatch((5.8, 0.2), 1.8, 0.6, boxstyle="round,pad=0.08", fc=C_LIGHT_BG, ec=C_OK, lw=1.5)
    ax.add_patch(rect_no)
    ax.text(6.7, 0.6, "绿标合规通过", fontsize=9, fontweight='bold', color=C_OK, ha='center')
    ax.text(6.7, 0.35, "记录入库并流转绘图", fontsize=7.5, color=C_TEXT, ha='center')
    
    # Arrows from Decision
    ax.annotate("是 (超标)", xy=(1.4, 0.9), xytext=(3.0, 1.5), arrowprops=dict(arrowstyle="->", lw=1.2, color=C_WARN))
    ax.annotate("否 (合规)", xy=(6.7, 0.9), xytext=(5.0, 1.5), arrowprops=dict(arrowstyle="->", lw=1.2, color=C_OK))
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "compliance_audit_flow.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated compliance_audit_flow.png")

if __name__ == "__main__":
    draw_system_architecture()
    draw_negotiation_workflow()
    draw_compliance_audit_flow()
