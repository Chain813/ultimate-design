# -*- coding: utf-8 -*-
"""
Super-resolution script for the 5 design creed strategy drawings.
Uses caidas/swin2SR-lightweight-x2-64 on CPU.
"""
import os
# Avoid httpx IPv6 parsing bug with proxy settings
os.environ['NO_PROXY'] = '127.0.0.1,localhost'

import sys
import torch
import numpy as np
from PIL import Image
from pathlib import Path
from transformers import Swin2SRForImageSuperResolution, Swin2SRImageProcessor

ROOT = Path(__file__).resolve().parent.parent
ATLAS_DIR = ROOT / "static" / "atlas"

TARGET_FILES = [
    "DR-027_规划设计依据.png",
    "DR-028_规划设计原则.png",
    "DR-029_规划设计目标.png",
    "DR-030_规划设计定位.png",
    "DR-031_规划设计策略.png",
]

def main():
    print("="*60)
    print("开始执行 5 张设计图纸的深度学习超分辨率（Swin2SR 2x）")
    print("="*60)
    
    # 1. Load Swin2SR model
    model_id = "caidas/swin2SR-lightweight-x2-64"
    print(f"正在加载 Swin2SR 模型: {model_id} ...")
    try:
        processor = Swin2SRImageProcessor.from_pretrained(model_id)
        model = Swin2SRForImageSuperResolution.from_pretrained(model_id)
        print("模型加载成功！")
    except Exception as e:
        print(f"加载模型失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Process each file
    for filename in TARGET_FILES:
        filepath = ATLAS_DIR / filename
        if not filepath.exists():
            print(f"[警告] 文件不存在: {filename}，跳过。")
            continue
            
        print(f"\n[处理中] {filename} ...")
        try:
            # Load original image
            img = Image.open(filepath).convert("RGB")
            orig_w, orig_h = img.size
            print(f"  - 原始尺寸: {orig_w}x{orig_h}")
            
            # Save backup of the original image if not already backed up
            backup_path = ATLAS_DIR / f"{filepath.stem}_backup{filepath.suffix}"
            if not backup_path.exists():
                img.save(backup_path)
                print(f"  - 已备份原始图像至: {backup_path.name}")
            
            # Preprocess
            inputs = processor(img, return_tensors="pt")
            
            # Run inference
            print("  - 正在运行模型推断 (CPU)...")
            with torch.no_grad():
                outputs = model(**inputs)
                
            # Postprocess
            print("  - 后处理并进行尺寸裁剪...")
            output_tensor = outputs.reconstruction.data.squeeze().float().cpu().clamp_(0, 1).numpy()
            output_tensor = np.moveaxis(output_tensor, source=0, destination=-1)
            output_np = (output_tensor * 255.0).round().astype(np.uint8)
            
            output_img = Image.fromarray(output_np)
            
            # Crop to exact scale size (2x) to remove padding
            target_w = orig_w * 2
            target_h = orig_h * 2
            output_cropped = output_img.crop((0, 0, target_w, target_h))
            print(f"  - 超分后裁剪尺寸: {output_cropped.size}")
            
            # Save back to original path
            output_cropped.save(filepath)
            print(f"  [成功] 已保存超分图像: {filename}")
            
        except Exception as e:
            print(f"  [错误] 处理 {filename} 时发生异常: {e}", file=sys.stderr)
            
    print("\n" + "="*60)
    print("超分辨率处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
