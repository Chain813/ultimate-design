# -*- coding: utf-8 -*-
# tools/drawings/dr_114.py
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

NO_FRAME = True

def wrap_text_by_pixels(text, font, max_width, draw):
    forbidden_start = set("，。、；：？！）】』」》〉〕”’）,.?!;:)】")
    forbidden_end = set("（【『「《〈〔“‘（([【")
    
    def get_width(t):
        try:
            return draw.textlength(t, font=font)
        except AttributeError:
            try:
                left, top, right, bottom = font.getbbox(t)
                return right - left
            except AttributeError:
                return font.getsize(t)[0]

    lines = []
    for block in text.split('\n'):
        if not block:
            lines.append("")
            continue
        current_line = ""
        i = 0
        while i < len(block):
            char = block[i]
            test_line = current_line + char
            if get_width(test_line) <= max_width:
                current_line = test_line
                i += 1
            else:
                if not current_line:
                    current_line = char
                    i += 1
                else:
                    if block[i] in forbidden_start:
                        current_line += block[i]
                        i += 1
                        while i < len(block) and block[i] in forbidden_start:
                            current_line += block[i]
                            i += 1
                    while current_line and current_line[-1] in forbidden_end:
                        i -= 1
                        current_line = current_line[:-1]
                if current_line:
                    lines.append(current_line)
                current_line = ""
        if current_line:
            lines.append(current_line)
    return lines

def resize_and_crop(img, target_w, target_h):
    w, h = img.size
    target_aspect = target_w / target_h
    aspect = w / h
    if aspect > target_aspect:
        # Image is too wide: crop left/right
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # Image is too tall: crop top/bottom
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

def get_or_generate_satellite_image(STATIC_DIR):
    # Depend on DR-103
    filename = "DR-103_市一中北侧-现状卫星图.png"
    drawing_type = "市一中北侧-现状卫星图"
    code = "DR-103"
    out_path = STATIC_DIR / "atlas" / filename
    
    if not out_path.exists():
        print(f"[DR-114] Dependency satellite sheet {filename} not found, generating it now...")
        from tools.draw_scope_map import draw_spatial_map, process_a3_layout
        temp_drawn = STATIC_DIR / f"temp_drawn_map_{code}.png"
        try:
            view_w = draw_spatial_map(temp_drawn, drawing_type=drawing_type)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            process_a3_layout(temp_drawn, out_path, view_w, drawing_type=drawing_type, title=drawing_type, drawing_number=code)
        finally:
            if temp_drawn.exists():
                temp_drawn.unlink()
    return Image.open(out_path)

def get_layout_image(STATIC_DIR):
    # Search for DR-108_市一中北侧-改造总平面图 in atlas first, then backup
    fuzzy_name = "市一中北侧-改造总平面图"
    
    # Try atlas first
    atlas_dir = STATIC_DIR / "atlas"
    if atlas_dir.exists():
        for root, dirs, files in os.walk(str(atlas_dir)):
            for f in files:
                if f.lower().endswith(".png") and fuzzy_name in f:
                    return Image.open(Path(root) / f)
                    
    # Try backup
    backup_dir = STATIC_DIR / "atlas_backup"
    if backup_dir.exists():
        for root, dirs, files in os.walk(str(backup_dir)):
            for f in files:
                if f.lower().endswith(".png") and fuzzy_name in f:
                    return Image.open(Path(root) / f)
                    
    # Fallback if nothing found
    raise FileNotFoundError(f"[DR-114] Cannot find layout plan image for {fuzzy_name}")

def draw_map_early(output_path, view_w, view_h, STATIC_DIR):
    print("Drawing DR-114 Before-and-After Comparison Sheet...")
    
    # 1. Load Left & Right maps
    try:
        sat_sheet = get_or_generate_satellite_image(STATIC_DIR)
        # Crop out map area (48, 222, 1568, 1505) from standard sheet to get pure map
        sat_map = sat_sheet.crop((48, 222, 1568, 1505))
    except Exception as e:
        print(f"[DR-114] Failed to load satellite image: {e}. Using empty canvas.")
        sat_map = Image.new("RGB", (1705, 1369), color=(240, 240, 240))
        
    try:
        layout_map = get_layout_image(STATIC_DIR)
    except Exception as e:
        print(f"[DR-114] Failed to load layout image: {e}. Using empty canvas.")
        layout_map = Image.new("RGB", (1448, 1086), color=(240, 240, 240))

    # Resize both maps to fit card layout perfectly: 1000x800 px
    sat_map_resized = resize_and_crop(sat_map, 1000, 800)
    layout_map_resized = resize_and_crop(layout_map, 1000, 800)

    # 2. Setup A3 Main Canvas (2240x1584)
    img = Image.new("RGB", (2240, 1584), color=(248, 250, 252)) # slate-50
    draw = ImageDraw.Draw(img)

    # Fonts
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    font_bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
    try:
        font_large_title = ImageFont.truetype(font_bold_path, 36)
        font_card_title = ImageFont.truetype(font_bold_path, 20)
        font_desc_title = ImageFont.truetype(font_bold_path, 22)
        font_body = ImageFont.truetype(font_path, 18)
        font_body_bold = ImageFont.truetype(font_bold_path, 18)
        font_desc = ImageFont.truetype(font_path, 15)
    except IOError:
        font_large_title = font_card_title = font_desc_title = font_body = font_body_bold = font_desc = ImageFont.load_default()

    # Draw grid
    grid_spacing = 79.2
    for x in range(1, int(2240 / grid_spacing)):
        lx = int(x * grid_spacing)
        draw.line([(lx, 0), (lx, 1584)], fill=(226, 232, 240), width=1)
    for y in range(1, int(1584 / grid_spacing)):
        ly = int(y * grid_spacing)
        draw.line([(0, ly), (2240, ly)], fill=(226, 232, 240), width=1)

    # 3. Header Card (X: 32 to 2208, Y: 40 to 140)
    draw.rectangle([36, 44, 2212, 144], fill=(226, 232, 240)) # shadow
    draw.rectangle([32, 40, 2208, 140], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 40, 2208, 46], fill=(217, 119, 6)) # amber top line
    
    draw.text((55, 90), "市一中北侧地块 — 改造前后对比图", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((800, 90), "对比地块改造前后的空间状态与总平面布局形态。左侧为现状卫星图，右侧为改造后总平面图。", 
              fill=(100, 116, 139), font=font_desc, anchor="lm")

    # 4. Left Map Card (Before)
    draw.rectangle([36, 164, 1108, 1064], fill=(226, 232, 240)) # shadow
    draw.rectangle([32, 160, 1104, 1060], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 160, 1104, 166], fill=(217, 119, 6)) # amber top line
    draw.text((55, 195), "改造前现状卫星图 / BEFORE SATELLITE IMAGE", fill=(15, 23, 42), font=font_card_title, anchor="lm")
    # Paste Map
    img.paste(sat_map_resized, (68, 230))

    # 5. Right Map Card (After)
    draw.rectangle([1140, 164, 2212, 1064], fill=(226, 232, 240)) # shadow
    draw.rectangle([1136, 160, 2208, 1060], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1136, 160, 2208, 166], fill=(16, 185, 129)) # emerald top line
    draw.text((1159, 195), "改造后总平面图 / AFTER MASTER PLAN", fill=(15, 23, 42), font=font_card_title, anchor="lm")
    # Paste Map
    img.paste(layout_map_resized, (1172, 230))

    # 6. Left Bottom Card (Before Diagnosis Notes)
    draw.rectangle([36, 1084, 1108, 1544], fill=(226, 232, 240)) # shadow
    draw.rectangle([32, 1080, 1104, 1540], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 1080, 1104, 1086], fill=(217, 119, 6)) # amber top line
    draw.text((55, 1115), "现状诊断说明 / DIAGNOSIS NOTES", fill=(217, 119, 6), font=font_desc_title, anchor="lm")
    
    sat_notes = [
        "1. 遥感影像反映场地现状生态绿化较差，内部硬质地表占比高，大跨度工业大棚与仓储设施痕迹清晰可见。",
        "2. 场地贴邻铁路或主要交通干道，内部机动车路网密度较低，大部分空间被低能级建筑或闲置空地覆盖。",
        "3. 影像表明场地内部绿化断续，未与东侧伊通河生态走廊建立连贯性，周边景观风貌缺乏系统设计与织补。"
    ]
    y_pos = 1150
    for note in sat_notes:
        wrapped = wrap_text_by_pixels(note, font_body, 1020, draw)
        for line in wrapped:
            draw.text((55, y_pos), line, fill=(71, 85, 105), font=font_body)
            y_pos += 30
        y_pos += 12

    # 7. Right Bottom Card (After Design Notes)
    draw.rectangle([1140, 1084, 2212, 1544], fill=(226, 232, 240)) # shadow
    draw.rectangle([1136, 1080, 2208, 1540], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1136, 1080, 2208, 1086], fill=(16, 185, 129)) # emerald top line
    draw.text((1159, 1115), "改造设计定位 / DESIGN PROPOSALS", fill=(16, 185, 129), font=font_desc_title, anchor="lm")
    
    design_notes = [
        "规划方案：市一中北侧地块定位于“全龄共享生活社区”。改造侧重于老旧小区服务短板修补，完善适老与托育公共配套，营造共享开敞绿地空间。",
        "1. 服务补短：重点配建适老化活动室与幼托服务中心，填补周边社区全龄级公共服务配套盲区。",
        "2. 空间缝合：打通封闭小区间的割裂边界，重构开放连通的社区微循环网络，增设口袋绿地与交往节点。",
        "3. 环境织补：修补破损硬质铺装，增加环境绿视率与全龄无障碍通行步道，全面改善社区户外活动风貌。"
    ]
    y_pos = 1150
    for i, note in enumerate(design_notes):
        f_style = font_body_bold if i == 0 else font_body
        color_style = (15, 23, 42) if i == 0 else (71, 85, 105)
        wrapped = wrap_text_by_pixels(note, f_style, 1020, draw)
        for line in wrapped:
            draw.text((1159, y_pos), line, fill=color_style, font=f_style)
            y_pos += 30
        y_pos += 12

    # Save to output_path
    img.save(output_path)
    print(f"[DR-114] Comparison drawing generated successfully: {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
