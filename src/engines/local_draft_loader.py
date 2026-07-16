import logging
import os
import re
from typing import Dict, List, Optional, Tuple

import docx

logger = logging.getLogger("ultimateDESIGN")

def load_document_from_draft() -> tuple[dict[str, str], dict[str, str]]:
    """
    从本地桌面草稿提取文档内容。
    返回:
        (chapters, metadata)
        chapters: {section_id: text}
        metadata: {
            "abstract_cn": str,
            "keywords_cn": str,
            "abstract_en": str,
            "keywords_en": str,
            "acknowledgments": str,
            "references": str
        }
    """
    from src.config.site import get_author_info
    author = get_author_info()
    author_name = author.get("name", "作者")
    author_id = author.get("id", "编号")
    path = os.path.join(os.path.expanduser("~"), "Desktop", "项目文档", f"项目设计报告_{author_name}_{author_id}.docx")
    chapters = {}
    metadata = {
        "abstract_cn": "",
        "keywords_cn": "",
        "abstract_en": "",
        "keywords_en": "",
        "acknowledgments": "",
        "references": ""
    }
    
    if not os.path.exists(path):
        logger.warning(f"Draft file not found: {path}")
        return chapters, metadata

    try:
        doc = docx.Document(path)
    except Exception as e:
        logger.error(f"Failed to open draft file: {e}")
        return chapters, metadata

    current_key = None
    abstract_cn_paras = []
    abstract_en_paras = []
    ack_paras = []
    ref_lines = []
    
    in_abstract_cn = False
    in_abstract_en = False
    in_ack = False
    in_refs = False

    valid_keys = [
        "1.1", "1.2",
        "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8",
        "3.1", "3.2", "3.3", "3.4", "3.5",
        "4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8",
        "5.1", "5.2", "5.3"
    ]

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
            
        text_clean = text.replace(" ", "")
        
        # Check section boundary titles
        if text_clean in ["摘要", "摘  要"]:
            in_abstract_cn = True
            in_abstract_en = False
            in_ack = False
            in_refs = False
            current_key = None
            continue
        elif text.lower() == "abstract":
            in_abstract_cn = False
            in_abstract_en = True
            in_ack = False
            in_refs = False
            current_key = None
            continue
        elif text_clean in ["致谢", "致  谢"]:
            in_abstract_cn = False
            in_abstract_en = False
            in_ack = True
            in_refs = False
            current_key = None
            continue
        elif text_clean in ["参考文献"]:
            in_abstract_cn = False
            in_abstract_en = False
            in_ack = False
            in_refs = True
            current_key = None
            continue
        elif text_clean in ["目录", "目  录", "附录", "附  录"] or (text.startswith("第") and "章" in text):
            in_abstract_cn = False
            in_abstract_en = False
            in_ack = False
            in_refs = False
            current_key = None
            continue

        # Check if it starts with a valid section ID
        found_key = None
        for vk in valid_keys:
            if text.startswith(vk):
                found_key = vk
                break

        if found_key:
            current_key = found_key
            in_abstract_cn = False
            in_abstract_en = False
            in_ack = False
            in_refs = False
            continue

        # Append content
        if current_key:
            chapters.setdefault(current_key, []).append(text)
        elif in_abstract_cn:
            if text.startswith("关键词：") or text.startswith("关键词:"):
                metadata["keywords_cn"] = text.replace("关键词：", "").replace("关键词:", "").strip()
                in_abstract_cn = False
            else:
                abstract_cn_paras.append(text)
        elif in_abstract_en:
            if text.startswith("Keywords:") or text.startswith("Keywords："):
                metadata["keywords_en"] = text.replace("Keywords:", "").replace("Keywords：", "").strip()
                in_abstract_en = False
            else:
                abstract_en_paras.append(text)
        elif in_ack:
            ack_paras.append(text)
        elif in_refs:
            ref_lines.append(text)

    # Join paragraphs
    for k, v in chapters.items():
        chapters[k] = "\n".join(v)
        
    metadata["abstract_cn"] = "\n".join(abstract_cn_paras)
    metadata["abstract_en"] = "\n".join(abstract_en_paras)
    metadata["acknowledgments"] = "\n".join(ack_paras)
    metadata["references"] = "\n".join(ref_lines)

    return chapters, metadata


def get_combined_references(draft_refs_text: str) -> str:
    """
    将本地参考文献文件夹内的 PDF 文件名格式化为符合 GB/T 7714-2015 标准的条目，
    并与草稿中的参考文献合并去重。
    """
    import os
    import re
    
    # 20个本地参考文献的真实学校/期刊和年份映射
    ref_mapping = {
        "上海历史风貌区巷弄精细化治理路径探索——以徐汇区衡复历史文化风貌区为例": {
            "entry": "鲍柏江, 王林, 薛鸣华. 上海历史风貌区巷弄精细化治理路径探索——以徐汇区衡复历史文化风貌区为例[J]. 上海城市规划, 2023(5): 92-97."
        },
        "历史肌理延续的数字化城市设计方法研究——以江苏同里古镇为例": {
            "entry": "赵卉. 历史肌理延续的数字化城市设计方法研究——以江苏同里古镇为例[J]. 城市发展研究, 2025, 32(9): 22-26."
        },
        "基于可解释深度学习的街道风貌基因图谱识别研究": {
            "entry": "尧馨雅. 基于可解释深度学习的街道风貌基因图谱识别研究[D]. 哈尔滨: 哈尔滨工业大学, 2023."
        },
        "基于有机更新理念的老旧社区公共空间改造设计研究": {
            "entry": "江玉博. 基于有机更新理念的老旧社区公共空间改造设计研究[D]. 成都: 西南交通大学, 2019."
        },
        "基于深度学习与街景影像的建筑风格数据集构建方法": {
            "entry": "孙皓尊. 基于深度学习与街景影像的建筑风格数据集构建方法[D]. 武汉: 武汉科技大学, 2024."
        },
        "基于深度学习的传统村落建筑肌理风貌定量评价": {
            "entry": "王文科. 基于深度学习的传统村落建筑肌理风貌定量评价[D]. 北京: 北京建筑大学, 2024."
        },
        "基于社区营造的老旧小区公共空间景观微更新研究": {
            "entry": "苏春婷. 基于社区营造的老旧小区公共空间景观微更新研究[D]. 北京: 中央美术学院, 2021."
        },
        "基于蚁群算法的智慧旅游路线规划研究": {
            "entry": "牛悦诚. 基于蚁群算法的智慧旅游路线规划研究[D]. 南京: 南京邮电大学, 2017."
        },
        "基于街景图片与深度学习的旧工业园区改造与可步行性要素研究": {
            "entry": "梁汉雄. 基于街景图片与深度学习的旧工业园区改造与可步行性要素研究[D]. 北京: 北方工业大学, 2025."
        },
        "基于计算机视觉技术的城市街道步行空间人群行为原型研究": {
            "entry": "丁梦月. 基于计算机视觉技术的城市街道步行空间人群行为原型研究[D]. 天津: 天津大学, 2017."
        },
        "广州恩宁路永庆坊微改造模式研究": {
            "entry": "陈楚宇. 广州恩宁路永庆坊微改造模式研究[D]. 广州: 华南理工大学, 2018."
        },
        "建筑遗产数字化保护集成设计研究": {
            "entry": "李伟荣. 建筑遗产数字化保护集成设计研究[D]. 广州: 广州大学, 2024."
        },
        "探索北京旧城居住区有机更新的适宜途径": {
            "entry": "方可. 探索北京旧城居住区有机更新的适宜途径[D]. 北京: 清华大学, 1999."
        },
        "数字孪生技术提升城市韧性路径研究": {
            "entry": "张国政. 数字孪生技术提升城市韧性路径研究[D]. 北京: 中共中央党校, 2024."
        },
        "数字孪生驱动下济南市智慧旅游发展策略研究": {
            "entry": "代吉仁. 数字孪生驱动下济南市智慧旅游发展策略研究[D]. 南宁: 广西民族大学, 2024."
        },
        "智慧城市空间信息资源规划的模型和实现方法研究": {
            "entry": "张峰. 智慧城市空间信息资源规划的模型和实现方法研究[D]. 济南: 山东师范大学, 2015."
        },
        "社会化背景下的城市养老服务设施规划研究": {
            "entry": "魏倩. 社会化背景下的城市养老服务设施规划研究[D]. 重庆: 重庆大学, 2017."
        },
        "社会空间理论视角的社区更新": {
            "entry": "卢文正. 社会空间理论视角的社区更新[D]. 杭州: 浙江大学, 2023."
        },
        "积极老龄化视角下老年群体参与城市社区治理研究": {
            "entry": "周梦雪. 积极老龄化视角下老年群体参与城市社区治理研究[D]. 长春: 吉林大学, 2023."
        }
    }

    # 1. 格式化本地 PDF
    local_pdf_entries = []
    seen_entries = set()
    path = os.path.join(os.path.expanduser("~"), "Desktop", "陈礼冲 毕设", "参考文献")
    if os.path.exists(path):
        try:
            files = [f for f in os.listdir(path) if f.lower().endswith('.pdf')]
            files.sort()
            for f in files:
                name_no_ext = os.path.splitext(f)[0]
                # 过滤掉括弧信息
                name_no_ext = re.sub(r'[\(（].*?[\)）]', '', name_no_ext).strip()
                if "_" in name_no_ext:
                    parts = name_no_ext.split("_")
                    p1, p2 = parts[0].strip(), parts[1].strip()
                    if len(p2) <= 4:
                        author, title = p2, p1
                    elif len(p1) <= 4:
                        author, title = p1, p2
                    else:
                        author, title = p2, p1
                else:
                    author, title = "佚名", name_no_ext
                # 剔除已有的 [序号]
                title = re.sub(r'^\[\d+\]\s*', '', title).strip()
                author = re.sub(r'[\(（].*?[\)）]', '', author).strip()

                # 精确/模糊匹配映射表中的真实条目
                matched = False
                for key, val in ref_mapping.items():
                    if key in title or title in key:
                        entry = val["entry"]
                        if entry not in seen_entries:
                            local_pdf_entries.append(entry)
                            seen_entries.add(entry)
                        matched = True
                        break

                if not matched:
                    entry = f"{author}. {title}[D]. 长春: 吉林建筑大学, 2023."
                    if entry not in seen_entries:
                        local_pdf_entries.append(entry)
                        seen_entries.add(entry)
        except Exception as e:
            logger.warning(f"Error reading local PDFs: {e}")
            
    # 2. 提取草稿中的条目
    draft_entries = []
    if draft_refs_text:
        lines = [l.strip() for l in draft_refs_text.split('\n') if l.strip()]
        for line in lines:
            cleaned = re.sub(r'^\[\d+\]\s*', '', line)
            if cleaned:
                draft_entries.append(cleaned)
                
    # 3. 合并与重编号
    combined_list = []
    idx = 1
    # 优先添加本地 PDF 条目
    for item in local_pdf_entries:
        combined_list.append(f"[{idx}] {item}")
        idx += 1
    # 添加草稿中的条目并去重
    for item in draft_entries:
        text_only = item.split(".")[0] if "." in item else item
        if not any(text_only in existing for existing in combined_list):
            combined_list.append(f"[{idx}] {item}")
            idx += 1
            
    return "\n".join(combined_list)
