# tools/rearrange_tables_landscape.py
import os
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ATLAS_DIR = ROOT / "static" / "atlas"

def rearrange_table_to_landscape(filename, output_filename):
    img_path = ATLAS_DIR / filename
    out_path = ATLAS_DIR / output_filename
    
    if not img_path.exists():
        print(f"Error: {filename} does not exist.")
        return False
        
    print(f"Rearranging {filename} -> {output_filename}...")
    img = Image.open(img_path)
    w, h = img.size
    pixels = img.load()
    
    # 1. Scan multiple y-coordinates to find table borders left_x and right_x
    left_x = w
    right_x = 0
    for y_scan in range(int(h * 0.2), int(h * 0.8), int(h * 0.05)):
        # find first non-white pixel
        for x in range(0, w):
            r, g, b = pixels[x, y_scan][:3]
            if r < 245 or g < 245 or b < 245:
                if x < left_x:
                    left_x = x
                break
        # find last non-white pixel
        for x in range(w - 1, -1, -1):
            r, g, b = pixels[x, y_scan][:3]
            if r < 245 or g < 245 or b < 245:
                if x > right_x:
                    right_x = x
                break
                
    # Add a tiny safety margin
    left_x = max(0, left_x - 2)
    right_x = min(w - 1, right_x + 2)
    orig_table_w = right_x - left_x
    print(f" -> Table border detected: left_x={left_x}, right_x={right_x}, width={orig_table_w}")
    
    # 2. Find all horizontal lines
    lines = []
    y = 100
    while y < h - 100:
        grey_count = 0
        step = 5
        samples = range(left_x + 10, right_x - 10, step)
        for x in samples:
            r, g, b = pixels[x, y][:3]
            if r < 240 or g < 240 or b < 240:
                grey_count += 1
        if grey_count > len(samples) * 0.85:
            lines.append(y)
            y += 12
        else:
            y += 1
            
    print(f" -> Detected {len(lines)} horizontal lines: {lines}")
    
    if len(lines) < 3:
        print(" -> Error: Could not detect enough table grid lines. Skipping rearrangement.")
        return False
        
    # N rows = len(lines) - 2
    N = len(lines) - 2
    print(f" -> Total rows detected in table: {N}")
    
    # Split rows
    left_rows_count = (N + 1) // 2
    mid_idx = 1 + left_rows_count
    
    h_header = lines[1] - lines[0]
    h_left_rows = lines[mid_idx] - lines[1]
    h_right_rows = lines[N+1] - lines[mid_idx]
    
    # Crop components
    header_img = img.crop((left_x, lines[0], right_x, lines[1]))
    left_rows_img = img.crop((left_x, lines[1], right_x, lines[mid_idx]))
    right_rows_img = img.crop((left_x, lines[mid_idx], right_x, lines[N+1]))
    
    # Assemble left column
    left_col_img = Image.new("RGB", (orig_table_w, h_header + h_left_rows), (255, 255, 255))
    left_col_img.paste(header_img, (0, 0))
    left_col_img.paste(left_rows_img, (0, h_header))
    
    # Assemble right column
    right_col_img = Image.new("RGB", (orig_table_w, h_header + h_right_rows), (255, 255, 255))
    right_col_img.paste(header_img, (0, 0))
    right_col_img.paste(right_rows_img, (0, h_header))
    
    # Create landscape canvas (5370, 3796)
    canvas_w = 5370
    canvas_h = 3796
    landscape_img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    
    # Paste title
    title_img = img.crop((0, 0, w, lines[0]))
    landscape_img.paste(title_img, (0, 0))
    
    # Calculate scale factor to fit horizontally
    gap = 120
    side_margins = 160
    dest_table_w = (canvas_w - 2 * side_margins - gap) // 2
    S = dest_table_w / orig_table_w
    
    print(f" -> Rescaling columns with factor S={S:.4f} (width: {orig_table_w} -> {dest_table_w})")
    
    # Scale columns
    left_scaled = left_col_img.resize((dest_table_w, int(left_col_img.height * S)), Image.Resampling.LANCZOS)
    right_scaled = right_col_img.resize((dest_table_w, int(right_col_img.height * S)), Image.Resampling.LANCZOS)
    
    # Center vertically in remaining space
    remaining_h = canvas_h - lines[0]
    max_scaled_h = max(left_scaled.height, right_scaled.height)
    start_y = lines[0] + (remaining_h - max_scaled_h) // 2
    
    # Calculate horizontal positions
    left_x_pos = side_margins
    right_x_pos = side_margins + dest_table_w + gap
    
    # Paste columns
    landscape_img.paste(left_scaled, (left_x_pos, start_y))
    landscape_img.paste(right_scaled, (right_x_pos, start_y))
    
    # Save output
    landscape_img.save(out_path, "PNG")
    print(f" -> Successfully saved landscape copy to {out_path}")
    return True

def main():
    rearrange_table_to_landscape("A原始数据.png", "A原始数据_横版.png")
    rearrange_table_to_landscape("A数学公式.png", "A数学公式_横版.png")
    rearrange_table_to_landscape("A核心代码清单.png", "A核心代码清单_横版.png")

if __name__ == "__main__":
    main()
