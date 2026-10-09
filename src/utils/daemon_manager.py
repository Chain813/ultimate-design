"""daemon_manager.py — 算力服务后台守护进程管理器与生命周期控制。

功能：
1. DaemonProcessManager: 提供 Stable Diffusion WebUI 与 Ollama 的统一进程管理
   (start / stop / restart / is_running / tail_logs / get_service_status)
2. 跨平台（尤其是 Windows）子进程生命周期管控、PID 记录与端口健康检查
3. Streamlit UI 组件：render_daemon_control_panel() 算力指挥中心面板
"""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from src.config.paths import ROOT_DIR
from src.utils.service_check import OLLAMA_PORT, SD_PORT, is_port_alive

logger = logging.getLogger("ultimateDESIGN")

CONFIG_PATH = ROOT_DIR / "config" / "config_daemon.json"
PID_DIR = ROOT_DIR / "logs" / "pids"
LOG_DIR = ROOT_DIR / "logs" / "daemon"

DEFAULT_CONFIG = {
    "ollama_model": "deepseek-v4-pro",
    "sd_webui_path": "",
    "sd_launch_file": "webui-user.bat",
    "sd_extra_args": "--api --xformers"
}


def _load_daemon_config() -> dict[str, Any]:
    """加载守护进程配置，优先从环境变量读取 SD_WEBUI_PATH。"""
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    cfg.update(saved)
        except Exception as e:
            logger.warning(f"Failed to read {CONFIG_PATH}: {e}")

    env_sd_path = os.getenv("SD_WEBUI_PATH")
    if env_sd_path:
        cfg["sd_webui_path"] = env_sd_path

    env_ollama_model = os.getenv("OLLAMA_MODEL")
    if env_ollama_model:
        cfg["ollama_model"] = env_ollama_model

    return cfg


def _save_daemon_config(cfg: dict[str, Any]) -> None:
    """持久化守护进程配置。"""
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save daemon config: {e}")


class DaemonProcessManager:
    """算力微服务（Ollama & SD WebUI）守护进程管理器。"""

    PORT_MAP = {
        "ollama": OLLAMA_PORT,
        "sd": SD_PORT,
        "sd_webui": SD_PORT,
    }

    def __init__(self, pid_dir: Path | None = None, log_dir: Path | None = None):
        self.pid_dir = pid_dir or PID_DIR
        self.log_dir = log_dir or LOG_DIR
        self.pid_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_name(self, service: str) -> str:
        s = service.lower().strip()
        if s in ("sd", "sd_webui", "stable-diffusion", "stablediffusion"):
            return "sd"
        if s in ("ollama", "ollama_serve"):
            return "ollama"
        return s

    def _pid_file(self, service: str) -> Path:
        return self.pid_dir / f"{self._normalize_name(service)}.pid"

    def _log_file(self, service: str) -> Path:
        return self.log_dir / f"{self._normalize_name(service)}.log"

    def _read_pid(self, service: str) -> int | None:
        pf = self._pid_file(service)
        if not pf.exists():
            return None
        try:
            val = int(pf.read_text(encoding="utf-8").strip())
            return val if val > 0 else None
        except Exception:
            return None

    def _write_pid(self, service: str, pid: int) -> None:
        self._pid_file(service).write_text(str(pid), encoding="utf-8")

    def _clear_pid(self, service: str) -> None:
        pf = self._pid_file(service)
        if pf.exists():
            try:
                pf.unlink()
            except Exception:
                pass

    def _is_pid_alive(self, pid: int) -> bool:
        """跨平台检查进程号是否存在且正在运行。"""
        if pid <= 0:
            return False
        if os.name == "nt":
            try:
                # Windows tasklist 快速检测
                proc = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                return str(pid) in proc.stdout
            except Exception:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False

    def is_running(self, service: str) -> bool:
        """检测服务是否处于运行状态（结合 PID 存活性与端口检测）。"""
        svc = self._normalize_name(service)
        port = self.PORT_MAP.get(svc)
        port_alive = is_port_alive(port) if port else False

        pid = self._read_pid(svc)
        if pid and self._is_pid_alive(pid):
            return True

        if port_alive:
            return True

        return False

    def get_service_status(self, service: str) -> dict[str, Any]:
        """获取服务的详细状态信息。"""
        svc = self._normalize_name(service)
        port = self.PORT_MAP.get(svc)
        pid = self._read_pid(svc)
        pid_alive = self._is_pid_alive(pid) if pid else False
        port_alive = is_port_alive(port) if port else False

        return {
            "service": svc,
            "running": pid_alive or port_alive,
            "pid": pid if pid_alive else None,
            "port": port,
            "port_alive": port_alive,
            "log_path": str(self._log_file(svc)),
        }

    def start(self, service: str, **kwargs) -> tuple[bool, str]:
        """启动指定微服务。"""
        svc = self._normalize_name(service)
        if self.is_running(svc):
            return True, f"服务 {svc} 已在运行中。"

        cfg = _load_daemon_config()

        if svc == "ollama":
            return self._start_ollama()
        elif svc == "sd":
            sd_path = kwargs.get("sd_path") or cfg.get("sd_webui_path", "")
            launch_file = kwargs.get("launch_file") or cfg.get("sd_launch_file", "webui-user.bat")
            extra_args = kwargs.get("extra_args") or cfg.get("sd_extra_args", "--api --xformers")
            return self._start_sd(sd_path, launch_file, extra_args)
        else:
            return False, f"未知服务类型: {service}"

    def _start_ollama(self) -> tuple[bool, str]:
        log_fp = self._log_file("ollama")
        try:
            with open(log_fp, "a", encoding="utf-8") as out:
                creationflags = 0
                if os.name == "nt":
                    creationflags = (
                        subprocess.CREATE_NEW_PROCESS_GROUP
                        | subprocess.CREATE_NO_WINDOW
                    )

                proc = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=out,
                    stderr=out,
                    creationflags=creationflags,
                )
                self._write_pid("ollama", proc.pid)
                logger.info(f"Ollama serve process launched with PID {proc.pid}")
                return True, f"Ollama 启动指令已发送 (PID: {proc.pid})"
        except FileNotFoundError:
            return False, "未找到 ollama 可执行文件，请确认已安装 Ollama 并加入 PATH 环境变量。"
        except Exception as e:
            logger.error(f"Failed to start Ollama: {e}")
            return False, str(e)

    def _start_sd(self, sd_path: str, launch_file: str, extra_args: str) -> tuple[bool, str]:
        if not sd_path or not os.path.isdir(sd_path):
            return False, f"SD WebUI 路径无效或不存在: {sd_path}"

        bat_path = os.path.join(sd_path, launch_file)
        if not os.path.exists(bat_path):
            return False, f"启动脚本不存在: {bat_path}"

        log_fp = self._log_file("sd")
        try:
            env = os.environ.copy()
            env["COMMANDLINE_ARGS"] = extra_args

            with open(log_fp, "a", encoding="utf-8") as out:
                creationflags = 0
                if os.name == "nt":
                    creationflags = subprocess.CREATE_NEW_CONSOLE

                proc = subprocess.Popen(
                    [bat_path],
                    cwd=sd_path,
                    env=env,
                    stdout=out,
                    stderr=out,
                    creationflags=creationflags,
                )
                self._write_pid("sd", proc.pid)
                logger.info(f"SD WebUI launched with PID {proc.pid}")
                return True, f"SD WebUI 启动指令已发送 (PID: {proc.pid})"
        except Exception as e:
            logger.error(f"Failed to start SD WebUI: {e}")
            return False, str(e)

    def stop(self, service: str) -> tuple[bool, str]:
        """停止指定服务（优雅退出 + 强制终止）。"""
        svc = self._normalize_name(service)
        pid = self._read_pid(svc)

        if not pid or not self._is_pid_alive(pid):
            self._clear_pid(svc)
            return True, f"服务 {svc} 未记录有效运行 PID。"

        try:
            if os.name == "nt":
                # Windows 采用 taskkill 杀死进程树
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            else:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                if self._is_pid_alive(pid):
                    os.kill(pid, signal.SIGKILL)

            self._clear_pid(svc)
            logger.info(f"Service {svc} (PID {pid}) stopped successfully.")
            return True, f"服务 {svc} (PID {pid}) 已成功停止。"
        except subprocess.TimeoutExpired:
            self._clear_pid(svc)
            logger.warning(f"Taskkill timed out for {svc} (PID {pid}), forcibly cleared PID record.")
            return True, f"停止指令超时，已强制清理服务 {svc} 的 PID 登记。"
        except Exception as e:
            self._clear_pid(svc)
            logger.error(f"Failed to stop service {svc}: {e}")
            return False, f"停止服务失败: {e}"

    def restart(self, service: str, **kwargs) -> tuple[bool, str]:
        """重启服务。"""
        svc = self._normalize_name(service)
        self.stop(svc)
        time.sleep(1.5)
        return self.start(svc, **kwargs)

    def tail_logs(self, service: str, lines: int = 50) -> str:
        """获取指定服务的最新日志尾部内容。"""
        log_fp = self._log_file(service)
        if not log_fp.exists():
            return "（暂无日志文件）"

        try:
            with open(log_fp, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return "".join(tail)
        except Exception as e:
            return f"读取日志出错: {e}"


# ==========================================
# 顶层向下兼容函数
# ==========================================

_default_manager = DaemonProcessManager()


def check_ollama_model(model_name: str) -> bool:
    """检查 Ollama 本地模型库中是否存在指定模型。"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            prefix = model_name.split(":")[0]
            return prefix in result.stdout
    except Exception:
        pass
    return False


def start_ollama_serve() -> bool:
    """后台启动 ollama serve 进程。"""
    ok, _ = _default_manager.start("ollama")
    return ok


def start_sd_webui(
    sd_path: str,
    launch_file: str = "webui-user.bat",
    extra_args: str = "--api --xformers",
) -> tuple[bool, str]:
    """后台启动 SD WebUI。"""
    return _default_manager.start(
        "sd",
        sd_path=sd_path,
        launch_file=launch_file,
        extra_args=extra_args,
    )


def render_daemon_control_panel():
    """渲染'算力指挥中心'控制面板，供 Streamlit 页面顶部调用。"""
    import streamlit as st

    cfg = _load_daemon_config()

    ollama_alive = is_port_alive(OLLAMA_PORT)
    sd_alive = is_port_alive(SD_PORT)

    if ollama_alive and sd_alive:
        return

    st.markdown("""
    <style>
        .daemon-panel {
            background: rgba(10, 15, 30, 0.6);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 16px;
        }
        .daemon-title {
            font-size: 14px; font-weight: 700; color: #a5b4fc;
            margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
        }
        .daemon-row {
            display: flex; align-items: center; gap: 10px;
            margin-bottom: 8px; font-size: 13px; color: #cbd5e1;
        }
        .dot-online { width: 10px; height: 10px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 12px #4ade80; }
        .dot-offline { width: 10px; height: 10px; border-radius: 50%; background: #ef4444; box-shadow: 0 0 12px #ef4444; animation: pulse-red 1.5s infinite; }
        @keyframes pulse-red { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="daemon-panel">
        <div class="daemon-title">⚡ 算力指挥中心 — 服务挂载状态</div>
    </div>
    """, unsafe_allow_html=True)

    col_ollama, col_sd = st.columns(2)

    with col_ollama:
        if ollama_alive:
            st.markdown('<div class="daemon-row"><span class="dot-online"></span> Ollama 大模型引擎 — <b style="color:#4ade80;">已联机</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="daemon-row"><span class="dot-offline"></span> Ollama 大模型引擎 — <b style="color:#ef4444;">未检测到</b></div>', unsafe_allow_html=True)

            if st.button("🦙 一键唤醒 Ollama", key="btn_start_ollama"):
                with st.spinner("正在检查本地模型库..."):
                    model_name = cfg.get("ollama_model", "deepseek-v4-pro")
                    has_model = check_ollama_model(model_name)

                    if not has_model:
                        st.error(f"❌ 本地模型库中未找到 `{model_name}`。请先在终端执行: `ollama pull {model_name}`")
                    else:
                        progress = st.progress(0, text="正在启动 Ollama Serve...")
                        start_ollama_serve()
                        for i in range(100):
                            time.sleep(0.05)
                            progress.progress(i + 1, text=f"Ollama 启动中... {i+1}%")
                            if i > 30 and is_port_alive(OLLAMA_PORT):
                                progress.progress(100, text="✅ Ollama 已成功联机！")
                                time.sleep(0.5)
                                st.rerun()
                                return
                        if is_port_alive(OLLAMA_PORT):
                            st.success("✅ Ollama 已成功联机！")
                            st.rerun()
                        else:
                            st.warning("⏳ Ollama 正在后台加载模型, 请稍等片刻后刷新页面。")

    with col_sd:
        if sd_alive:
            st.markdown('<div class="daemon-row"><span class="dot-online"></span> Stable Diffusion 渲染引擎 — <b style="color:#4ade80;">已联机</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="daemon-row"><span class="dot-offline"></span> Stable Diffusion 渲染引擎 — <b style="color:#ef4444;">未检测到</b></div>', unsafe_allow_html=True)

            with st.expander("⚙️ SD 路径配置", expanded=False):
                current_sd_path = cfg.get("sd_webui_path", "")
                new_path = st.text_input("SD WebUI 根目录绝对路径 (或配置环境变量 SD_WEBUI_PATH):", value=current_sd_path, key="sd_path_input")
                if new_path != current_sd_path:
                    cfg["sd_webui_path"] = new_path
                    _save_daemon_config(cfg)
                    st.success("路径已保存！")

                st.markdown("""
                <div style="font-size: 11px; color: #94a3b8; line-height: 1.6; margin-top: 8px;">
                    <b>📖 如何找到您的 SD 路径：</b><br>
                    1. 找到您安装 Stable Diffusion 的文件夹（通常包含 <code>webui-user.bat</code>）<br>
                    2. 复制文件夹完整绝对路径粘贴至上方<br>
                    <b>提示：</b>也可通过环境变量 <code>SD_WEBUI_PATH</code> 配置
                </div>
                """, unsafe_allow_html=True)

            if st.button("🎨 一键唤醒 SD (--api --xformers)", key="btn_start_sd"):
                sd_path = cfg.get("sd_webui_path", "")
                if not sd_path or not os.path.isdir(sd_path):
                    st.error("❌ SD 路径无效，请先在上方配置正确的安装路径。")
                else:
                    progress = st.progress(0, text="正在启动 Stable Diffusion...")
                    ok, msg = start_sd_webui(
                        sd_path,
                        cfg.get("sd_launch_file", "webui-user.bat"),
                        cfg.get("sd_extra_args", "--api --xformers"),
                    )
                    if ok:
                        for i in range(100):
                            time.sleep(0.8)
                            progress.progress(min(i + 1, 99), text=f"SD 模型加载中 (约需 30-60 秒)... {min(i+1, 99)}%")
                            if is_port_alive(SD_PORT):
                                progress.progress(100, text="✅ Stable Diffusion 已成功联机！(API + xformers)")
                                time.sleep(0.5)
                                st.rerun()
                                return
                        st.warning("⏳ SD 正在后台初始化模型，这通常需要 30-90 秒。请稍后刷新页面。")
                    else:
                        st.error(f"❌ 启动失败: {msg}")
