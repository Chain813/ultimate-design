# -*- coding: utf-8 -*-
"""Cropping tool to extract the map regions from the scanned PDF/JPEG master plan pages."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_DIR = ROOT / "static" / "extracted_images"

def auto_crop_map(img_path, output_path):
    print(f"Scanning and cropping {img_path.name}...")
    try:
        img = Image.open(img_path)
        w, h = img.size
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Downsample to speed up scanning
        scale = 8
        small_img = img.resize((w // scale, h // scale))
        sw, sh = small_img.size
        
        left = sw
        right = 0
        top = sh
        bottom = 0
        
        pixels = small_img.load()
        for y in range(sh):
            for x in range(sw):
                r, g, b = pixels[x, y]
                # A pixel belongs to the map if it's not paper white/light gray
                if r < 242 or g < 242 or b < 242:
                    if x < left: left = x
                    if x > right: right = x
                    if y < top: top = y
                    if y > bottom: bottom = y
        
        # Add safety margin and scale back
        margin = 15
        left = max(0, (left - margin) * scale)
        right = min(w, (right + margin) * scale)
        top = max(0, (top - margin) * scale)
        bottom = min(h, (bottom + margin) * scale)
        
        # Perform crop
        cropped = img.crop((left, top, right, bottom))
        cropped.save(output_path, "PNG")
        print(f" -> Saved crop to {output_path.name} (Dimensions: {right-left}x{bottom-top})")
    except Exception as e:
        print(f" -> Error cropping {img_path.name}: {e}")

def main():
    targets = [
        ("zg_p95_img1.jpeg", "zg_p95_crop.png"),
        ("zg_p96_img1.jpeg", "zg_p96_crop.png"),
        ("zg_p102_img1.jpeg", "zg_p102_crop.png"),
    ]
    for src_name, dst_name in targets:
        src_path = EXTRACTED_DIR / src_name
        dst_path = EXTRACTED_DIR / dst_name
        if src_path.exists():
            auto_crop_map(src_path, dst_path)
        else:
            print(f"Warning: Source file {src_name} not found in {EXTRACTED_DIR}")

if __name__ == "__main__":
    main()
