"""Desktop window launcher for ultimateDESIGN using pywebview."""

import os
import sys
import subprocess
import time
import socket
import webview

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    port = 8501
    while is_port_in_use(port):
        port += 1
        
    print(f"Starting background Streamlit server on port {port}...")
    
    # Run streamlit in headless mode
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.headless", "true",
        "--server.enableStaticServing", "true",
        "--server.port", str(port)
    ]
    
    # Hide terminal window for the child process on Windows
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0 # SW_HIDE

    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo
    )
    
    # Wait for streamlit port to open
    server_ready = False
    for _ in range(40):
        if is_port_in_use(port):
            server_ready = True
            break
        time.sleep(0.5)
        
    if not server_ready:
        print("Error: Streamlit server failed to start.")
        process.terminate()
        return

    print("Launching native desktop window...")
    # Initialize pywebview window
    window = webview.create_window(
        title="长春伪满皇宫周边街区微更新决策支持平台",
        url=f"http://localhost:{port}",
        width=1440,
        height=900,
        resizable=True
    )
    
    # Open the window (this blocks until closed)
    webview.start()
    
    # Terminate streamlit server when window is closed
    print("Terminating background Streamlit server...")
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()

if __name__ == "__main__":
    main()
