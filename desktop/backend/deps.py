"""Shared FastAPI dependencies and SSE streaming helpers for Desktop Sidecar."""

from __future__ import annotations

from collections.abc import AsyncIterable, Iterable
import inspect
import json
import os
from typing import Any

from fastapi import Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from src.core.runtime_adapter import get_active_project_id


def verify_session_token(
    request: Request,
    x_ud_token: str | None = Header(default=None, alias="X-UD-Token"),
    token: str | None = Query(default=None),
) -> bool:
    """Verify desktop session token when UD_SESSION_TOKEN is configured in env.

    When UD_SESSION_TOKEN is unset or empty (local dev / pytest TestClient default),
    all loopback requests are permitted.
    """
    expected = os.environ.get("UD_SESSION_TOKEN", "").strip()
    if not expected:
        return True

    # Check X-UD-Token header or ?token= query parameter
    if x_ud_token == expected or token == expected:
        return True

    # Also support standard Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        bearer_token = auth_header[7:].strip()
        if bearer_token == expected:
            return True

    # Also check lowercase header fallback
    raw_header = request.headers.get("x-ud-token", "").strip()
    if raw_header == expected:
        return True

    raise HTTPException(status_code=401, detail="未授权的桌面会话请求")


def get_current_project_id() -> str:
    """Return the active project workspace ID."""
    return get_active_project_id()


def format_sse_data(item: Any) -> str:
    """Format an arbitrary payload into a valid SSE `data: <json>\\n\\n` frame."""
    if isinstance(item, bytes):
        item = item.decode("utf-8", errors="replace")

    if isinstance(item, str):
        stripped = item.strip()
        if stripped.startswith("data:") or stripped.startswith("event:") or stripped.startswith(":"):
            return stripped + "\n\n"
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            try:
                json.loads(stripped)
                return f"data: {stripped}\n\n"
            except Exception:
                pass
        payload = json.dumps({"type": "token", "content": item, "token": item}, ensure_ascii=False)
        return f"data: {payload}\n\n"

    try:
        payload = json.dumps(item, ensure_ascii=False, default=str)
    except Exception:
        payload = json.dumps({"type": "token", "content": str(item)}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def sse_response(generator: AsyncIterable[Any] | Iterable[Any]) -> StreamingResponse:
    """Wrap a sync or async generator into an SSE StreamingResponse."""

    async def _async_wrapper():
        try:
            if inspect.isasyncgen(generator) or hasattr(generator, "__aiter__"):
                async for item in generator:  # type: ignore[union-attr]
                    if item is not None:
                        yield format_sse_data(item)
            else:
                for item in generator:  # type: ignore[union-attr]
                    if item is not None:
                        yield format_sse_data(item)
        except Exception as exc:
            err_payload = json.dumps(
                {"type": "error", "error": str(exc), "message": f"流式输出中断: {exc}"},
                ensure_ascii=False,
            )
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(
        _async_wrapper(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
