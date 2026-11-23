"use strict";

const { contextBridge, ipcRenderer, webUtils } = require("electron");

/**
 * Synchronously fetch loopback sidecar runtime config at t=0ms so MVT tile URLs,
 * binary buffers, and static assets resolve immediately under app://ultimatedesign/.
 */
let syncRuntimeConfig = null;
try {
  syncRuntimeConfig = ipcRenderer.sendSync("ud:getRuntimeConfigSync");
} catch (_err) {
  syncRuntimeConfig = null;
}

/**
 * Context-isolated Desktop IPC Bridge exposed as `window.udDesktop`
 */
contextBridge.exposeInMainWorld("udDesktop", {
  /**
   * Synchronously available runtime config ({ apiBaseUrl, sessionToken, version, platform, unlockFps, sidecarMode })
   */
  runtimeConfig: syncRuntimeConfig,

  /**
   * Async accessor returning the latest runtime config
   */
  getRuntimeConfig: () => ipcRenderer.invoke("ud:getRuntimeConfig"),

  /**
   * Read & update persistent desktop preferences (e.g., unlockFps high-refresh-rate mode)
   */
  getDesktopPreferences: () => ipcRenderer.invoke("ud:getDesktopPreferences"),
  setDesktopPreferences: (prefs) => ipcRenderer.invoke("ud:setDesktopPreferences", prefs),

  /**
   * Opens native OS file picker and returns array of absolute file paths
   */
  pickFile: (options = {}) => ipcRenderer.invoke("ud:pickFile", options),

  /**
   * Opens native OS directory picker and returns selected folder path or null
   */
  pickDirectory: (options = {}) => ipcRenderer.invoke("ud:pickDirectory", options),

  /**
   * Opens native OS Save As dialog and returns target file path or null
   */
  saveFileAs: (options = {}) => ipcRenderer.invoke("ud:saveFileAs", options),

  /**
   * Highlights the generated file in Windows Explorer / OS file manager
   */
  openInExplorer: (targetPath) => ipcRenderer.invoke("ud:openInExplorer", targetPath),

  /**
   * Opens or focuses the secondary monitor sc-datav fullscreen cockpit window
   */
  openDatavPopoutWindow: (projectId) =>
    ipcRenderer.invoke("ud:openDatavPopoutWindow", projectId),

  /**
   * Shows native hardware / GPU / DuckDB Spatial / rustworkx diagnostics dialog
   */
  openHardwareDiagnostics: () => ipcRenderer.invoke("ud:openHardwareDiagnostics"),

  /**
   * Subscribe to native Windows menu bar commands (e.g., navigate route, toggle copilot)
   */
  onMenuCommand: (callback) => {
    if (typeof callback !== "function") return () => {};
    const handler = (_event, payload) => callback(payload);
    ipcRenderer.on("ud:menu-command", handler);
    return () => ipcRenderer.removeListener("ud:menu-command", handler);
  },

  /**
   * Resolves true native filesystem path from a dropped File object
   */
  getPathForFile: (file) => {
    if (!file) return "";
    if (webUtils && typeof webUtils.getPathForFile === "function") {
      try {
        return webUtils.getPathForFile(file) || file.path || "";
      } catch (_err) {
        return file.path || "";
      }
    }
    return file.path || "";
  },
});
