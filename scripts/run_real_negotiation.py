"""scripts/run_real_negotiation.py

Run real multi-agent planning negotiation using live DeepSeek API calls.
Saves conversation logs, satisfaction scores, and strategy matrix to stage data bus.
"""

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Force real LLM API calls by setting the env variable
os.environ["FORCE_REAL_LLM"] = "1"

# Import system dependencies
import streamlit as st

# Mock Streamlit session state and functions if necessary, but stage_data_bus writes to file directly.
if not hasattr(st, "session_state"):
    st.session_state = {}

from src.engines.llm_engine import call_llm_engine, call_llm_engine_stream
from src.engines.site_diagnostic_engine import generate_policy_matrix
from src.engines.spatial_data_injector import (
    get_full_spatial_context,
    get_key_plots_summary,
    get_landuse_summary,
)
from src.workflow.stage_data_bus import load_stage_output, save_stage_output
from src.workflow.stage_keys import SK


def parse_streaming_text(raw_text: str):
    pattern = r"(【正式回复】|\[正式回复\]|\*\*正式回复\*\*|###?\s*正式回复|正式回复[:：]|【正式发言】|\[正式发言\]|\*\*正式发言\*\*|###?\s*正式发言|正式发言[:：]|【正式方案】|\[正式方案\]|\*\*正式方案\*\*|###?\s*正式方案|正式方案[:：])"
    match = re.search(pattern, raw_text)
    
    thinking_part = ""
    formal_part = ""
    
    if match:
        boundary_start = match.start()
        boundary_end = match.end()
        thinking_part = raw_text[:boundary_start].strip()
        formal_part = raw_text[boundary_end:].strip()
    else:
        thinking_part = raw_text.strip()
        formal_part = ""
        
    think_pattern = r"^(【思考过程】|\[思考过程\]|\*\*思考过程\*\*|###?\s*思考过程|思考过程[:：]\s*)"
    thinking_part = re.sub(think_pattern, "", thinking_part, flags=re.IGNORECASE).strip()
    thinking_part = re.sub(r'^[\s#\*：:]+', '', thinking_part).strip()
    
    formal_part = re.sub(r'^[\s#\*：:]+', '', formal_part).strip()
    
    return thinking_part, formal_part

def calculate_dynamic_satisfaction(memory_text: str):
    scores = {
        "👥 居民代表（老王）": 50.0,
        "💰 文旅运营商（赵总）": 50.0,
        "📐 规划师（李工）": 50.0
    }
    try:
        from src.utils.llm_json_parser import parse_llm_json
        
        prompt = f"""
        分析以下三个主体关于城市更新协商的对话文本，从语义上评估三方角色对当前方案的满意度得分（0-100分）。
        
        各方利益关注点：
        - 👥 居民代表：绿化、配套、生活便利、社区医疗、菜场养老等民生品质。
        - 💰 文旅运营商：投资回报、文旅商业品牌、容积率可行性、经济收益及活化运营。
        - 📐 规划师：历史文化名城保护、限高合规、视廊控制、指标红线合规。
        
        协商对话文本：
        {memory_text}
        
        请严格评估三方当前的态度是否在朝良性合作发展，计算出合理的分数。初始分为 50 分。每条满足或推进该角色利益的合理方案加分，损害利益的方案扣分。
        请仅返回 JSON 格式结果，不要包含任何 markdown 块或多余文字：
        {{
            \"👥 居民代表（老王）\": 分数(数字),
            \"💰 文旅运营商（赵总）\": 分数(数字),
            \"📐 规划师（李工）\": 分数(数字)
        }}
        """
        resp = call_llm_engine(prompt=prompt, system_prompt="你是一位客观的城市规划博弈审计员。", model="deepseek-v4-flash")
        parsed = parse_llm_json(resp, fallback=None)
        if parsed and isinstance(parsed, dict):
            valid = True
            for k in scores:
                if k not in parsed or not isinstance(parsed[k], (int, float)):
                    valid = False
            if valid:
                return {k: min(100.0, max(0.0, float(parsed[k]))) for k in scores}
    except Exception as e:
        print(f"Error calculating satisfaction with LLM: {e}")

    # Fallback keyword matching
    community_keywords = ["绿", "公园", "配套", "社区", "医院", "菜市", "养老", "口袋", "老年", "居民", "人行道", "活动", "活动中心", "休憩"]
    developer_keywords = ["容积率", "收益", "文旅", "商业", "民宿", "运营", "产业", "投资", "回报", "品牌", "特色餐饮", "盈利", "客流", "商铺"]
    planner_keywords = ["历史保护", "紫线", "限高", "合规", "风貌", "条例", "保护区", "天际线", "视廊", "数据", "红线", "导则", "退让", "绿地率"]
    
    for kw in community_keywords:
        if kw in memory_text:
            scores["👥 居民代表（老王）"] += 7.0
    for kw in developer_keywords:
        if kw in memory_text:
            scores["💰 文旅运营商（赵总）"] += 7.0
    for kw in planner_keywords:
        if kw in memory_text:
            scores["📐 规划师（李工）"] += 7.0
            
    for k in scores:
        scores[k] = min(100.0, max(0.0, scores[k]))
    return scores

def main():
    print("==================================================")
    print("🚀 开始进行真实的规划设计策略多智能体博弈协商...")
    print("==================================================")

    # 1. Load context
    spatial_ctx = get_full_spatial_context()
    s3 = load_stage_output("06", SK.DESIGN_CONCEPT, "")
    
    proposal = (
        s3[:300] if s3 else 
        "如何利用伪满皇宫文化IP与区位优势，通过政策引导、产业导入和空间更新的协同，"
        "盘活整个研究范围的经济活力，并使其辐射至全区乃至全城？"
    )
    print(f"\n[策划议题]: {proposal}\n")

    # 2. Define roles and prompt guidelines
    shared_context = (
        f"\n\n【研究范围空间数据约束】：\n{spatial_ctx[:2500]}"
        f"\n\n【上游设计目标】：\n{s3[:1500] if s3 else '暂无'}"
        f"\n\n【红线】：容积率≤1.4，核心区限高≤9m，一般区限高≤18m，遵守《长春市历史文化名城保护条例》。"
    )
    cot = ("\n\n请用【思考过程】展示推理，【正式回复】给出建设性方案，"
           "末行<SCORE:数值>打分(0-100)表示对方案的支持度。"
           "注意：三方立场是相辅相成的，共同推动良性循环。")

    roles = {
        "🏠 居民代表（老王）": {
            "system": (
                "你是老王，在伪满皇宫周边住了30年的社区代表。"
                "你支持改造，期盼更好的菜市场、社区医院和绿化。"
                "你关注政策如何让改造惠及原住民、改善老年人生活。"
                "你的立场是与开发商和规划师协同合作，共同推动社区更新。"
                + shared_context + cot
            ),
        },
        "💰 文旅运营商（赵总）": {
            "system": (
                "你是赵总，专注文旅商业运营的企业家。"
                "你看好伪满皇宫的文化IP和区位价值。"
                "你想导入文创品牌、特色餐饮和精品民宿。"
                "你理解容积率1.4的红线约束，但你认为通过文旅品牌溢价可以实现投资回报。"
                "你的核心观点是'政策引导+产业导入→经济盘活→反哺公共空间'的良性循环。"
                "你与居民和规划师相辅相成，共同构建可持续运营模式。"
                + shared_context + cot
            ),
        },
        "📐 规划师（李工）": {
            "system": (
                "你是李工，注册规划师，精通城市更新法规 and 空间分析。"
                "你基于空间数据进行科学研判，关注天际线视廊保护和历史风貌。"
                "你认为通过精准的政策工具（如历史风貌保护红利、文旅税收优惠）"
                "可以引导开发商和居民实现共赢。"
                "你的任务是将各方诉求整合为有法定依据、有空间落位的策略。"
                "你与居民和运营商相辅相成，确保方案既合规又可行。"
                + shared_context + cot
            ),
        }
    }

    # 3. Main loop
    NUM_ROUNDS = 3
    ROUND_LABELS = ["第一轮：方案陈述", "第二轮：利益交锋", "第三轮：妥协共识"]
    ROUND_INSTRUCTIONS = [
        "请基于策划议题提出你的初步方案与核心利益诉求。",
        "请阅读前一轮各方的方案，指出你认为的核心冲突焦点，并表达你的交锋意见。",
        "请基于前两轮的讨论，提出具体的折中妥协条件（例如用配建公共设施换取指标让步），给出你的最终支持度。",
    ]

    memory = ""
    detailed_log = []
    new_dialogues_list = []
    
    detailed_log.append(f"# 城市更新三方多轮博弈协商推演记录\n\n**策划议题**：{proposal}\n\n---\n")

    for round_idx in range(NUM_ROUNDS):
        print(f"\n--- 🔄 {ROUND_LABELS[round_idx]} ---")
        round_memory = ""
        detailed_log.append(f"## {ROUND_LABELS[round_idx]}\n")
        
        for name, cfg in roles.items():
            print(f"💬 {name} 正在思考发言中...")
            dp = f"【当前轮次】{ROUND_LABELS[round_idx]}\n{ROUND_INSTRUCTIONS[round_idx]}\n\n策划议题：\n{proposal}"
            if memory:
                dp += f"\n\n【前序各轮发言记录】：\n{memory[-3000:]}"
            if round_memory:
                dp += f"\n\n【本轮已有发言】：\n{round_memory}"
                
            # Call live LLM (FORCE_REAL_LLM is set)
            response = call_llm_engine(
                prompt=dp, system_prompt=cfg["system"], model="deepseek-v4-pro"
            )
            
            thinking, formal = parse_streaming_text(response)
            formal_clean = re.sub(r"<SCORE:\s*\d+\s*>", "", formal)
            
            print(f"💭 {name} 思考: {thinking[:100]}...")
            print(f"📢 {name} 发言: {formal_clean}\n")
            
            new_dialogues_list.append({
                "round_label": ROUND_LABELS[round_idx],
                "name": name,
                "thinking": thinking,
                "formal": formal_clean
            })

            detailed_log.append(f"### {name}\n")
            if thinking:
                detailed_log.append(f"**💭 思考过程**：\n> {thinking}\n\n")
            detailed_log.append(f"**💬 正式回复**：\n{formal_clean}\n\n")
            
            round_memory += f"[{name}]: {formal_clean}\n---\n"
            
        memory += f"\n=== {ROUND_LABELS[round_idx]} ===\n{round_memory}"

    # 4. Calculate satisfaction and strategy matrix
    print("📊 计算三方满意度得分并提取策略共识矩阵...")
    voting_scores = calculate_dynamic_satisfaction(memory)
    print(f"三方最终满意度: {voting_scores}")

    sp = (
        f"基于三方 **3轮博弈协商** 推演记录，生成Markdown表格【策略矩阵】：\n{memory[:4000]}\n\n"
        f"格式：| 策略方向 | 具体举措 | 政策依据 | 空间落位 | 资金逻辑 | 协同度 |\n\n"
        f"要求：\n"
        f"1. 每条策略必须有明确的空间落位（具体到哪个地块或哪条路段）\n"
        f"2. 必须体现'政策→产业→经济→空间'的良性循环逻辑\n"
        f"3. 重点体现第三轮妥协阶段达成的折中条件"
    )
    strategy_matrix = call_llm_engine(
        prompt=sp,
        system_prompt=(
            "资深城市更新策划师。策略须在容积率≤1.4、"
            "核心区限高≤9m约束下，构建政策-经济-空间良性循环。"
        ),
        model="deepseek-v4-pro"
    )
    print("\n[策略共识矩阵]:\n", strategy_matrix)

    # 5. Write to stage data bus
    full_log_content = "\n".join(detailed_log)
    save_stage_output("07", "negotiation_dialogues", new_dialogues_list)
    save_stage_output("07", SK.NEGOTIATION_RESULT, full_log_content)
    save_stage_output("07", SK.VOTING_SCORES, voting_scores)
    save_stage_output("07", SK.STRATEGY_MATRIX, strategy_matrix)

    print("\n✅ 博弈协商推演成功完成，并已将真实数据同步写入本地总线缓存中！")
    print("==================================================")

if __name__ == "__main__":
    main()
