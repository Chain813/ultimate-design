"""Quality assessor: dual evaluation with Ollama Gemma vision + DeepSeek content."""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from io import BytesIO
from typing import List

import requests

try:
    import torch
except ImportError:
    torch = None

logger = logging.getLogger("ultimateDESIGN")


@dataclass
class VisualScore:
    """Result from visual assessment."""
    score: float
    description: str
    issues: List[str] = field(default_factory=list)


@dataclass
class ContentScore:
    """Result from content assessment."""
    score: float
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """Combined quality assessment report."""
    rating: str
    visual_score: float
    content_score: float
    combined_score: float
    issue_types: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    raw_visual: str = ""
    raw_content: str = ""


class QualityAssessor:
    """Dual quality assessment: Ollama Gemma vision + DeepSeek content."""

    def __init__(self, ollama_url: str = "", vision_model: str = "",
                 text_model: str = ""):
        self.ollama_url = ollama_url or "http://127.0.0.1:11434"
        self.text_model = text_model or "deepseek-v4-pro"
        self.vision_model = vision_model or self._auto_select_vision_model()

    def assess(self, image, prompt: str, drawing_name: str) -> QualityReport:
        """Run dual assessment and return combined report."""
        visual = self._visual_assessment(image, drawing_name)
        content = self._content_assessment(visual.description, prompt, drawing_name)
        return self._combine_scores(visual, content)

    def _visual_assessment(self, image, drawing_name: str) -> VisualScore:
        """Assess visual quality via Ollama Gemma vision."""
        img_b64 = self._encode_image(image)
        prompt = (
            f'请评估这张城市规划图纸"{drawing_name}"的视觉质量。\n\n'
            f"评分标准（0-10分）：\n"
            f"- 图面整洁度（无乱码、无杂乱元素）\n"
            f"- 信息层级清晰度（主图、图例、标注分明）\n"
            f"- 色彩协调性（配色专业统一）\n"
            f"- 文字可读性（标题清晰、无乱码）\n\n"
            f"请严格输出JSON格式：\n"
            f'{{"score": 0-10, "description": "图面描述50字以内", "issues": ["问题1", "问题2"]}}'
        )
        try:
            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.vision_model,
                    "prompt": prompt,
                    "images": [img_b64],
                    "stream": False,
                },
                timeout=120,
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                return self._parse_visual_response(text)
        except Exception as e:
            logger.warning("Visual assessment failed: %s", e)
        return VisualScore(score=5.0, description="视觉评估不可用", issues=["评估服务不可用"])

    def _content_assessment(self, image_desc: str, prompt: str,
                            drawing_name: str) -> ContentScore:
        """Assess content accuracy via DeepSeek."""
        review_prompt = (
            f'请评估以下城市规划图纸"{drawing_name}"的内容准确性。\n\n'
            f"原始提示词要求：\n{prompt[:500]}\n\n"
            f"图像描述：\n{image_desc}\n\n"
            f"评分标准（0-10分）：\n"
            f"- 是否符合提示词要求\n"
            f"- 空间关系是否合理\n"
            f"- 数据/图例是否准确\n"
            f"- 是否有虚构内容\n\n"
            f'请严格输出JSON：{{"score": 0-10, "issues": ["问题1"], "suggestions": ["建议1"]}}'
        )
        try:
            from src.engines.llm_engine import call_llm_engine
            text = call_llm_engine(prompt=review_prompt, model=self.text_model)
            return self._parse_content_response(text)
        except Exception as e:
            logger.warning("Content assessment failed: %s", e)
        return ContentScore(score=5.0, issues=["内容评估不可用"], suggestions=[])

    def _combine_scores(self, visual: VisualScore,
                        content: ContentScore) -> QualityReport:
        """Combine visual and content scores into final report."""
        combined = (visual.score * 0.4 + content.score * 0.6)
        rating = self._score_to_rating(combined)
        all_issues = list(set(visual.issues + content.issues))
        all_suggestions = list(set(content.suggestions))
        return QualityReport(
            rating=rating,
            visual_score=round(visual.score, 1),
            content_score=round(content.score, 1),
            combined_score=round(combined, 1),
            issue_types=all_issues,
            suggestions=all_suggestions,
            raw_visual=visual.description,
            raw_content=str(content.issues),
        )

    def _score_to_rating(self, score: float) -> str:
        if score >= 8:
            return "A"
        elif score >= 6:
            return "B"
        elif score >= 4:
            return "C"
        else:
            return "D"

    def _parse_visual_response(self, text: str) -> VisualScore:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                return VisualScore(
                    score=float(data.get("score", 5)),
                    description=str(data.get("description", "")),
                    issues=list(data.get("issues", [])),
                )
        except (json.JSONDecodeError, ValueError):
            pass
        return VisualScore(score=5.0, description=text[:100], issues=["解析失败"])

    def _parse_content_response(self, text: str) -> ContentScore:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                return ContentScore(
                    score=float(data.get("score", 5)),
                    issues=list(data.get("issues", [])),
                    suggestions=list(data.get("suggestions", [])),
                )
        except (json.JSONDecodeError, ValueError):
            pass
        return ContentScore(score=5.0, issues=["解析失败"], suggestions=[])

    def _encode_image(self, image) -> str:
        img_copy = image.copy()
        img_copy.thumbnail((1024, 1024))
        buffered = BytesIO()
        img_copy.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _auto_select_vision_model(self) -> str:
        vram_gb = self._detect_vram()
        if vram_gb >= 16:
            model = "gemma3:12b"
        elif vram_gb >= 8:
            model = "gemma3:4b"
        else:
            model = "gemma3:2b"
        self._ensure_model_available(model)
        return model

    def _detect_vram(self) -> int:
        try:
            if torch and torch.cuda.is_available():
                vram = torch.cuda.get_device_properties(0).total_mem // (1024**3)
                if isinstance(vram, int):
                    return vram
        except Exception:
            pass
        return 4

    def _ensure_model_available(self, model: str):
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            installed = [m["name"] for m in resp.json().get("models", [])]
            if model not in installed:
                logger.info("Downloading %s via Ollama...", model)
                requests.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": model},
                    timeout=600,
                )
        except Exception as e:
            logger.warning("Could not verify/download model %s: %s", model, e)
