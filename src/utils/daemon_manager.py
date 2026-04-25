"""
daemon_manager.py — 算力服务后台守护进程管理器

功能：
1. 检测 Ollama (端口 11434) 和 SD WebUI (端口 7860) 是否在线
2. 自动拉起离线的服务进程（带 --api --xformers 参数）
3. 提供 Streamlit UI 组件：进度条 + 状态指示灯

使用方式：
    from src.utils.daemon_manager import render_daemon_control_panel
    render_daemon_control_panel()  # 在任意页面顶部调用
"""

import subprocess
import time
import os
import json
import streamlit as st
from pathlib import Path


# ==========================================
# 🔧 配置常量
# ==========================================

from src.utils.service_check import is_port_alive, OLLAMA_PORT, SD_PORT

# SD 路径配置文件（用户首次使用时需配置）
CONFIG_PATH = Path("config_daemon.json")

DEFAULT_CONFIG = {
    "ollama_model": "gemma4:e2b-it-q4_K_M",
    "sd_webui_path": r"E:\SDstablediffusion\sd-webui-aki\sd-webui-aki-v4.11.1-cu128\sd-webui-aki-v4.11.1-cu128",
    "sd_launch_file": "webui-user.bat",
    "sd_extra_args": "--api --xformers"
}


def _load_daemon_config():
    """加载守护进程配置"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    # 首次运行：创建默认配置
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    return DEFAULT_CONFIG


def _save_daemon_config(cfg):
    """保存守护进程配置"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ==========================================
# 🦙 Ollama 管理
# ==========================================
def check_ollama_model(model_name):
    """检查 Ollama 本地模型库中是否存在指定模型"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return model_name.split(":")[0] in result.stdout
    except Exception:
        pass
    return False


def start_ollama_serve():
    """后台静默启动 ollama serve 进程"""
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return True
    except Exception:
        return False


# ==========================================
# 🎨 SD WebUI 管理
# ==========================================
def start_sd_webui(sd_path, launch_file="webui-user.bat", extra_args="--api --xformers"):
    """
    后台静默启动 SD WebUI。
    通过修改 COMMANDLINE_ARGS 环境变量注入 --api --xformers 参数。
    """
    bat_path = os.path.join(sd_path, launch_file)
    if not os.path.exists(bat_path):
        return False, f"启动文件不存在: {bat_path}"

    try:
        env = os.environ.copy()
        env["COMMANDLINE_ARGS"] = extra_args

        subprocess.Popen(
            [bat_path],
            cwd=sd_path,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        return True, "SD WebUI 启动命令已发送"
    except Exception as e:
        return False, str(e)


# ==========================================
# 🖥️ Streamlit UI 渲染组件
# ==========================================
def render_daemon_control_panel():
    """
    渲染"算力指挥中心"控制面板。
    在页面顶部展示 Ollama 和 SD 的实时状态，并提供一键启动按钮。
    """
    cfg = _load_daemon_config()

    ollama_alive = is_port_alive(OLLAMA_PORT)
    sd_alive = is_port_alive(SD_PORT)

    # 如果两个服务都在线，不显示面板（减少视觉干扰）
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

    # --- Ollama 控制 ---
    with col_ollama:
        if ollama_alive:
            st.markdown('<div class="daemon-row"><span class="dot-online"></span> Ollama 大模型引擎 — <b style="color:#4ade80;">已联机</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="daemon-row"><span class="dot-offline"></span> Ollama 大模型引擎 — <b style="color:#ef4444;">未检测到</b></div>', unsafe_allow_html=True)

            if st.button("🦙 一键唤醒 Ollama", key="btn_start_ollama"):
                with st.spinner("正在检查本地模型库..."):
                    model_name = cfg.get("ollama_model", "gemma4:e2b-it-q4_K_M")
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

    # --- SD 控制 ---
    with col_sd:
        if sd_alive:
            st.markdown('<div class="daemon-row"><span class="dot-online"></span> Stable Diffusion 渲染引擎 — <b style="color:#4ade80;">已联机</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="daemon-row"><span class="dot-offline"></span> Stable Diffusion 渲染引擎 — <b style="color:#ef4444;">未检测到</b></div>', unsafe_allow_html=True)

            # 路径配置（可折叠）
            with st.expander("⚙️ SD 路径配置", expanded=False):
                new_path = st.text_input("SD WebUI 根目录绝对路径:", value=cfg.get("sd_webui_path", ""), key="sd_path_input")
                if new_path != cfg.get("sd_webui_path", ""):
                    cfg["sd_webui_path"] = new_path
                    _save_daemon_config(cfg)
                    st.success("路径已保存！")

                st.markdown("""
                <div style="font-size: 11px; color: #94a3b8; line-height: 1.6; margin-top: 8px;">
                    <b>📖 如何找到您的 SD 路径：</b><br>
                    1. 找到您安装 Stable Diffusion 的文件夹（通常带 <code>sd-webui</code> 字样）<br>
                    2. 文件管理器中右键 → 选择"复制文件夹路径"<br>
                    3. 粘贴至上方输入框<br>
                    <b>示例：</b><code>E:\\SDstablediffusion\\sd-webui-aki-v4.11.1</code>
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
                        cfg.get("sd_extra_args", "--api --xformers")
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
