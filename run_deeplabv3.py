import torch
import os
import numpy as np
import pandas as pd
from PIL import Image
from torchvision import transforms, models
from torchvision.models.segmentation import DeepLabV3_ResNet50_Weights

print("🧠 正在初始化计算机视觉推理引擎 (DeepLabV3-ResNet50)...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
weights = DeepLabV3_ResNet50_Weights.DEFAULT
model = models.segmentation.deeplabv3_resnet50(weights=weights).to(device).eval()

print(f"⚡ 模型已加载至运算设备: {device.type.upper()}")

# 图像张量化预处理 (保持你极其标准的写法)
preprocess = transforms.Compose([
    transforms.Resize((512, 1024)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def evaluate_gvi(image_path):
    """利用语义分割模型量化绿视率"""
    img = Image.open(image_path).convert('RGB')
    input_tensor = preprocess(img).unsqueeze(0).to(device)
    
    with torch.no_grad(): # 停止梯度计算，加速推理
        output = model(input_tensor)['out']
    
    # 提取像素级特征矩阵
    mask = torch.argmax(output, dim=1).squeeze().cpu().numpy()
    
    # Pascal VOC class 16 = potted plant (唯一植被类别)
    # 注意：VOC 仅含盆栽类，无法识别行道树/草坪，GVI 会偏低
    # 如需精确街景绿视率，推荐使用 cv_semantic_engine.py (Cityscapes class 8 = Vegetation)
    green_pixels = np.sum(mask == 16)
    return round((green_pixels / mask.size) * 100, 1)

# 🌟 核心对接：将路径换成我们刚刚抓取成功的绝对路径
root_path = r"data/StreetViews"
output_csv = r"data/GVI_Results_Analysis.csv"
results = []

print("🚀 开始执行高通量视觉推断 (分析 240 张街景切片)...")
for subdir, dirs, files in os.walk(root_path):
    # 只处理以 Point_ 开头的有效节点文件夹
    folder_name = os.path.basename(subdir)
    if not folder_name.startswith("Point_"):
        continue
        
    for file in files:
        if file.endswith(".jpg"):
            try:
                img_path = os.path.join(subdir, file)
                gvi = evaluate_gvi(img_path)
                results.append({"Folder": folder_name, "File": file, "GVI": gvi})
                print(f"✅ 成功测度: {folder_name} | {file} -> GVI: {gvi}%")
            except Exception as e:
                print(f"⚠️ 跳过损坏切片 {file}: {e}")

# 生成 Streamlit 沙盘第一页严格要求的 CSV 格式
if results:
    pd.DataFrame(results).to_csv(output_csv, index=False)
    print("\n" + "="*50)
    print(f"🎉 推理完成！共处理 {len(results)} 个视觉切片。")
    print(f"💾 核心测度报告已生成：\n{output_csv}")
    print("="*50)
else:
    print("❌ 未能生成结果，请检查 StreetViews 文件夹是否为空。")