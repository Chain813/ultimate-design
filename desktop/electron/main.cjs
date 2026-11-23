"use strict";

const {
  app,
  BrowserWindow,
  Menu,
  ipcMain,
  dialog,
  shell,
  protocol,
  screen,
} = require("electron");
const path = require("path");
const fs = require("fs");
const net = require("net");
const http = require("http");
const crypto = require("crypto");
const { pathToFileURL } = require("url");
const { spawn, execSync } = require("child_process");

// ============================================================================
// 1. Pre-Ready GPU & High-Refresh-Rate Engine Configuration
// ============================================================================

/**
 * Register privileged desktop protocol `app://ultimatedesign/` BEFORE app ready.
 * Gives bundled frontend static files (inside app.asar) native 0ms disk boot,
 * real secure origin, full WebGL2/Worker support, and zero browser URL feel.
 */
protocol.registerSchemesAsPrivileged([
  {
    scheme: "app",
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true,
      corsEnabled: true,
      stream: true,
      allowServiceWorkers: true,
    },
  },
]);

/**
 * Resolve workspace root cleanly in both packaged (.exe) and dev modes.
 * Walks upward from app directory / executable directory to locate project root
 * containing `desktop/backend` or `data/gis` (portable-first design).
 */
function resolveWorkspaceRoot() {
  const candidates = [];
  if (process.env.UD_WORKSPACE_ROOT) {
    candidates.push(path.resolve(process.env.UD_WORKSPACE_ROOT));
  }
  if (app.isPackaged) {
    const exeDir = path.dirname(process.execPath);
    candidates.push(
      exeDir,
      path.resolve(exeDir, ".."),
      path.resolve(exeDir, "..", ".."),
      path.resolve(exeDir, "..", "..", ".."),
      process.resourcesPath
    );
  }
  candidates.push(
    path.resolve(__dirname, "..", ".."),
    process.cwd()
  );

  for (const dir of candidates) {
    try {
      if (
        fs.existsSync(path.join(dir, "desktop", "backend", "main.py")) ||
        fs.existsSync(path.join(dir, "resources", "sidecar", "ud-sidecar.exe")) ||
        fs.existsSync(path.join(dir, "data", "gis"))
      ) {
        return dir;
      }
    } catch (_err) {
      // ignore permission errors
    }
  }
  return path.resolve(__dirname, "..", "..");
}

function resolvePreferencesPath() {
  try {
    const userDir = app.getPath("userData");
    fs.mkdirSync(userDir, { recursive: true });
    return path.join(userDir, "desktop-prefs.json");
  } catch (_err) {
    return path.join(resolveWorkspaceRoot(), "output", "desktop-prefs.json");
  }
}

function loadDesktopPreferences() {
  const defaults = {
    unlockFps: false, // Default: native display VSync (60/120/144/165/240Hz); true: unlimited FPS
    windowBounds: { width: 1600, height: 980 },
  };
  try {
    const prefPath = resolvePreferencesPath();
    if (fs.existsSync(prefPath)) {
      const parsed = JSON.parse(fs.readFileSync(prefPath, "utf-8"));
      return { ...defaults, ...parsed };
    }
  } catch (_err) {
    // ignore corrupt prefs
  }
  return defaults;
}

function saveDesktopPreferences(patch) {
  const next = { ...desktopPrefs, ...patch };
  desktopPrefs = next;
  try {
    const prefPath = resolvePreferencesPath();
    fs.mkdirSync(path.dirname(prefPath), { recursive: true });
    fs.writeFileSync(prefPath, JSON.stringify(next, null, 2), "utf-8");
  } catch (_err) {
    // ignore write failure
  }
  return next;
}

let desktopPrefs = loadDesktopPreferences();

// Enable hardware-accelerated WebGL2 / ANGLE / zero-copy GPU rasterization
app.commandLine.appendSwitch("enable-webgl");
app.commandLine.appendSwitch("ignore-gpu-blocklist");
app.commandLine.appendSwitch("enable-gpu-rasterization");
app.commandLine.appendSwitch("enable-zero-copy");

// Optional: Unlock VSync frame-rate ceiling for uncapped GPU benchmarking / max responsiveness
if (desktopPrefs.unlockFps) {
  app.commandLine.appendSwitch("disable-frame-rate-limit");
  app.commandLine.appendSwitch("disable-gpu-vsync");
}

// ============================================================================
// 2. Single-Instance Lock (Protects DuckDB ACID file locks from duplicate launch)
// ============================================================================

const gotSingleInstanceLock = app.requestSingleInstanceLock();
if (!gotSingleInstanceLock) {
  app.quit();
}

const repoRoot = resolveWorkspaceRoot();
let sidecarProc = null;
let sidecarPort = 0;
let sidecarMode = "winpython";
const sessionToken = crypto.randomBytes(32).toString("hex");
let mainWindow = null;
let datavPopoutWindow = null;
let isQuitting = false;

/**
 * Resolve bundled frontend dist directory (works inside app.asar AND dev tree)
 */
function resolveFrontendDistDir() {
  const candidates = [
    path.join(__dirname, "frontend-dist"),
    path.join(repoRoot, "desktop", "frontend", "dist"),
    path.join(process.resourcesPath || "", "frontend-dist"),
  ];
  for (const dir of candidates) {
    if (dir && fs.existsSync(path.join(dir, "index.html"))) {
      return dir;
    }
  }
  return null;
}

/**
 * Resolve application window icon
 */
function resolveAppIcon() {
  const candidates = [
    path.join(__dirname, "build", "icon.ico"),
    path.join(__dirname, "build", "icon.png"),
    path.join(process.resourcesPath || "", "icon.ico"),
    path.join(repoRoot, "desktop", "electron", "build", "icon.ico"),
  ];
  for (const candidate of candidates) {
    if (candidate && fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return undefined;
}

/**
 * 3-Tier Future-Proof Sidecar Discovery:
 *  Tier 1: Compiled standalone C/Nuitka native binary (`resources/sidecar/ud-sidecar.exe`)
 *  Tier 2: Bundled portable Python runtime (`resources/runtime/python/python.exe` or `<repo>/WinPython/python/python.exe`)
 *  Tier 3: `UD_PYTHON_PATH` env var or system `python`
 */
function discoverSidecarCommand(port) {
  const exeDir = app.isPackaged ? path.dirname(process.execPath) : repoRoot;

  // Tier 1: Nuitka compiled native binary sidecar
  const nativeCandidates = [
    path.join(process.resourcesPath || "", "sidecar", "ud-sidecar.exe"),
    path.join(exeDir, "sidecar", "ud-sidecar.exe"),
    path.join(repoRoot, "release", "sidecar", "ud-sidecar.exe"),
  ];
  for (const binPath of nativeCandidates) {
    if (binPath && fs.existsSync(binPath)) {
      sidecarMode = "nuitka-native";
      return {
        command: binPath,
        args: ["--host", "127.0.0.1", "--port", String(port)],
      };
    }
  }

  // Tier 2: Bundled portable Python / WinPython
  const pythonCandidates = [
    path.join(process.resourcesPath || "", "runtime", "python", "python.exe"),
    path.join(exeDir, "WinPython", "python", "python.exe"),
    path.join(repoRoot, "WinPython", "python", "python.exe"),
    process.env.UD_PYTHON_PATH || "",
  ];
  for (const pyPath of pythonCandidates) {
    if (pyPath && fs.existsSync(pyPath)) {
      sidecarMode = pyPath.includes("WinPython") ? "winpython-portable" : "embedded-python";
      return {
        command: pyPath,
        args: [
          "-m",
          "uvicorn",
          "desktop.backend.main:app",
          "--host",
          "127.0.0.1",
          "--port",
          String(port),
        ],
      };
    }
  }

  // Tier 3: System python fallback
  sidecarMode = "system-python";
  return {
    command: "python",
    args: [
      "-m",
      "uvicorn",
      "desktop.backend.main:app",
      "--host",
      "127.0.0.1",
      "--port",
      String(port),
    ],
  };
}

function allocateFreeLoopbackPort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.unref();
    srv.on("error", reject);
    srv.listen(0, "127.0.0.1", () => {
      const addr = srv.address();
      const port = typeof addr === "object" && addr ? addr.port : 8765;
      srv.close(() => resolve(port));
    });
  });
}

function waitForSidecarHealth(port, timeoutMs = 45000) {
  const startTime = Date.now();
  const healthUrl = `http://127.0.0.1:${port}/api/v1/system/health`;

  return new Promise((resolve, reject) => {
    const check = () => {
      if (isQuitting) {
        return reject(new Error("Application is quitting"));
      }
      const req = http.get(healthUrl, { timeout: 1000 }, (res) => {
        res.resume();
        if (res.statusCode === 200) {
          resolve(true);
        } else if (Date.now() - startTime >= timeoutMs) {
          reject(new Error(`Sidecar health returned HTTP ${res.statusCode}`));
        } else {
          setTimeout(check, 180);
        }
      });

      req.on("error", () => {
        if (Date.now() - startTime >= timeoutMs) {
          reject(new Error("等待本地空间计算内核就绪超时 (45s)"));
        } else {
          setTimeout(check, 180);
        }
      });

      req.on("timeout", () => req.destroy());
    };

    check();
  });
}

function spawnSidecar(port) {
  const { command, args } = discoverSidecarCommand(port);
  const env = {
    ...process.env,
    PYTHONNOUSERSITE: "1",
    PYTHONUTF8: "1",
    PYTHONPATH: repoRoot,
    UD_SESSION_TOKEN: sessionToken,
    UD_PARENT_PID: String(process.pid),
    UD_PORT: String(port),
    UD_WORKSPACE_ROOT: repoRoot,
  };

  sidecarProc = spawn(command, args, {
    cwd: repoRoot,
    env,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  if (sidecarProc.stdout) {
    sidecarProc.stdout.on("data", (chunk) => {
      if (!app.isPackaged) {
        process.stdout.write(`[UD-Sidecar] ${chunk.toString()}`);
      }
    });
  }
  if (sidecarProc.stderr) {
    sidecarProc.stderr.on("data", (chunk) => {
      if (!app.isPackaged) {
        process.stderr.write(`[UD-Sidecar] ${chunk.toString()}`);
      }
    });
  }
  sidecarProc.on("exit", (code, signal) => {
    sidecarProc = null;
    if (!isQuitting && !app.isPackaged) {
      console.log(`[UD-Sidecar] exited (code=${code}, signal=${signal})`);
    }
  });
}

function stopSidecar() {
  if (!sidecarProc || !sidecarProc.pid) {
    return;
  }
  const pid = sidecarProc.pid;
  sidecarProc = null;
  try {
    if (process.platform === "win32") {
      execSync(`taskkill /PID ${pid} /T /F`, { stdio: "ignore", windowsHide: true });
    } else {
      process.kill(pid, "SIGTERM");
    }
  } catch (_err) {
    // Already exited
  }
}

function getRuntimeConfigObject() {
  const primaryDisplay = screen.getPrimaryDisplay();
  return {
    apiBaseUrl: `http://127.0.0.1:${sidecarPort}`,
    sessionToken,
    version: "7.0.0",
    platform: process.platform,
    isPackaged: app.isPackaged,
    sidecarMode,
    unlockFps: Boolean(desktopPrefs.unlockFps),
    displayRefreshHz: primaryDisplay?.displayFrequency || 60,
  };
}

function buildLoadingSplashDataUrl(message) {
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<title>UltimateDESIGN v7.0 Studio</title>
<style>
  body {
    margin: 0; height: 100vh; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: #f5f5f7; color: #1d1d1f;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    user-select: none;
  }
  .card {
    background: #ffffff; border: 1px solid rgba(0,0,0,0.08); border-radius: 20px;
    padding: 36px 48px; box-shadow: 0 20px 50px rgba(0,0,0,0.07);
    text-align: center; max-width: 500px;
  }
  .badge {
    display: inline-block; padding: 4px 12px; border-radius: 999px;
    background: rgba(0,113,227,0.1); color: #0071e3;
    font-size: 12px; font-weight: 600; margin-bottom: 14px;
  }
  h1 { margin: 0 0 8px 0; font-size: 21px; font-weight: 700; color: #1d1d1f; }
  p { margin: 0 0 22px 0; font-size: 13px; color: #515154; line-height: 1.6; }
  .spinner {
    width: 30px; height: 30px; margin: 0 auto;
    border: 3px solid rgba(0,113,227,0.18); border-top-color: #0071e3;
    border-radius: 50%; animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
  <div class="card">
    <div class="badge">UltimateDESIGN v7.0 Native Desktop Workstation</div>
    <h1>正在启动空间算力与 3D 数字孪生工作站</h1>
    <p>${message}</p>
    <div class="spinner"></div>
  </div>
</body>
</html>`;
  return `data:text/html;charset=utf-8,${encodeURIComponent(html)}`;
}

/**
 * Register custom `app://ultimatedesign/` protocol serving bundled dist/ directly from app.asar
 */
function registerDesktopAppProtocol() {
  const distDir = resolveFrontendDistDir();
  if (!distDir) return false;

  protocol.handle("app", (request) => {
    const url = new URL(request.url);
    let pathname = decodeURIComponent(url.pathname || "/");
    if (pathname === "/" || pathname === "") {
      pathname = "/index.html";
    }
    const candidate = path.normalize(path.join(distDir, pathname));
    const safeTarget = candidate.startsWith(path.normalize(distDir))
      ? candidate
      : path.join(distDir, "index.html");
    const finalFile = fs.existsSync(safeTarget) && fs.statSync(safeTarget).isFile()
      ? safeTarget
      : path.join(distDir, "index.html");

    const fileUrl = pathToFileURL(finalFile).toString();
    return require("electron").net.fetch(fileUrl);
  });
  return true;
}

function sendMenuCommand(command, payload = {}) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("ud:menu-command", { command, ...payload });
  }
}

async function openHardwareDiagnosticsDialog() {
  const cfg = getRuntimeConfigObject();
  const gpuInfo = await app.getGPUInfo("basic").catch(() => ({}));
  const gpuModel =
    (Array.isArray(gpuInfo?.gpuDevice) && gpuInfo.gpuDevice[0]?.description) ||
    "Hardware Accelerated WebGL2 / ANGLE";
  await dialog.showMessageBox(mainWindow, {
    type: "info",
    title: "UltimateDESIGN v7.0 · 硬件与空间算力诊断",
    message: "UltimateDESIGN v7.0 原生桌面工作站运行状态",
    detail: [
      `应用打包模式: ${cfg.isPackaged ? "独立编译可执行程序 (app.asar)" : "开发运行模式"}`,
      `空间后端内核: ${cfg.sidecarMode} (127.0.0.1:${sidecarPort})`,
      `数据工作根目录: ${repoRoot}`,
      `显示器原生刷新率: ${cfg.displayRefreshHz} Hz`,
      `帧率上限模式: ${cfg.unlockFps ? "已解锁 VSync (无上限满帧)" : `跟随显示器原生刷新率 (${cfg.displayRefreshHz} FPS VSync)`}`,
      `GPU 加速引擎: ${gpuModel}`,
      `Electron / Chromium: ${process.versions.electron} / ${process.versions.chrome}`,
    ].join("\n"),
    buttons: ["确定"],
  });
}

async function openDatavPopout(projectId = "changchun_default") {
  const useCustomProtocol = Boolean(resolveFrontendDistDir());
  const baseUrl = useCustomProtocol
    ? "app://ultimatedesign/index.html"
    : `http://127.0.0.1:${sidecarPort}/`;
  const targetUrl = `${baseUrl}#/datav-popout?project=${encodeURIComponent(
    projectId || "changchun_default"
  )}&token=${encodeURIComponent(sessionToken)}`;

  if (datavPopoutWindow && !datavPopoutWindow.isDestroyed()) {
    await datavPopoutWindow.loadURL(targetUrl);
    datavPopoutWindow.focus();
    return true;
  }

  // Prefer secondary monitor automatically if connected!
  const displays = screen.getAllDisplays();
  const primary = screen.getPrimaryDisplay();
  const secondary = displays.find((d) => d.id !== primary.id);

  const bounds = secondary
    ? {
        x: secondary.bounds.x + 40,
        y: secondary.bounds.y + 40,
        width: Math.min(1600, secondary.bounds.width - 80),
        height: Math.min(960, secondary.bounds.height - 80),
      }
    : { width: 1440, height: 900 };

  datavPopoutWindow = new BrowserWindow({
    ...bounds,
    minWidth: 1024,
    minHeight: 680,
    icon: resolveAppIcon(),
    title: "UltimateDESIGN v7.0 · sc-datav 全域空间态势副屏指挥舱",
    backgroundColor: "#0b1120",
    autoHideMenuBar: true,
    fullscreenable: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  datavPopoutWindow.on("closed", () => {
    datavPopoutWindow = null;
  });

  await datavPopoutWindow.loadURL(targetUrl);
  return true;
}

/**
 * Build Native Windows Desktop Application Menu Bar
 */
function buildNativeApplicationMenu() {
  const template = [
    {
      label: "文件(&F)",
      submenu: [
        {
          label: "导入本地空间矢量/数据...",
          accelerator: "CmdOrCtrl+O",
          click: () => sendMenuCommand("navigate", { route: "wb1", subTab: "assets" }),
        },
        {
          label: "打开工程输出目录 (output)",
          click: () => {
            const outDir = path.join(repoRoot, "output");
            fs.mkdirSync(outDir, { recursive: true });
            shell.openPath(outDir);
          },
        },
        { type: "separator" },
        {
          label: "系统与模型密钥设置",
          accelerator: "CmdOrCtrl+,",
          click: () => sendMenuCommand("open-settings"),
        },
        { type: "separator" },
        { label: "退出 UltimateDESIGN", accelerator: "Alt+F4", role: "quit" },
      ],
    },
    {
      label: "工作台(&W)",
      submenu: [
        {
          label: "首页指挥中枢",
          accelerator: "CmdOrCtrl+0",
          click: () => sendMenuCommand("navigate", { route: "home" }),
        },
        {
          label: "工作台 01 · 全息空间诊断与数据沙盘",
          accelerator: "CmdOrCtrl+1",
          click: () => sendMenuCommand("navigate", { route: "wb1", subTab: "diagnosis" }),
        },
        {
          label: "工作台 02 · 多主体博弈与空间 AIGC 工坊",
          accelerator: "CmdOrCtrl+2",
          click: () => sendMenuCommand("navigate", { route: "wb2", subTab: "strategy" }),
        },
        {
          label: "工作台 03 · 数字图则与工程交付枢纽",
          accelerator: "CmdOrCtrl+3",
          click: () => sendMenuCommand("navigate", { route: "wb3", subTab: "delivery" }),
        },
        { type: "separator" },
        {
          label: "独立副屏弹出 sc-datav 全屏大屏",
          accelerator: "CmdOrCtrl+Shift+D",
          click: () => openDatavPopout(),
        },
        {
          label: "展开 / 折叠 AI 规划副驾",
          accelerator: "CmdOrCtrl+Shift+A",
          click: () => sendMenuCommand("toggle-copilot"),
        },
      ],
    },
    {
      label: "性能与渲染(&P)",
      submenu: [
        {
          label: "解除 VSync 帧率封顶（无上限满帧模式）",
          type: "checkbox",
          checked: Boolean(desktopPrefs.unlockFps),
          click: async (menuItem) => {
            saveDesktopPreferences({ unlockFps: menuItem.checked });
            const res = await dialog.showMessageBox(mainWindow, {
              type: "question",
              title: "帧率渲染引擎切换",
              message: menuItem.checked
                ? "已开启「无上限满帧模式（禁用 GPU VSync）」，重启应用后立即生效。"
                : "已恢复「显示器原生刷新率同步（VSync 满刷不撕裂）」，重启应用后生效。",
              buttons: ["立即重启生效", "稍后手动重启"],
              defaultId: 0,
            });
            if (res.response === 0) {
              stopSidecar();
              app.relaunch();
              app.exit(0);
            }
          },
        },
        { type: "separator" },
        { label: "重新加载界面", accelerator: "CmdOrCtrl+R", role: "reload" },
        { label: "切换全屏显示", accelerator: "F11", role: "togglefullscreen" },
        { label: "缩放恢复默认", accelerator: "CmdOrCtrl+0", role: "resetZoom" },
      ],
    },
    {
      label: "帮助(&H)",
      submenu: [
        {
          label: "硬件加速与空间算力诊断...",
          click: () => openHardwareDiagnosticsDialog(),
        },
        {
          label: "打开开发者工具 (DevTools)",
          accelerator: "F12",
          click: () => {
            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.webContents.toggleDevTools();
            }
          },
        },
        { type: "separator" },
        {
          label: "关于 UltimateDESIGN v7.0 Desktop Studio",
          click: () => openHardwareDiagnosticsDialog(),
        },
      ],
    },
  ];
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// ============================================================================
// 3. IPC Handlers Registration
// ============================================================================

function registerIpcHandlers() {
  ipcMain.on("ud:getRuntimeConfigSync", (event) => {
    event.returnValue = getRuntimeConfigObject();
  });

  ipcMain.handle("ud:getRuntimeConfig", async () => getRuntimeConfigObject());

  ipcMain.handle("ud:getDesktopPreferences", async () => desktopPrefs);

  ipcMain.handle("ud:setDesktopPreferences", async (_event, patch = {}) => {
    const prevUnlock = Boolean(desktopPrefs.unlockFps);
    const updated = saveDesktopPreferences(patch);
    buildNativeApplicationMenu();
    return {
      ...updated,
      requiresRestart: Boolean(updated.unlockFps) !== prevUnlock,
    };
  });

  ipcMain.handle("ud:openHardwareDiagnostics", async () => {
    await openHardwareDiagnosticsDialog();
    return true;
  });

  ipcMain.handle("ud:pickFile", async (_event, options = {}) => {
    const filters =
      Array.isArray(options.filters) && options.filters.length > 0
        ? options.filters
        : [
            {
              name: "规划空间与文档数据 (GeoJSON/SHP/DXF/CSV/PDF/MD)",
              extensions: [
                "geojson",
                "json",
                "shp",
                "dxf",
                "csv",
                "pdf",
                "docx",
                "md",
                "txt",
                "jpg",
                "png",
              ],
            },
            { name: "All Files", extensions: ["*"] },
          ];
    const properties = ["openFile"];
    if (options.multi) {
      properties.push("multiSelections");
    }
    const res = await dialog.showOpenDialog(mainWindow, {
      title: options.title || "选择规划空间或文档文件",
      filters,
      properties,
    });
    return res.canceled ? [] : res.filePaths;
  });

  ipcMain.handle("ud:pickDirectory", async (_event, options = {}) => {
    const res = await dialog.showOpenDialog(mainWindow, {
      title: options.title || "选择文件夹",
      properties: ["openDirectory", "createDirectory"],
    });
    if (res.canceled || !res.filePaths || res.filePaths.length === 0) {
      return null;
    }
    return res.filePaths[0];
  });

  ipcMain.handle("ud:saveFileAs", async (_event, options = {}) => {
    const res = await dialog.showSaveDialog(mainWindow, {
      title: options.title || "另存规划交付成果",
      defaultPath: options.defaultName || "UltimateDESIGN_Export",
      filters: options.filters || [{ name: "All Files", extensions: ["*"] }],
    });
    return res.canceled ? null : res.filePath || null;
  });

  ipcMain.handle("ud:openInExplorer", async (_event, targetPath) => {
    if (!targetPath || typeof targetPath !== "string") {
      return false;
    }
    const resolved = path.isAbsolute(targetPath)
      ? targetPath
      : path.resolve(repoRoot, targetPath);
    if (fs.existsSync(resolved)) {
      shell.showItemInFolder(resolved);
      return true;
    }
    const parentDir = path.dirname(resolved);
    if (fs.existsSync(parentDir)) {
      await shell.openPath(parentDir);
      return true;
    }
    return false;
  });

  ipcMain.handle("ud:openDatavPopoutWindow", async (_event, projectId = "changchun_default") =>
    openDatavPopout(projectId)
  );
}

// ============================================================================
// 4. Main Window Bootstrap
// ============================================================================

async function createMainWindow(hasCustomProtocol) {
  const saved = desktopPrefs.windowBounds || { width: 1600, height: 980 };
  mainWindow = new BrowserWindow({
    width: Math.max(1280, saved.width || 1600),
    height: Math.max(760, saved.height || 980),
    minWidth: 1200,
    minHeight: 720,
    icon: resolveAppIcon(),
    title: "UltimateDESIGN v7.0 Studio — 城市设计与微更新原生桌面工作站",
    backgroundColor: "#f5f5f7",
    show: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow.on("close", () => {
    try {
      if (mainWindow && !mainWindow.isDestroyed() && !mainWindow.isMinimized()) {
        const bounds = mainWindow.getBounds();
        saveDesktopPreferences({
          windowBounds: { width: bounds.width, height: bounds.height },
        });
      }
    } catch (_err) {
      // ignore
    }
  });

  await mainWindow.loadURL(
    buildLoadingSplashDataUrl(
      "正在挂载 DuckDB Spatial (C++ SIMD) 与 rustworkx 空间句法内核，请稍候…"
    )
  );

  try {
    await waitForSidecarHealth(sidecarPort, 45000);
    if (hasCustomProtocol) {
      await mainWindow.loadURL("app://ultimatedesign/index.html");
    } else {
      await mainWindow.loadURL(
        `http://127.0.0.1:${sidecarPort}/?token=${encodeURIComponent(sessionToken)}`
      );
    }
  } catch (err) {
    await mainWindow.loadURL(
      buildLoadingSplashDataUrl(`空间算力内核启动超时或异常：${err.message || String(err)}`)
    );
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.on("second-instance", () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  }
});

app.whenReady().then(async () => {
  const hasCustomProtocol = registerDesktopAppProtocol();
  registerIpcHandlers();
  buildNativeApplicationMenu();
  sidecarPort = await allocateFreeLoopbackPort();
  spawnSidecar(sidecarPort);
  await createMainWindow(hasCustomProtocol);
});

app.on("before-quit", () => {
  isQuitting = true;
  stopSidecar();
});

app.on("will-quit", () => {
  isQuitting = true;
  stopSidecar();
});

app.on("window-all-closed", () => {
  isQuitting = true;
  stopSidecar();
  app.quit();
});

process.on("SIGINT", () => {
  isQuitting = true;
  stopSidecar();
  process.exit(0);
});

process.on("SIGTERM", () => {
  isQuitting = true;
  stopSidecar();
  process.exit(0);
});
