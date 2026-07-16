"""持久化成果面板 — 跨页面常驻的生成成果下载入口

所有页面共享同一个 session_state，本模块提供：
1. register_output() — 注册任意阶段产出的可下载成果
2. get_persistent_outputs() — 获取所有已注册成果
3. render_persistent_output_bar() — 渲染顶部常驻成果栏（供所有页面调用）

Usage (在任意页面注册成果):
    from src.ui.persistent_outputs import register_output
    register_output(
        label="项目设计报告",
        data=docx_buf,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="项目设计报告.docx",
        category="document",
    )

Usage (所有页面渲染常驻栏):
    from src.ui.persistent_outputs import render_persistent_output_bar
    render_persistent_output_bar()  # 放在 render_top_nav() 之后
"""

from __future__ import annotations

import base64
import io
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass
class PersistentOutput:
    """单个持久化成果"""
    key: str                # 唯一标识符 (如 "thesis_docx", "diagnosis_report")
    label: str              # 显示名称 (如 "项目设计报告")
    category: str           # 分类: "thesis" | "report" | "image" | "data" | "drawing"
    mime: str               # MIME 类型
    filename: str           # 下载文件名
    timestamp: float = field(default_factory=time.time)
    size_bytes: int = 0     # 数据大小（字节）
    metadata: dict[str, str] = field(default_factory=dict)  # 额外信息
    _data_ref: str = ""     # session_state 中的数据引用键名


# ═══════════════════════════════════════════════════════════════
# Session State Key
# ═══════════════════════════════════════════════════════════════

OUTPUT_REGISTRY_KEY = "_persistent_outputs_registry"
OUTPUT_DATA_PREFIX = "_persistent_output_data_"
CACHE_DIR = Path("output/persistent_outputs")


def _save_registry_to_disk():
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        registry = st.session_state.get(OUTPUT_REGISTRY_KEY, {})
        meta_dict = {}
        for k, out in registry.items():
            meta_dict[k] = {
                "key": out.key,
                "label": out.label,
                "category": out.category,
                "mime": out.mime,
                "filename": out.filename,
                "timestamp": out.timestamp,
                "size_bytes": out.size_bytes,
                "metadata": out.metadata,
                "_data_ref": out._data_ref,
            }
        registry_file = CACHE_DIR / "registry.json"
        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        import logging
        logging.error(f"Error saving persistent outputs registry to disk: {e}")


def _load_registry_from_disk():
    try:
        registry_file = CACHE_DIR / "registry.json"
        if not registry_file.exists():
            return
        with open(registry_file, "r", encoding="utf-8") as f:
            meta_dict = json.load(f)
        
        registry = st.session_state[OUTPUT_REGISTRY_KEY]
        for k, val in meta_dict.items():
            bin_file = CACHE_DIR / f"{k}.bin"
            if bin_file.exists():
                with open(bin_file, "rb") as bf:
                    data_bytes = bf.read()
                data_key = val["_data_ref"]
                st.session_state[data_key] = data_bytes
                
                out = PersistentOutput(
                    key=val["key"],
                    label=val["label"],
                    category=val["category"],
                    mime=val["mime"],
                    filename=val["filename"],
                    timestamp=val["timestamp"],
                    size_bytes=val["size_bytes"],
                    metadata=val["metadata"],
                    _data_ref=val["_data_ref"],
                )
                registry[k] = out
    except Exception as e:
        import logging
        logging.error(f"Error loading persistent outputs registry from disk: {e}")


def _init_registry():
    """初始化注册表"""
    if OUTPUT_REGISTRY_KEY not in st.session_state:
        st.session_state[OUTPUT_REGISTRY_KEY] = {}
        _load_registry_from_disk()


def _get_registry() -> dict[str, PersistentOutput]:
    """获取注册表"""
    _init_registry()
    return st.session_state[OUTPUT_REGISTRY_KEY]


# ═══════════════════════════════════════════════════════════════
# 注册 / 注销
# ═══════════════════════════════════════════════════════════════

def register_output(
    label: str,
    data: Any,
    mime: str = "application/octet-stream",
    filename: str = "output",
    category: str = "report",
    key: str | None = None,
    metadata: dict[str, str] | None = None,
    overwrite: bool = True,
) -> str:
    """注册一个持久化成果。"""
    registry = _get_registry()

    if key is None:
        import re
        safe_label = re.sub(r'[^\w]', '_', label.lower())[:30]
        key = f"{category}_{safe_label}"

    if key in registry and not overwrite:
        return key

    # 将数据存入 session_state
    data_key = f"{OUTPUT_DATA_PREFIX}{key}"
    if isinstance(data, io.BytesIO):
        data_bytes = data.getvalue()
    elif isinstance(data, bytes):
        data_bytes = data
    elif isinstance(data, str):
        data_bytes = data.encode("utf-8")
    else:
        try:
            data_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        except (TypeError, ValueError):
            data_bytes = str(data).encode("utf-8")

    st.session_state[data_key] = data_bytes

    # 同步写入磁盘
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        bin_file = CACHE_DIR / f"{key}.bin"
        with open(bin_file, "wb") as bf:
            bf.write(data_bytes)
    except Exception as e:
        import logging
        logging.error(f"Error writing persistent output data to disk: {e}")

    output = PersistentOutput(
        key=key,
        label=label,
        category=category,
        mime=mime,
        filename=filename,
        size_bytes=len(data_bytes),
        metadata=metadata or {},
        _data_ref=data_key,
    )

    registry[key] = output
    _save_registry_to_disk()
    return key


def get_output(key: str) -> PersistentOutput | None:
    """获取单个已注册成果的元数据"""
    registry = _get_registry()
    return registry.get(key)


def get_output_data(key: str) -> bytes | None:
    """获取已注册成果的实际数据"""
    output = get_output(key)
    if output is None:
        return None
    return st.session_state.get(output._data_ref)


def get_all_outputs(category: str | None = None) -> list[PersistentOutput]:
    """获取所有已注册成果，按时间倒序"""
    registry = _get_registry()
    outputs = list(registry.values())
    if category:
        outputs = [o for o in outputs if o.category == category]
    outputs.sort(key=lambda o: o.timestamp, reverse=True)
    return outputs


def unregister_output(key: str):
    """注销一个成果"""
    registry = _get_registry()
    if key in registry:
        output = registry[key]
        data_key = output._data_ref
        if data_key in st.session_state:
            del st.session_state[data_key]
        del registry[key]

        # 同步删除磁盘文件
        try:
            bin_file = CACHE_DIR / f"{key}.bin"
            if bin_file.exists():
                bin_file.unlink()
        except Exception:
            pass
        _save_registry_to_disk()


def clear_all_outputs(category: str | None = None):
    """清空所有（或指定分类的）已注册成果"""
    registry = _get_registry()
    keys = [k for k, v in registry.items() if v.category == category] if category else list(registry.keys())
    for k in keys:
        unregister_output(k)


def has_outputs(category: str | None = None) -> bool:
    """检查是否有已注册成果"""
    registry = _get_registry()
    if category:
        return any(v.category == category for v in registry.values())
    return len(registry) > 0


# ═══════════════════════════════════════════════════════════════
# UI 渲染
# ═══════════════════════════════════════════════════════════════

# 分类图标和颜色
CATEGORY_META = {
    "document":  {"icon": "📝", "color": "#f59e0b", "label": "设计报告"},
    "report":    {"icon": "📊", "color": "#38bdf8", "label": "分析报告"},
    "drawing":   {"icon": "🗺️", "color": "#a855f7", "label": "规划图纸"},
    "image":     {"icon": "🖼️", "color": "#10b981", "label": "生成图像"},
    "data":      {"icon": "📦", "color": "#f97316", "label": "数据导出"},
}


def _format_size(n_bytes: int) -> str:
    """格式化字节数"""
    if n_bytes < 1024:
        return f"{n_bytes} B"
    elif n_bytes < 1024 * 1024:
        return f"{n_bytes / 1024:.1f} KB"
    else:
        return f"{n_bytes / (1024 * 1024):.1f} MB"


def render_persistent_output_bar():
    """在页面顶部渲染常驻成果下载栏。

    调用位置：每个页面的 render_top_nav() 之后。
    当没有任何已注册成果时，不渲染任何内容。
    """
    if not has_outputs():
        return

    outputs = get_all_outputs()
    if not outputs:
        return

    st.markdown("---")

    # ── 标题行 ──
    col_title, col_clear = st.columns([6, 1])
    with col_title:
        st.markdown("#### 📦 已生成的成果（切换页面不丢失）")
    with col_clear:
        if st.button("🗑️ 清空全部", key="clear_all_outputs", help="清空所有已生成的成果缓存"):
            clear_all_outputs()
            st.rerun()

    # ── 成果卡片网格 ──
    cols = st.columns(min(len(outputs), 3))
    for i, output in enumerate(outputs):
        meta = CATEGORY_META.get(output.category, {"icon": "📄", "color": "#64748b", "label": "其他"})
        data = get_output_data(output.key)

        with cols[i % 3], st.container(border=True):
            # 标题行
            st.markdown(
                f"<span style='color:{meta['color']};font-weight:700;'>{meta['icon']} {output.label}</span>"
                f"<span style='float:right;color:#94a3b8;font-size:0.75rem;'>{meta['label']}</span>",
                unsafe_allow_html=True,
            )

            # 元信息
            st.caption(
                f"📄 {output.filename[:40]}"
                f"{'…' if len(output.filename) > 40 else ''}"
                f" · {_format_size(output.size_bytes)}"
            )

            if data is not None:
                st.download_button(
                    f"💾 下载 {output.label}",
                    data=data,
                    file_name=output.filename,
                    mime=output.mime,
                    key=f"persistent_dl_{output.key}",
                    use_container_width=True,
                )
            else:
                st.warning("⚠️ 数据丢失，请重新生成")

    st.markdown("---")


# ═══════════════════════════════════════════════════════════════
# 便捷注册函数（供各阶段页面直接调用）
# ═══════════════════════════════════════════════════════════════

def register_document_output(
    docx_buf,
    student_name: str = "",
    student_id: str = "",
    chapters: dict[str, str] | None = None,
):
    """注册项目设计报告成果"""
    safe_name = student_name or "学生"
    safe_id = student_id or "000000"
    fname = f"项目设计报告_{safe_name}_{safe_id}.docx"

    # 注册 docx
    register_output(
        label="项目设计报告 (.docx)",
        data=docx_buf,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=fname,
        category="document",
        key="report_docx",
    )

    # 如果有章节数据，注册纯文本备份
    if chapters:
        full_text = "\n\n".join(
            f"## {sid} {chapters[sid]}" for sid in sorted(chapters.keys())
        )
        register_output(
            label="设计报告纯文本 (.txt)",
            data=full_text,
            mime="text/plain; charset=utf-8",
            filename=f"项目设计报告_{safe_name}_{safe_id}.txt",
            category="document",
            key="report_txt",
        )


def register_report_output(
    label: str,
    content: str,
    stage_code: str = "",
    key: str | None = None,
):
    """注册一份分析报告"""
    safe_stage = stage_code or "report"
    report_key = key or f"report_{safe_stage}_{label[:10]}"
    safe_filename = f"{label}.md"

    register_output(
        label=label,
        data=content,
        mime="text/markdown; charset=utf-8",
        filename=safe_filename,
        category="report",
        key=report_key,
        metadata={"stage": stage_code},
    )

    if stage_code:
        try:
            from src.workflow.artifact_registry import register_artifact

            register_artifact(
                stage_code=stage_code,
                key=report_key,
                label=label,
                category="report",
                location=safe_filename,
                mime="text/markdown; charset=utf-8",
                metadata={"persistent_output_key": report_key},
            )
        except Exception as e:
            import logging

            logging.error(f"Error registering report artifact: {e}")
