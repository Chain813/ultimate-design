import os
import sys
from PIL import Image, ImageDraw, ImageFont
from src.config.paths import STATIC_DIR

# Output Directory
OUTPUT_DIR = str(STATIC_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Font Settings
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"  # Microsoft YaHei
FONT_BOLD_PATH = r"C:\Windows\Fonts\msyhbd.ttc"  # Microsoft YaHei Bold

if not os.path.exists(FONT_PATH):
    FONT_PATH = "arial.ttf"
if not os.path.exists(FONT_BOLD_PATH):
    FONT_BOLD_PATH = FONT_PATH

# -------------------------------------------------------------
# Utility Function to Draw Bezier-like Smooth Branch Line
# -------------------------------------------------------------
def draw_branch_line(draw, start, end, color, width=2):
    mid_x = (start[0] + end[0]) // 2
    draw.line([start, (mid_x, start[1]), (mid_x, end[1]), end], fill=color, width=width)

def generate_urban_rural_planning_mindmap():
    print("Generating urban and rural planning mindmap...")
    canvas_w = 1920
    canvas_h = 1200
    img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 32)
        subtitle_font = ImageFont.truetype(FONT_PATH, 16)
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, 17)
        node_desc_font = ImageFont.truetype(FONT_PATH, 13)
        section_title_font = ImageFont.truetype(FONT_BOLD_PATH, 18)
    except:
        title_font = subtitle_font = node_title_font = node_desc_font = section_title_font = ImageFont.load_default()

    # Header
    draw.rectangle([0, 0, canvas_w, 80], fill=(241, 245, 249))
    draw.line([(0, 80), (canvas_w, 80)], fill=(203, 213, 225), width=2)
    draw.text((40, 20), "城乡规划实务工作流与成果图册思维导图", fill=(15, 23, 42), font=title_font)
    draw.text((1500, 32), "城乡规划专业视角的法定与设计流程", fill=(100, 116, 139), font=subtitle_font)

    # ROOT NODE SCHEME
    ROOT_SCHEME = {"fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138)}

    # COLOR PALETTES FOR STAGES
    # 0 & 3: Teal (现状调研 & 专项规划)
    # 1 & 4: Purple (定位策划 & 重点深化)
    # 2 & 5: Amber (空间结构 & 开发实施)
    PALETTES = [
        {"fill": (240, 253, 250), "stroke": (13, 148, 136), "text": (15, 118, 110), "title": "阶段一：现状调研与多维诊断"},
        {"fill": (250, 245, 255), "stroke": (168, 85, 247), "text": (107, 33, 168), "title": "阶段二：发展定位与目标策划"},
        {"fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (180, 83, 9), "title": "阶段三：空间结构与总体布局"},
        {"fill": (240, 253, 250), "stroke": (13, 148, 136), "text": (15, 118, 110), "title": "阶段四：专项系统规划设计"},
        {"fill": (250, 245, 255), "stroke": (168, 85, 247), "text": (107, 33, 168), "title": "阶段五：重点地段深化城市设计"},
        {"fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (180, 83, 9), "title": "阶段六：开发实施与规划导则"}
    ]

    # LEAF CARDS CONFIGURATION
    # Left Side: Branch 0, 1, 2
    # Right Side: Branch 3, 4, 5
    LEAF_CARDS = [
        # Branch 0
        {"branch": 0, "side": "left", "title": "用地与建筑现状测绘", "bullets": ["• 土地利用现状分类普查与平衡表编制", "• 现状建筑年代、层数与质量评级分类"]},
        {"branch": 0, "side": "left", "title": "道路交通与市政设施评估", "bullets": ["• 道路网通达度、公交站点覆盖率评估", "• 给排水、电力、供热等管网容量测算"]},
        {"branch": 0, "side": "left", "title": "历史文化与自然本底调查", "bullets": ["• 历史风貌保护建筑名录与文脉遗存普查", "• 水体、山体与生态保护红线边界确定"]},
        {"branch": 0, "side": "left", "title": "公众参与与社会诉求收集", "bullets": ["• 社区居民更新意愿问卷与入户访谈", "• 多方主体利益诉求整理与痛点清单分析"]},

        # Branch 1
        {"branch": 1, "side": "left", "title": "城市性质与核心功能定位", "bullets": ["• 确定城市或街区发展愿景与主导职能", "• 明确长远发展目标与战略转型方向"]},
        {"branch": 1, "side": "left", "title": "产业空间布局与经济测算", "bullets": ["• 主导产业选址与空间载体容量配置", "• 项目开发投资成本估算与财务可行性评估"]},
        {"branch": 1, "side": "left", "title": "规划指标体系拟定", "bullets": ["• 确定容积率上限与建筑密度总量控制", "• 明确绿地率、建筑限高与职住平衡比例"]},

        # Branch 2
        {"branch": 2, "side": "left", "title": "空间结构与功能分区规划", "bullets": ["• 规划“一轴多心”等骨架与组团边界", "• 划定城镇开发边界与限制建设区"]},
        {"branch": 2, "side": "left", "title": "用地配置与总平面布局", "bullets": ["• 进行各类规划用地性质优化调整与平衡", "• 绘制概念总平面草图并细化路网布局"]},
        {"branch": 2, "side": "left", "title": "规划“四线”刚性控制", "bullets": ["• 道路红线、绿地绿线、市政黄线划分", "• 历史文化紫线等刚性空间约束划定"]},

        # Branch 3
        {"branch": 3, "side": "right", "title": "综合交通与慢行网络规划", "bullets": ["• 道路红线拓宽、人车分流与步行街规划", "• 绿道、单车径等城市慢性绿网系统设计"]},
        {"branch": 3, "side": "right", "title": "开敞空间与防灾避险系统", "bullets": ["• 绿地公园服务半径计算与避难场地组织", "• 亲水平台与微型雨水花园生态组织"]},
        {"branch": 3, "side": "right", "title": "天际线轮廓与视线通廊控制", "bullets": ["• 空间高度梯度控制，留出主要视廊", "• 塑造滨水或面山的美观天际线界面"]},
        {"branch": 3, "side": "right", "title": "历史风貌与特色街区保护", "bullets": ["• 核心保护区与建设控制地带划定", "• 建筑高度、材料色彩与历史立面整治引导"]},

        # Branch 4
        {"branch": 4, "side": "right", "title": "重点更新项目建筑形态设计", "bullets": ["• 重点更新地块的建筑体量与空间形态组织", "• 节点人视角度立面设计与三维意象塑造"]},
        {"branch": 4, "side": "right", "title": "街道公共空间与景观详细设计", "bullets": ["• 口袋公园、街道铺装、标识系统设计", "• 街道绿化树种、公共家具与照明系统配置"]},
        {"branch": 4, "side": "right", "title": "地块功能画像与微更新导则", "bullets": ["• 地块混合用途控制与立面退让控制", "• 老旧建筑改造、加建、修缮规则分类指引"]},

        # Branch 5
        {"branch": 5, "side": "right", "title": "留改拆分区与开发时序划分", "bullets": ["• 拆除重建/保留整治/更新改造分区划定", "• 明确近期、中期、远期分期开发行动计划"]},
        {"branch": 5, "side": "right", "title": "控制性规划条文与导则编制", "bullets": ["• 制定地块控制指标的法定管理条文", "• 汇编城市设计弹性引导图集与设计指南"]},
        {"branch": 5, "side": "right", "title": "投资估算与运营管理机制", "bullets": ["• 更新资金筹措模式评估与多渠道招商", "• 社区共治管理机制与长期运营维护方案"]}
    ]

    # Canvas Dimensions & Layout Coords
    # Root centered at (960, 600)
    root_x = 960
    root_y = 600
    root_w, root_h = 320, 80

    # Left Side Coordinates
    left_branch_x = 480
    left_leaf_x = 40

    # Right Side Coordinates
    right_branch_x = 1160
    right_leaf_x = 1500

    # General Node Dimensions
    branch_w, branch_h = 280, 60
    leaf_w, leaf_h = 380, 85
    leaf_spacing = 12

    # Assign Y coordinates for all leaves
    # Left side has 10 leaves, Right side has 10 leaves
    left_leaves = [card for card in LEAF_CARDS if card["side"] == "left"]
    right_leaves = [card for card in LEAF_CARDS if card["side"] == "right"]

    leaf_start_y = 120
    for i, card in enumerate(left_leaves):
        card["y"] = leaf_start_y + i * (leaf_h + leaf_spacing)

    for i, card in enumerate(right_leaves):
        card["y"] = leaf_start_y + i * (leaf_h + leaf_spacing)

    # -------------------------------------------------------------
    # Drawing Connections (Pass 1)
    # -------------------------------------------------------------
    # Draw Root to Left Branches
    for b_idx in [0, 1, 2]:
        palette = PALETTES[b_idx]
        b_leaves = [c for c in left_leaves if c["branch"] == b_idx]
        b_y = sum(c["y"] + leaf_h // 2 for c in b_leaves) // len(b_leaves)
        
        # Connection: Root -> Branch
        draw_branch_line(draw, (root_x - root_w // 2, root_y), (left_branch_x + branch_w, b_y), color=(203, 213, 225), width=2)

        # Connection: Branch -> Leaves
        for card in b_leaves:
            draw_branch_line(draw, (left_branch_x, b_y), (left_leaf_x + leaf_w, card["y"] + leaf_h // 2), color=(226, 232, 240), width=2)

    # Draw Root to Right Branches
    for b_idx in [3, 4, 5]:
        palette = PALETTES[b_idx]
        b_leaves = [c for c in right_leaves if c["branch"] == b_idx]
        b_y = sum(c["y"] + leaf_h // 2 for c in b_leaves) // len(b_leaves)
        
        # Connection: Root -> Branch
        draw_branch_line(draw, (root_x + root_w // 2, root_y), (right_branch_x, b_y), color=(203, 213, 225), width=2)

        # Connection: Branch -> Leaves
        for card in b_leaves:
            draw_branch_line(draw, (right_branch_x + branch_w, b_y), (right_leaf_x, card["y"] + leaf_h // 2), color=(226, 232, 240), width=2)

    # -------------------------------------------------------------
    # Drawing Nodes (Pass 2)
    # -------------------------------------------------------------
    # 1. Root Node
    draw.rounded_rectangle([root_x - root_w // 2, root_y - root_h // 2, root_x + root_w // 2, root_y + root_h // 2], radius=10, fill=ROOT_SCHEME["fill"], outline=ROOT_SCHEME["stroke"], width=3)
    # Root Text (Centered)
    root_text = "城乡规划与设计实务工作流"
    rt_w = section_title_font.getbbox(root_text)[2] - section_title_font.getbbox(root_text)[0]
    draw.text((root_x - rt_w // 2, root_y - 12), root_text, fill=ROOT_SCHEME["text"], font=section_title_font)

    # 2. Branch and Leaf Nodes (Left Side)
    for b_idx in [0, 1, 2]:
        palette = PALETTES[b_idx]
        b_leaves = [c for c in left_leaves if c["branch"] == b_idx]
        b_y = sum(c["y"] + leaf_h // 2 for c in b_leaves) // len(b_leaves)

        # Draw Branch Box
        draw.rounded_rectangle([left_branch_x, b_y - branch_h // 2, left_branch_x + branch_w, b_y + branch_h // 2], radius=8, fill=palette["fill"], outline=palette["stroke"], width=2)
        # Center text inside branch
        bt_w = node_title_font.getbbox(palette["title"])[2] - node_title_font.getbbox(palette["title"])[0]
        draw.text((left_branch_x + (branch_w - bt_w) // 2, b_y - 10), palette["title"], fill=palette["text"], font=node_title_font)

        # Draw Leaves
        for card in b_leaves:
            draw.rounded_rectangle([left_leaf_x, card["y"], left_leaf_x + leaf_w, card["y"] + leaf_h], radius=6, fill=(255, 255, 255), outline=palette["stroke"], width=1)
            # Left stripe
            draw.rectangle([left_leaf_x, card["y"], left_leaf_x + 8, card["y"] + leaf_h], fill=palette["stroke"])
            
            # Title
            draw.text((left_leaf_x + 18, card["y"] + 8), card["title"], fill=(15, 23, 42), font=node_title_font)
            # Bullets
            ty = card["y"] + 32
            for bullet in card["bullets"]:
                draw.text((left_leaf_x + 18, ty), bullet, fill=(71, 85, 105), font=node_desc_font)
                ty += 18

    # 3. Branch and Leaf Nodes (Right Side)
    for b_idx in [3, 4, 5]:
        palette = PALETTES[b_idx]
        b_leaves = [c for c in right_leaves if c["branch"] == b_idx]
        b_y = sum(c["y"] + leaf_h // 2 for c in b_leaves) // len(b_leaves)

        # Draw Branch Box
        draw.rounded_rectangle([right_branch_x, b_y - branch_h // 2, right_branch_x + branch_w, b_y + branch_h // 2], radius=8, fill=palette["fill"], outline=palette["stroke"], width=2)
        # Center text
        bt_w = node_title_font.getbbox(palette["title"])[2] - node_title_font.getbbox(palette["title"])[0]
        draw.text((right_branch_x + (branch_w - bt_w) // 2, b_y - 10), palette["title"], fill=palette["text"], font=node_title_font)

        # Draw Leaves
        for card in b_leaves:
            draw.rounded_rectangle([right_leaf_x, card["y"], right_leaf_x + leaf_w, card["y"] + leaf_h], radius=6, fill=(255, 255, 255), outline=palette["stroke"], width=1)
            # Left stripe
            draw.rectangle([right_leaf_x, card["y"], right_leaf_x + 8, card["y"] + leaf_h], fill=palette["stroke"])
            
            # Title
            draw.text((right_leaf_x + 18, card["y"] + 8), card["title"], fill=(15, 23, 42), font=node_title_font)
            # Bullets
            ty = card["y"] + 32
            for bullet in card["bullets"]:
                draw.text((right_leaf_x + 18, ty), bullet, fill=(71, 85, 105), font=node_desc_font)
                ty += 18

    # Bottom Legend / Footer Panel
    draw.rectangle([0, canvas_h - 60, canvas_w, canvas_h], fill=(248, 250, 252))
    draw.line([(0, canvas_h - 60), (canvas_w, canvas_h - 60)], fill=(226, 232, 240), width=1)
    footer_text = "提示：本工作流涵盖了总体规划、控制性与修建性详细规划、城市设计及其实施阶段的核心内容体系。"
    draw.text((40, canvas_h - 40), footer_text, fill=(71, 85, 105), font=subtitle_font)

    # Save
    img.save(os.path.join(OUTPUT_DIR, "urban_rural_planning_mindmap.png"), "PNG")
    print("Urban and rural planning mindmap generated successfully!")

if __name__ == "__main__":
    generate_urban_rural_planning_mindmap()
