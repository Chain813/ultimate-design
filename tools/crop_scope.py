# tools/crop_scope.py
import sys
from PIL import Image, ImageDraw, ImageFont

def process_a3_layout(map_path, output_path):
    template = Image.open('static/a3_layout_preview.png').convert('RGB')
    map_img = Image.open(map_path).convert('RGB')
    windrose = Image.open('assets/长春市风玫瑰.png')
    
    # 1. 缩放地图并粘贴到主绘图区
    # 主绘图区坐标: x=183, y=289, w=1705, h=1369
    map_resized = map_img.resize((1705, 1369), Image.Resampling.LANCZOS)
    template.paste(map_resized, (183, 289))
    
    # 2. 清理右上角并贴入长春风玫瑰
    # 指针盒坐标: x=1890, y=291, w=420, h=315
    draw = ImageDraw.Draw(template)
    draw.rectangle([1891, 292, 2309, 605], fill=(255, 255, 255))
    
    wr_w, wr_h = windrose.size
    new_h = 200
    new_w = int(new_h * wr_w / wr_h)
    windrose_resized = windrose.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    wx = 1890 + (420 - new_w) // 2
    wy = 291 + 15
    template.paste(windrose_resized, (wx, wy), windrose_resized)
    
    # 3. 绘制精细的比例尺与文字
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    try:
        font_small = ImageFont.truetype(font_path, 14)
        font_title = ImageFont.truetype(font_path, 20)
        font_body = ImageFont.truetype(font_path, 15)
        font_tb = ImageFont.truetype(font_path, 18)
    except IOError:
        font_small = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_tb = ImageFont.load_default()
        
    draw.line([(2010, 545), (2190, 545)], fill=(0, 0, 0), width=2)
    draw.line([(2010, 540), (2010, 545)], fill=(0, 0, 0), width=2)
    draw.line([(2190, 540), (2190, 545)], fill=(0, 0, 0), width=2)
    draw.text((2005, 552), "0", fill=(72, 72, 74), font=font_small)
    draw.text((2175, 552), "500m", fill=(72, 72, 74), font=font_small)
    draw.text((2065, 523), "比例尺 1:1000", fill=(72, 72, 74), font=font_small)
    
    # 4. 填充规划说明
    draw.rectangle([184, 1661, 1887, 1815], fill=(248, 250, 252))
    draw.text((210, 1675), "规划说明与设计指标 (Notes & Key Indicators)", fill=(29, 29, 31), font=font_title)
    draw.text((210, 1710), "1. 本图为长春伪满皇宫周边历史街区微更新设计范围图，研究范围约150公顷。本图按照A3标准图纸排版与比例设计规范绘制。", fill=(72, 72, 74), font=font_body)
    draw.text((210, 1738), "2. 规划策略：重点保护历史文化街区完整性，合理置换中车低效工业用地，提升历史风貌街区空间活力。", fill=(72, 72, 74), font=font_body)
    draw.text((210, 1766), "3. 设计指标：规划范围 150 公顷 | 历史风貌保护建筑 28 处 | 新增绿地与口袋公园 12.4 公顷", fill=(72, 72, 74), font=font_body)
    
    # 5. 更新图签中的图纸名称
    # 修改前: "图纸: 重点地块C06-03平面"
    draw.rectangle([1900, 1632, 2300, 1664], fill=(241, 245, 249))
    draw.text((1905, 1638), "图纸: 规划研究范围图", fill=(29, 29, 31), font=font_tb)
    
    template.save(output_path)
    print("A3 scope image processed successfully.")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python tools/crop_scope.py <map_path> <output_path>")
        sys.exit(1)
    process_a3_layout(sys.argv[1], sys.argv[2])
