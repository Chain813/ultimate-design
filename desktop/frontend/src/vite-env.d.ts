/// <reference types="vite/client" />

export interface UdRuntimeConfig {
  apiBaseUrl: string;
  sessionToken: string;
  version: string;
  platform: string;
  isPackaged?: boolean;
  sidecarMode?: string;
  unlockFps?: boolean;
  displayRefreshHz?: number;
}

export interface UdDesktopPreferences {
  unlockFps?: boolean;
  windowBounds?: { width: number; height: number };
  requiresRestart?: boolean;
}

export interface UdFileFilter {
  name: string;
  extensions: string[];
}

export interface UdPickFileOptions {
  title?: string;
  filters?: UdFileFilter[];
  multi?: boolean;
}

export interface UdSaveFileOptions {
  title?: string;
  defaultName?: string;
  filters?: UdFileFilter[];
}

export interface UdMenuCommand {
  command: "navigate" | "toggle-copilot" | "open-settings" | string;
  route?: "home" | "wb1" | "wb2" | "wb3" | "datav-popout";
  subTab?: string;
}

export interface UdDesktopBridge {
  runtimeConfig?: UdRuntimeConfig | null;
  getRuntimeConfig: () => Promise<UdRuntimeConfig>;
  getDesktopPreferences?: () => Promise<UdDesktopPreferences>;
  setDesktopPreferences?: (prefs: Partial<UdDesktopPreferences>) => Promise<UdDesktopPreferences>;
  pickFile: (options?: UdPickFileOptions) => Promise<string[]>;
  pickDirectory: (options?: { title?: string }) => Promise<string | null>;
  saveFileAs: (options?: UdSaveFileOptions) => Promise<string | null>;
  openInExplorer: (targetPath: string) => Promise<boolean>;
  openDatavPopoutWindow: (projectId?: string) => Promise<boolean>;
  openHardwareDiagnostics?: () => Promise<boolean>;
  onMenuCommand?: (callback: (payload: UdMenuCommand) => void) => () => void;
  getPathForFile: (file: File) => string;
}

declare global {
  interface Window {
    udDesktop?: UdDesktopBridge;
  }
}
