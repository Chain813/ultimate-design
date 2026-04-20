import pandas as pd
import numpy as np
import os
import math
import time
import json
import yaml
from collections import Counter
import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw
import streamlit as st
import jieba
from src.utils.geo_transform import bd09_to_wgs84

# ==========================================
# ⚙️ 配置文件及本地 RAG 知识库装载器
# ==========================================
@st.cache_resource
def load_global_config():
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {}

@st.cache_resource
def load_rag_knowledge():
    config = load_global_config()
    rag_path = config.get("data", {}).get("rag_knowledge_path", "data/rag_knowledge.json")
    try:
        with open(rag_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ==========================================
# 🎭 全局演示模式控制
# ==========================================
def is_demo_mode():
    return st.session_state.get("demo_mode", False)


# ==========================================
# 📊 HUD 动态数据统计引擎
# ==========================================
@st.cache_data
def get_hud_statistics():
    stats = {}
    try:
        stats["poi_count"] = len(pd.read_csv("data/Changchun_POI_Real.csv", encoding='utf-8-sig'))
    except Exception:
        stats["poi_count"] = "N/A"
    try:
        stats["nlp_count"] = len(pd.read_csv("data/CV_NLP_RawData.csv", encoding='utf-8-sig'))
    except Exception:
        stats["nlp_count"] = "N/A"
    try:
        stats["gvi_count"] = len(pd.read_csv("data/GVI_Results_Analysis.csv"))
    except Exception:
        stats["gvi_count"] = "N/A"
    try:
        with open("data/shp/Boundary_Scope.geojson", 'r', encoding='utf-8') as f:
            geo = json.load(f)
        total_area_ha = 0
        for feat in geo.get("features", []):
            coords = feat["geometry"]["coordinates"][0]
            n = len(coords)
            area_deg = 0
            for i in range(n):
                j = (i + 1) % n
                area_deg += coords[i][0] * coords[j][1]
                area_deg -= coords[j][0] * coords[i][1]
            area_deg = abs(area_deg) / 2
            total_area_ha += area_deg * 80 * 111 * 100
        stats["boundary_ha"] = round(total_area_ha, 1)
    except Exception:
        stats["boundary_ha"] = "~156.4"
    return stats


# ==========================================
# 🌳 模块 1：空间物理测度计算引擎
# ==========================================
@st.cache_data
def get_spatial_data():
    base_path = "data/Changchun_Precise_Points.xlsx"
    gvi_path = "data/GVI_Results_Analysis.csv"
    if not os.path.exists(base_path): base_path = "../" + base_path
    if not os.path.exists(gvi_path): gvi_path = "../" + gvi_path

    try:
        df_base = pd.read_excel(base_path)
        df_gvi = pd.read_csv(gvi_path)
        if 'Folder' in df_gvi.columns:
            df_gvi['ID'] = df_gvi['Folder'].str.replace('Point_', '').astype(int)
            df_gvi = df_gvi.groupby('ID').mean().reset_index()
        df = pd.merge(df_base, df_gvi, on='ID', how='inner')
    except Exception:
        lngs = np.random.normal(loc=125.3517, scale=0.005, size=150)
        lats = np.random.normal(loc=43.9116, scale=0.005, size=150)
        df = pd.DataFrame({"ID": range(1, 151), "Lng": lngs, "Lat": lats, "GVI": np.random.randint(10, 50, size=150)})

    if "GVI" not in df.columns: df["GVI"] = 0
    df = df.dropna(subset=['Lng', 'Lat'])

    min_v, max_v = df["GVI"].min(), df["GVI"].max()
    if min_v == max_v: max_v = min_v + 1

    def get_gradient_color(val):
        n = (val - min_v) / (max_v - min_v)
        return [int(255 * (1 - n)), int(200 * math.sin(n * math.pi)), int(255 * n), 255]

    df["Dynamic_Color"] = df["GVI"].apply(get_gradient_color)
    return df


# ==========================================
# 💬 模块 5：NLP 社会情感计算引擎
# ==========================================
@st.cache_resource
def _load_sentiment_pipeline():
    from transformers import pipeline
    return pipeline(
        "sentiment-analysis",
        model="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
        top_k=1
    )


def classify_sentiment(texts):
    """使用 HuggingFace 多语言情感模型对文本列表进行批量分类，返回 (labels, scores)"""
    classifier = _load_sentiment_pipeline()
    labels, scores = [], []
    batch_size = 32
    truncated = [str(t)[:512] for t in texts]
    for i in range(0, len(truncated), batch_size):
        batch = truncated[i:i + batch_size]
        results = classifier(batch)
        for res in results:
            top = res[0]
            labels.append(top['label'])
            score = top['score'] if top['label'] == 'positive' else -top['score'] if top['label'] == 'negative' else 0.0
            scores.append(round(score, 3))
    return labels, scores


@st.cache_data
def get_nlp_data():
    file_path = "data/CV_NLP_RawData.csv"
    if not os.path.exists(file_path): file_path = "../" + file_path

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')

        if 'Text' not in df.columns:
            col_lower = {c.lower(): c for c in df.columns}
            if 'text' in col_lower:
                df = df.rename(columns={col_lower['text']: 'Text'})
            elif '评论' in df.columns:
                df = df.rename(columns={'评论': 'Text'})
            elif '内容' in df.columns:
                df = df.rename(columns={'内容': 'Text'})
            else:
                df['Text'] = df.iloc[:, 0].astype(str)

    except Exception:
        df = pd.DataFrame({"Text": ["环境很差", "历史遗迹不错", "老厂房太破了", "交通拥堵", "伪满建筑很有特色"],
                           "Score": [-0.8, 0.9, -0.6, -0.7, 0.8]})

    if 'Sentiment' not in df.columns or 'Score' not in df.columns:
        valid_texts = df['Text'].dropna().astype(str).tolist()
        labels, scores = classify_sentiment(valid_texts)
        df['Sentiment'] = labels[:len(df)]
        df['Score'] = scores[:len(df)]

    import jieba
    all_text = ' '.join(df['Text'].dropna().astype(str))
    stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '很', '什么', '我们'}
    words = [w for w in jieba.cut(all_text) if len(w) > 1 and w not in stop_words]
    word_counts = Counter(words).most_common(15)

    return df, word_counts


# ==========================================
# 🚥 模块 3：交通拥堵计算引擎
# ==========================================
@st.cache_data
def get_traffic_data():
    cong_bd_lngs = [125.360106, 125.355170, 125.346943]
    cong_bd_lats = [43.908314, 43.915339, 43.912892]
    cong_wgs = [bd09_to_wgs84(lon, lat) for lon, lat in zip(cong_bd_lngs, cong_bd_lats)]

    df_cong = pd.DataFrame({
        "Name": ["早市核心拥堵段", "铁道口车流瓶颈", "老旧小区出入口"],
        "Lng": [p[0] for p in cong_wgs], "Lat": [p[1] for p in cong_wgs],
        "Weight": [85, 90, 65]
    })
    return df_cong

# ==========================================
# 🎨 模块 2：AIGC 真实渲染引擎 (全参数 100% 互通版)
# ==========================================
def run_realtime_sd(pil_image, prompt, negative_prompt, steps=20, cfg_scale=7.0, denoising=0.55,
                    cn_module="none", cn_model="none", cn_weight=1.0,
                    sampler_name="DPM++ 2M Karras", seed=-1):
    if is_demo_mode():
        w, h = pil_image.size
        demo_img = Image.new('RGB', (min(w, 1024), min(h, 1024)), '#1e293b')
        draw = ImageDraw.Draw(demo_img)
        draw.text((demo_img.width // 6, demo_img.height // 2 - 20),
                  "AIGC Demo Placeholder", fill='#818cf8')
        draw.text((demo_img.width // 6, demo_img.height // 2 + 10),
                  "请替换 assets/demo_aigc_result.png", fill='#64748b')
        return demo_img

    buffered = BytesIO()
    img_copy = pil_image.copy()
    img_copy.thumbnail((1024, 1024))
    img_copy.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    controlnet_unit = {
        "input_image": img_base64,
        "module": cn_module,
        "model": cn_model,
        "weight": cn_weight,
        "resize_mode": "Just Resize",
        "lowvram": False,
        "processor_res": 512,
        "control_mode": "Balanced"
    }

    payload = {
        "init_images": [img_base64],
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "denoising_strength": denoising,
        "steps": steps,
        "sampler_name": sampler_name,
        "cfg_scale": cfg_scale,
        "seed": seed,
        "width": img_copy.width,
        "height": img_copy.height,
        "alwayson_scripts": {
            "ControlNet": {
                "args": [controlnet_unit]
            }
        }
    }

    config = load_global_config()
    url = config.get("engines", {}).get("aigc", {}).get("sd_webui_url", "http://127.0.0.1:7860/sdapi/v1/img2img")
    timeout_val = config.get("engines", {}).get("aigc", {}).get("timeout", 120)

    for attempt in range(2):
        try:
            response = requests.post(url, json=payload, timeout=timeout_val)
            if response.status_code == 200:
                r_data = response.json()
                return Image.open(BytesIO(base64.b64decode(r_data['images'][0])))
            else:
                return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt == 0:
                time.sleep(3)
        except Exception:
            return None
    return None

# ==========================================
# 🧠 模块 4：LLM 本地博弈引擎 (Gemma 4 驱动 - 6GB 显存版)
# ==========================================
def call_llm_engine(prompt, system_prompt="你是一位专业的城市规划专家。", model="gemma4:e2b-it-q4_K_M"):
    """
    呼叫本地 Ollama 引擎。针对 6GB 移动显存进行了模型减载优化。
    演示模式下返回预设角色回复。
    """
    if is_demo_mode():
        demo_responses = {
            "老王": "【思考过程】作为在铁北住了三十年的老居民，我首先想到的是这个方案会不会影响我们日常买菜、接孩子。其次我担心施工期间噪音和粉尘问题，毕竟这里老人孩子多。最后我关心拆迁补偿是否合理，不能让老百姓吃亏。\n\n【正式回复】我觉得改造是好事，但你们得先把老百姓的生活安排好。我家门口那棵老榆树可不能砍，那是我们几代人的记忆。还有，别光想着搞商业，我们需要的是菜市场、社区医院这些实实在在的东西。施工的时候能不能分期搞，别一下子把路全封了，我们出门都成问题。",
            "赵总": "【思考过程】从商业角度分析，这个地段紧邻伪满皇宫景区，日均客流量可观。我需要评估容积率能否支撑投资回报，首层商业租金预期，以及周边竞品项目的定价策略。关键是要找到文化IP与商业变现的平衡点。\n\n【正式回复】这个项目的核心价值在于文旅融合。我建议首层全部做沿街商业，引入文创品牌和特色餐饮，租金可以比周边高出30%。二层以上做精品民宿或联合办公，提升坪效。但前提是容积率不能低于2.0，否则投资回收期太长，资本不会进来。我们可以用历史建筑的外壳包装现代商业内核。",
            "李工": "【思考过程】根据《历史文化名城保护条例》和长春市总体规划，这个区域属于风貌协调区，建筑高度和风格都有严格管控。我需要平衡保护与发展的关系，确保中轴线视廊不被遮挡，同时满足居民改善生活条件的合理诉求。\n\n【正式回复】从规划专业角度，我建议采用'微介入、轻改造'策略。第一，严格控制新建建筑高度在12米以下，保护伪满皇宫的天际线视廊。第二，采用'修旧如旧'原则修缮历史建筑，保留红砖灰瓦的满洲风貌特征。第三，通过口袋公园和街角绿地的植入，提升公共空间品质。商业开发可以有，但必须服从上位规划的风貌管控要求。",
        }
        default_resp = "【思考过程】综合分析各方诉求，需要在历史保护、商业可行性和民生改善之间寻找平衡。\n\n【正式回复】建议采取渐进式更新策略，优先改善基础设施和公共空间，在保护历史风貌的前提下适度引入商业功能，确保居民利益不受损害。"
        for key, resp in demo_responses.items():
            if key in system_prompt:
                return resp
        return default_resp

    config = load_global_config()
    url = config.get("engines", {}).get("llm", {}).get("ollama_url", "http://127.0.0.1:11434/api/chat")
    model = config.get("engines", {}).get("llm", {}).get("default_model", model)
    timeout_val = config.get("engines", {}).get("llm", {}).get("timeout", 120)

    # ==========================================
    # 🔍 RAG：本地政策文档精准特征召回
    # ==========================================
    rag_db = load_rag_knowledge()
    if rag_db:
        # 基于 jieba 切词进行倒排查询碰撞
        words = [w for w in jieba.cut(prompt) if len(w) > 1]
        best_chunks = []
        for cid, p_info in rag_db.items():
            content = p_info['content']
            score = sum(1 for w in words if w in content)
            if score > 0:
                best_chunks.append((score, content, p_info['source']))
        
        if best_chunks:
            best_chunks.sort(key=lambda x: x[0], reverse=True)
            top_context = "\n\n".join([f"[{c[2]}]: {c[1]}" for c in best_chunks[:3]])
            system_prompt += f"\n\n【本地长春市法规与条例检索库片段，请严格以此时空限定背景作答】：\n{top_context}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    for attempt in range(2):
        try:
            response = requests.post(url, json=payload, timeout=timeout_val)
            if response.status_code == 200:
                return response.json().get('message', {}).get('content', "无法获取模型回复")
            else:
                return f"Ollama 报错: {response.status_code}"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt == 0:
                time.sleep(3)
        except Exception as e:
            return f"无法连接到 Ollama 服务，请确认已在终端运行: ollama run {model}"
    return f"无法连接到 Ollama 服务，请确认已在终端运行: ollama run {model}"


# ==========================================
# 🧠 模块 4b：LLM 流式引擎 (逐字打字机特效)
# ==========================================
def call_llm_engine_stream(prompt, system_prompt="你是一位专业的城市规划专家。", model="gemma4:e2b-it-q4_K_M"):
    """
    流式版本的 LLM 引擎调用。返回一个 Python generator，
    可直接被 st.write_stream() 消费，实现逐字输出的打字机效果。
    """
    if is_demo_mode():
        # 演示模式：模拟逐字输出
        demo_responses = {
            "老王": "【思考过程】作为在铁北住了三十年的老居民，我首先想到的是这个方案会不会影响我们日常买菜、接孩子。其次我担心施工期间噪音和粉尘问题，毕竟这里老人孩子多。最后我关心拆迁补偿是否合理，不能让老百姓吃亏。\n\n【正式回复】我觉得改造是好事，但你们得先把老百姓的生活安排好。我家门口那棵老榆树可不能砍，那是我们几代人的记忆。还有，别光想着搞商业，我们需要的是菜市场、社区医院这些实实在在的东西。施工的时候能不能分期搞，别一下子把路全封了，我们出门都成问题。",
            "赵总": "【思考过程】从商业角度分析，这个地段紧邻伪满皇宫景区，日均客流量可观。我需要评估容积率能否支撑投资回报，首层商业租金预期，以及周边竞品项目的定价策略。关键是要找到文化IP与商业变现的平衡点。\n\n【正式回复】这个项目的核心价值在于文旅融合。我建议首层全部做沿街商业，引入文创品牌和特色餐饮，租金可以比周边高出30%。二层以上做精品民宿或联合办公，提升坪效。但前提是容积率不能低于2.0，否则投资回收期太长，资本不会进来。我们可以用历史建筑的外壳包装现代商业内核。",
            "李工": "【思考过程】根据《历史文化名城保护条例》和长春市总体规划，这个区域属于风貌协调区，建筑高度和风格都有严格管控。我需要平衡保护与发展的关系，确保中轴线视廊不被遮挡，同时满足居民改善生活条件的合理诉求。\n\n【正式回复】从规划专业角度，我建议采用'微介入、轻改造'策略。第一，严格控制新建建筑高度在12米以下，保护伪满皇宫的天际线视廊。第二，采用'修旧如旧'原则修缮历史建筑，保留红砖灰瓦的满洲风貌特征。第三，通过口袋公园和街角绿地的植入，提升公共空间品质。商业开发可以有，但必须服从上位规划的风貌管控要求。",
        }
        default_resp = "【思考过程】综合分析各方诉求，需要在历史保护、商业可行性和民生改善之间寻找平衡。\n\n【正式回复】建议采取渐进式更新策略，优先改善基础设施和公共空间，在保护历史风貌的前提下适度引入商业功能，确保居民利益不受损害。"
        text = default_resp
        for key, resp in demo_responses.items():
            if key in system_prompt:
                text = resp
                break

        def _demo_gen():
            for char in text:
                yield char
                time.sleep(0.02)
        return _demo_gen()

    config = load_global_config()
    url = config.get("engines", {}).get("llm", {}).get("ollama_url", "http://127.0.0.1:11434/api/chat")
    model = config.get("engines", {}).get("llm", {}).get("default_model", model)
    timeout_val = config.get("engines", {}).get("llm", {}).get("timeout", 120)

    # RAG 文档召回（复用同一逻辑）
    rag_db = load_rag_knowledge()
    if rag_db:
        words = [w for w in jieba.cut(prompt) if len(w) > 1]
        best_chunks = []
        for cid, p_info in rag_db.items():
            content = p_info['content']
            score = sum(1 for w in words if w in content)
            if score > 0:
                best_chunks.append((score, content, p_info['source']))
        if best_chunks:
            best_chunks.sort(key=lambda x: x[0], reverse=True)
            top_context = "\n\n".join([f"[{c[2]}]: {c[1]}" for c in best_chunks[:3]])
            system_prompt += f"\n\n【本地长春市法规与条例检索库片段，请严格以此时空限定背景作答】：\n{top_context}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": True
    }

    def _stream_gen():
        try:
            response = requests.post(url, json=payload, timeout=timeout_val, stream=True)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        import json as _json
                        chunk = _json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
            else:
                yield f"Ollama 报错: {response.status_code}"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            yield f"无法连接到 Ollama 服务，请确认已在终端运行: ollama run {model}"
        except Exception as e:
            yield f"LLM 引擎异常: {str(e)}"

    return _stream_gen()
