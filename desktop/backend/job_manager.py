"""Thread-safe background job manager with SSE progress/log streaming."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
import inspect
import logging
import threading
import time
from typing import Any
import uuid

logger = logging.getLogger("ultimateDESIGN.job_manager")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobCancelledError(RuntimeError):
    """Raised when a background job observes a cancellation request."""


class JobContext:
    """Execution context injected into background worker callables."""

    def __init__(self, manager: JobManager, job_id: str) -> None:
        self._manager = manager
        self.job_id = job_id

    def update(
        self,
        progress: int | float | None = None,
        message: str | None = None,
        log: str | None = None,
        output_path: str | None = None,
    ) -> None:
        """Update job progress (0-100), status message, log entry, or output file path."""
        self._manager._update_job_from_ctx(
            self.job_id,
            progress=progress,
            message=message,
            log=log,
            output_path=output_path,
        )

    def log(self, message: str) -> None:
        """Append a log line to the job."""
        self.update(log=message)

    def is_cancelled(self) -> bool:
        """Return True if cancellation has been requested for this job."""
        return self._manager.is_cancelled(self.job_id)

    def check_cancelled(self) -> None:
        """Raise JobCancelledError if the job was cancelled."""
        if self.is_cancelled():
            raise JobCancelledError(f"任务 {self.job_id} 已被用户取消")


class JobManager:
    """Thread-safe background job queue using a bounded ThreadPoolExecutor."""

    def __init__(self, max_workers: int = 4) -> None:
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ud_job")
        self._jobs: dict[str, dict[str, Any]] = {}
        self._futures: dict[str, Future[Any]] = {}
        self._cancel_flags: dict[str, threading.Event] = {}
        self._version_counter: dict[str, int] = {}

    def submit_job(
        self,
        name: str,
        category: str,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Submit a background job and return its initial job state dictionary."""
        job_id = uuid.uuid4().hex[:12]
        now_iso = _utc_now_iso()
        job_record: dict[str, Any] = {
            "job_id": job_id,
            "name": str(name or "后台作业"),
            "category": str(category or "general"),
            "status": "queued",
            "progress": 0,
            "message": "任务已进入队列，等待执行...",
            "logs": [f"[{now_iso}] 任务已创建: {name}"],
            "result": None,
            "error": None,
            "output_path": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        cancel_event = threading.Event()

        with self._lock:
            self._jobs[job_id] = job_record
            self._cancel_flags[job_id] = cancel_event
            self._version_counter[job_id] = 1

        ctx = JobContext(self, job_id)
        future = self._executor.submit(self._run_job_wrapper, job_id, ctx, fn, args, kwargs)
        with self._lock:
            self._futures[job_id] = future

        return self._snapshot(job_record)

    def _run_job_wrapper(
        self,
        job_id: str,
        ctx: JobContext,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        if self.is_cancelled(job_id):
            self._finalize_cancelled(job_id, "任务在启动前已取消")
            return None

        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job["status"] = "running"
                job["progress"] = max(int(job.get("progress", 0)), 1)
                job["message"] = "正在执行..."
                job["updated_at"] = _utc_now_iso()
                job["logs"].append(f"[{job['updated_at']}] 开始执行任务")
                self._version_counter[job_id] = self._version_counter.get(job_id, 0) + 1

        try:
            # Determine if `fn` accepts job_ctx as first argument
            pass_ctx = True
            try:
                sig = inspect.signature(fn)
                params = list(sig.parameters.values())
                has_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
                positional_params = [
                    p
                    for p in params
                    if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                ]
                if not has_varargs and len(positional_params) == len(args):
                    # Caller already supplied all positional parameters that fn expects
                    pass_ctx = False
            except Exception:
                pass_ctx = True

            if pass_ctx:
                result = fn(ctx, *args, **kwargs)
            else:
                result = fn(*args, **kwargs)

            if self.is_cancelled(job_id):
                self._finalize_cancelled(job_id, "任务已取消")
                return None

            with self._lock:
                job = self._jobs.get(job_id)
                if job is not None:
                    job["status"] = "succeeded"
                    job["progress"] = 100
                    if job.get("message") in ("", "正在执行...", "任务已进入队列，等待执行..."):
                        job["message"] = "执行完成"
                    job["result"] = result
                    if isinstance(result, dict) and result.get("output_path") and not job.get("output_path"):
                        job["output_path"] = str(result["output_path"])
                    job["updated_at"] = _utc_now_iso()
                    job["logs"].append(f"[{job['updated_at']}] 任务执行成功")
                    self._version_counter[job_id] = self._version_counter.get(job_id, 0) + 1
            return result

        except JobCancelledError as exc:
            self._finalize_cancelled(job_id, str(exc) or "任务已取消")
            return None
        except Exception as exc:
            logger.warning("Background job %s (%s) failed: %s", job_id, fn, exc, exc_info=True)
            with self._lock:
                job = self._jobs.get(job_id)
                if job is not None:
                    job["status"] = "failed"
                    job["error"] = str(exc)
                    job["message"] = f"执行失败: {exc}"
                    job["updated_at"] = _utc_now_iso()
                    job["logs"].append(f"[{job['updated_at']}] 错误: {exc}")
                    self._version_counter[job_id] = self._version_counter.get(job_id, 0) + 1
            return None

    def _finalize_cancelled(self, job_id: str, reason: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job["status"] = "cancelled"
                job["message"] = reason
                job["updated_at"] = _utc_now_iso()
                job["logs"].append(f"[{job['updated_at']}] {reason}")
                self._version_counter[job_id] = self._version_counter.get(job_id, 0) + 1

    def _update_job_from_ctx(
        self,
        job_id: str,
        progress: int | float | None = None,
        message: str | None = None,
        log: str | None = None,
        output_path: str | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            now_iso = _utc_now_iso()
            if progress is not None:
                job["progress"] = max(0, min(100, int(round(float(progress)))))
            if message is not None:
                job["message"] = str(message)
            if log is not None:
                job["logs"].append(f"[{now_iso}] {log}")
                if len(job["logs"]) > 500:
                    job["logs"] = job["logs"][-500:]
            if output_path is not None:
                job["output_path"] = str(output_path)
            job["updated_at"] = now_iso
            self._version_counter[job_id] = self._version_counter.get(job_id, 0) + 1

    def _snapshot(self, job: dict[str, Any]) -> dict[str, Any]:
        snap = dict(job)
        snap["logs"] = list(job.get("logs", []))
        return snap

    def list_jobs(self) -> list[dict[str, Any]]:
        """Return all jobs ordered from most recent to oldest."""
        with self._lock:
            items = [self._snapshot(j) for j in self._jobs.values()]
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Return a snapshot of a job by ID, or None if not found."""
        with self._lock:
            job = self._jobs.get(job_id)
            return self._snapshot(job) if job is not None else None

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            ev = self._cancel_flags.get(job_id)
            return bool(ev and ev.is_set())

    def cancel_job(self, job_id: str) -> bool:
        """Request cancellation of a queued or running job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            if job["status"] in ("succeeded", "failed", "cancelled"):
                return False
            ev = self._cancel_flags.get(job_id)
            if ev is not None:
                ev.set()
            fut = self._futures.get(job_id)
            if fut is not None and not fut.running():
                fut.cancel()
            job["status"] = "cancelled"
            job["message"] = "用户请求取消任务"
            job["updated_at"] = _utc_now_iso()
            job["logs"].append(f"[{job['updated_at']}] 用户请求取消任务")
            self._version_counter[job_id] = self._version_counter.get(job_id, 0) + 1
            return True

    async def stream_job_events(
        self,
        job_id: str,
        poll_interval: float = 0.1,
        timeout_sec: float = 600.0,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Async generator yielding job state updates for SSE streaming until terminal state."""
        last_version = -1
        start_ts = time.monotonic()

        while True:
            with self._lock:
                job = self._jobs.get(job_id)
                cur_version = self._version_counter.get(job_id, 0)
                snap = self._snapshot(job) if job is not None else None

            if snap is None:
                yield {
                    "type": "error",
                    "job_id": job_id,
                    "status": "not_found",
                    "error": f"未找到任务: {job_id}",
                }
                break

            if cur_version != last_version:
                last_version = cur_version
                event_payload = dict(snap)
                event_payload["type"] = (
                    "done" if snap["status"] in ("succeeded", "failed", "cancelled") else "progress"
                )
                event_payload["job"] = snap
                yield event_payload

            if snap["status"] in ("succeeded", "failed", "cancelled"):
                break

            if (time.monotonic() - start_ts) > timeout_sec:
                yield {
                    "type": "timeout",
                    "job_id": job_id,
                    "status": snap["status"],
                    "message": "SSE 流监听超时",
                }
                break

            await asyncio.sleep(poll_interval)


_JOB_MANAGER_SINGLETON: JobManager | None = None
_SINGLETON_LOCK = threading.Lock()


def get_job_manager() -> JobManager:
    """Return the process-wide singleton JobManager instance."""
    global _JOB_MANAGER_SINGLETON
    if _JOB_MANAGER_SINGLETON is None:
        with _SINGLETON_LOCK:
            if _JOB_MANAGER_SINGLETON is None:
                _JOB_MANAGER_SINGLETON = JobManager(max_workers=4)
    return _JOB_MANAGER_SINGLETON
