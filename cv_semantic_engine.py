import os
import numpy as np
import pandas as pd
from PIL import Image
import torch
import torch.nn as nn
# 🚨 核心换装：引入专门处理城市街景的 Transformers 引擎
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation

print("🚀 启动 NVIDIA Segformer 城市级四维空间语义测度引擎 (360°全景聚合版)...")

# ==========================================
# 🧠 1. Cityscapes 19类标准语义映射字典 (这次绝对精准！)
# ==========================================
CITYSCAPES_CLASSES = {
    "Building": 2, "Wall": 3, "Fence": 4, "Pole": 5,
    "TrafficLight": 6, "TrafficSign": 7, "Vegetation": 8, "Sky": 10
}


def calculate_urban_indices(segmentation_mask):
    total_pixels = segmentation_mask.size
    pixels_veg = np.sum(segmentation_mask == CITYSCAPES_CLASSES["Vegetation"])
    pixels_sky = np.sum(segmentation_mask == CITYSCAPES_CLASSES["Sky"])
    pixels_building = np.sum(segmentation_mask == CITYSCAPES_CLASSES["Building"])
    pixels_wall = np.sum(segmentation_mask == CITYSCAPES_CLASSES["Wall"])
    pixels_fence = np.sum(segmentation_mask == CITYSCAPES_CLASSES["Fence"])
    pixels_pole = np.sum(segmentation_mask == CITYSCAPES_CLASSES["Pole"])
    pixels_sign = np.sum(segmentation_mask == CITYSCAPES_CLASSES["TrafficSign"])
    pixels_light = np.sum(segmentation_mask == CITYSCAPES_CLASSES["TrafficLight"])

    gvi = (pixels_veg / total_pixels) * 100
    svf = (pixels_sky / total_pixels) * 100
    enclosure = ((pixels_building + pixels_wall + pixels_veg) / total_pixels) * 100
    clutter = ((pixels_pole + pixels_sign + pixels_light + pixels_fence) / total_pixels) * 100

    return gvi, svf, enclosure, clutter


# ==========================================
# 🚁 2. AI 360° 全景推理流水线 (🚀 搭载断点续传与实时存档装甲)
# ==========================================
def run_pipeline():
    base_folder = "data/StreetViews"
    output_path = "data/GVI_Results_Analysis.csv"

    if not os.path.exists(base_folder):
        print(f"❌ 找不到总阵地: {base_folder}")
        return

    point_folders = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]
    if not point_folders:
        print(f"❌ 在 {base_folder} 文件夹里没有找到子文件夹！")
        return

    # 🛡️ 核心升级 1：雷达扫瞄历史存档 (断点续传机制)
    processed_ids = set()
    if os.path.exists(output_path):
        try:
            df_exist = pd.read_csv(output_path)
            if 'ID' in df_exist.columns:
                processed_ids = set(df_exist['ID'].astype(int))
                print(f"📦 侦测到历史战报！已自动锁定并跳过 {len(processed_ids)} 个已攻克节点！")
        except Exception as e:
            print(f"⚠️ 历史存档读取异常，将重新覆盖：{e}")

    print(f"🎯 侦测到 {len(point_folders)} 个坐标阵地，准备执行高通量扫描！")

    # 挂载 GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        print(f"🔥 已接管 NVIDIA GPU: 【{torch.cuda.get_device_name(0)}】")
    else:
        print("⚠️ 未检测到 GPU，使用 CPU 计算。")

    print("⏳ 正在唤醒 Nvidia Segformer 视觉引擎...")
    processor = SegformerImageProcessor.from_pretrained("nvidia/segformer-b0-finetuned-cityscapes-512-1024")
    model = SegformerForSemanticSegmentation.from_pretrained("nvidia/segformer-b0-finetuned-cityscapes-512-1024")
    model = model.to(device)
    model.eval()

    # 3. 逐个阵地 (Point_x) 突破！
    for folder_name in point_folders:
        point_path = os.path.join(base_folder, folder_name)
        node_id_str = ''.join(filter(str.isdigit, folder_name))
        if not node_id_str: continue
        node_id = int(node_id_str)

        # 🛡️ 核心升级 2：智能战术规避
        if node_id in processed_ids:
            print(f"⏩ 节点 {node_id} 情报已在库中，战术闪避，直接跳过！")
            continue

        images = [f for f in os.listdir(point_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not images: continue

        point_gvi, point_svf, point_enclosure, point_clutter = [], [], [], []

        for img_name in images:
            try:
                img_path = os.path.join(point_path, img_name)
                input_image = Image.open(img_path).convert("RGB")

                inputs = processor(images=input_image, return_tensors="pt").to(device)
                with torch.no_grad():
                    outputs = model(**inputs)

                logits = outputs.logits
                upsampled_logits = nn.functional.interpolate(
                    logits, size=input_image.size[::-1], mode="bilinear", align_corners=False
                )
                mask = upsampled_logits.argmax(dim=1)[0].cpu().numpy()

                gvi, svf, enclosure, clutter = calculate_urban_indices(mask)
                point_gvi.append(gvi)
                point_svf.append(svf)
                point_enclosure.append(enclosure)
                point_clutter.append(clutter)
            except Exception as e:
                print(f"⚠️ 图片 {img_name} 解析失败: {e}")

        # 🎯 核心升级 3：火力聚合与【实时落盘】
        if point_gvi:
            avg_gvi = round(np.mean(point_gvi), 2)
            avg_svf = round(np.mean(point_svf), 2)
            avg_enclosure = round(np.mean(point_enclosure), 2)
            avg_clutter = round(np.mean(point_clutter), 2)

            # 组装单条战报
            new_data = pd.DataFrame([{
                "ID": node_id, "GVI": avg_gvi, "SVF": avg_svf,
                "Enclosure": avg_enclosure, "Clutter": avg_clutter
            }])

            # 🚨 实时存档魔法：以 'a' (追加) 模式写入 CSV。
            # 如果是该文件第一次创建，就写入表头；如果已经存在，就直接接在末尾写数据！
            new_data.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)

            print(
                f"✅ 节点 {node_id} ({len(images)}图) -> 绿:{avg_gvi}% | 天:{avg_svf}% | 围:{avg_enclosure}% | 乱:{avg_clutter}% (💾 已实时存档)")

    print(f"\n🎉 辖区内所有节点扫荡完毕！数据安全存放于：{output_path}")

if __name__ == "__main__":
    run_pipeline()