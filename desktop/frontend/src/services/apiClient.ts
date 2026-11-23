import type {
  BinaryLayerHeader,
  BinaryLayerPayload,
} from "../types/api";
import type { UdPickFileOptions, UdSaveFileOptions } from "../vite-env";

let runtimeBaseUrl =
  typeof window !== "undefined" && window.udDesktop?.runtimeConfig?.apiBaseUrl
    ? window.udDesktop.runtimeConfig.apiBaseUrl.replace(/\/+$/, "")
    : "";
let runtimeToken =
  typeof window !== "undefined" && window.udDesktop?.runtimeConfig?.sessionToken
    ? window.udDesktop.runtimeConfig.sessionToken
    : "";
let initPromise: Promise<{ apiBaseUrl: string; sessionToken: string }> | null = null;

function extractTokenFromLocation(): string {
  if (typeof window === "undefined") return "";
  try {
    const searchParams = new URLSearchParams(window.location.search);
    const direct = searchParams.get("token");
    if (direct) return direct;
    const hash = window.location.hash || "";
    const qIdx = hash.indexOf("?");
    if (qIdx >= 0) {
      const hashParams = new URLSearchParams(hash.slice(qIdx + 1));
      return hashParams.get("token") || "";
    }
  } catch (_err) {
    // Ignore URL parsing errors
  }
  return "";
}

export async function ensureRuntimeInitialized(): Promise<{
  apiBaseUrl: string;
  sessionToken: string;
}> {
  if (initPromise) {
    return initPromise;
  }

  initPromise = (async () => {
    const urlToken = extractTokenFromLocation();
    if (urlToken) {
      runtimeToken = urlToken;
    }

    if (typeof window !== "undefined" && window.udDesktop?.getRuntimeConfig) {
      try {
        const cfg = await window.udDesktop.getRuntimeConfig();
        if (cfg?.apiBaseUrl) {
          runtimeBaseUrl = cfg.apiBaseUrl.replace(/\/+$/, "");
        }
        if (cfg?.sessionToken) {
          runtimeToken = cfg.sessionToken;
        }
      } catch (_err) {
        // Fallback to relative origin in browser/dev mode
      }
    }
    return {
      apiBaseUrl: runtimeBaseUrl,
      sessionToken: runtimeToken,
    };
  })();

  return initPromise;
}

export function getApiBaseUrl(): string {
  return runtimeBaseUrl;
}

export function getSessionToken(): string {
  if (!runtimeToken) {
    runtimeToken = extractTokenFromLocation();
  }
  return runtimeToken;
}

export function buildApiUrl(path: string, includeQueryToken = false): string {
  const normalizedPath = path.startsWith("http")
    ? path
    : `${runtimeBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;

  if (!includeQueryToken) {
    return normalizedPath;
  }

  const token = getSessionToken();
  if (!token) {
    return normalizedPath;
  }
  const sep = normalizedPath.includes("?") ? "&" : "?";
  return `${normalizedPath}${sep}token=${encodeURIComponent(token)}`;
}

function buildHeaders(extra?: Record<string, string>, isJson = true): HeadersInit {
  const headers: Record<string, string> = {};
  if (isJson) {
    headers["Content-Type"] = "application/json";
  }
  const token = getSessionToken();
  if (token) {
    headers["X-UD-Token"] = token;
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (extra) {
    Object.assign(headers, extra);
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const errJson = await res.json();
      detail = errJson.detail || errJson.message || errJson.error || JSON.stringify(errJson);
    } catch (_e) {
      try {
        const text = await res.text();
        if (text) detail = text;
      } catch (_e2) {
        // ignore
      }
    }
    throw new Error(detail);
  }
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await res.json()) as T;
  }
  return (await res.text()) as unknown as T;
}

export async function apiGet<T = any>(
  path: string,
  params?: Record<string, string | number | boolean | undefined | null>
): Promise<T> {
  await ensureRuntimeInitialized();
  let url = buildApiUrl(path);
  if (params) {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) {
        usp.set(k, String(v));
      }
    });
    const qs = usp.toString();
    if (qs) {
      url += (url.includes("?") ? "&" : "?") + qs;
    }
  }
  const res = await fetch(url, {
    method: "GET",
    headers: buildHeaders(undefined, false),
  });
  return handleResponse<T>(res);
}

export async function apiPost<T = any>(path: string, body?: any): Promise<T> {
  await ensureRuntimeInitialized();
  const url = buildApiUrl(path);
  const res = await fetch(url, {
    method: "POST",
    headers: buildHeaders(undefined, true),
    body: body !== undefined ? JSON.stringify(body) : JSON.stringify({}),
  });
  return handleResponse<T>(res);
}

export async function apiPut<T = any>(path: string, body?: any): Promise<T> {
  await ensureRuntimeInitialized();
  const url = buildApiUrl(path);
  const res = await fetch(url, {
    method: "PUT",
    headers: buildHeaders(undefined, true),
    body: body !== undefined ? JSON.stringify(body) : JSON.stringify({}),
  });
  return handleResponse<T>(res);
}

export async function apiDelete<T = any>(path: string): Promise<T> {
  await ensureRuntimeInitialized();
  const url = buildApiUrl(path);
  const res = await fetch(url, {
    method: "DELETE",
    headers: buildHeaders(undefined, false),
  });
  return handleResponse<T>(res);
}

export async function apiUpload<T = any>(path: string, formData: FormData): Promise<T> {
  await ensureRuntimeInitialized();
  const url = buildApiUrl(path);
  const res = await fetch(url, {
    method: "POST",
    headers: buildHeaders(undefined, false),
    body: formData,
  });
  return handleResponse<T>(res);
}

/**
 * Stream Server-Sent Events (SSE) over POST or GET with automatic token header injection.
 * Supports standard `event:` and `data:` SSE framing.
 */
export function streamSSE(
  path: string,
  body: any,
  onEvent: (data: any, eventType?: string) => void,
  onDone?: () => void,
  onError?: (err: Error) => void
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      await ensureRuntimeInitialized();
      const isGet = body === null || body === undefined;
      const url = buildApiUrl(path, true);
      const res = await fetch(url, {
        method: isGet ? "GET" : "POST",
        headers: buildHeaders(
          { Accept: "text/event-stream" },
          !isGet
        ),
        body: isGet ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });

      if (!res.ok) {
        let msg = `SSE HTTP ${res.status}`;
        try {
          const errJson = await res.json();
          msg = errJson.detail || errJson.message || msg;
        } catch (_e) {
          // ignore
        }
        throw new Error(msg);
      }

      if (!res.body) {
        onDone?.();
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let currentEvent = "message";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split(/\r?\n/);
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) {
            currentEvent = "message";
            continue;
          }
          if (trimmed.startsWith("event:")) {
            currentEvent = trimmed.slice(6).trim();
            continue;
          }
          if (trimmed.startsWith("data:")) {
            const rawData = trimmed.slice(5).trim();
            if (rawData === "[DONE]") {
              onDone?.();
              return;
            }
            try {
              const parsed = JSON.parse(rawData);
              onEvent(parsed, currentEvent);
            } catch (_parseErr) {
              onEvent({ text: rawData, chunk: rawData }, currentEvent);
            }
          }
        }
      }

      onDone?.();
    } catch (err: any) {
      if (err?.name === "AbortError") {
        return;
      }
      onError?.(err instanceof Error ? err : new Error(String(err)));
    }
  })();

  return controller;
}

/**
 * Fetch and zero-copy parse a binary packed Float32Array layer from:
 * `GET /api/v1/diagnosis/binary/{layer}`
 * Wire format:
 *   - Bytes 0..4: uint32 little-endian header byte length (N)
 *   - Bytes 4..(4+N): UTF-8 JSON metadata header ({ layer, count, stride, fields, ... })
 *   - Bytes (4+N)..EOF: Packed Float32Array payload (count * stride floats)
 */
export async function fetchBinaryLayer(layer: string): Promise<BinaryLayerPayload> {
  await ensureRuntimeInitialized();
  const url = buildApiUrl(`/api/v1/diagnosis/binary/${encodeURIComponent(layer)}`, true);
  const res = await fetch(url, {
    method: "GET",
    headers: buildHeaders(undefined, false),
  });

  if (!res.ok) {
    throw new Error(`加载二进制空间图层 ${layer} 失败 (HTTP ${res.status})`);
  }

  const arrayBuffer = await res.arrayBuffer();
  if (arrayBuffer.byteLength < 4) {
    return {
      header: { layer, count: 0, stride: 0, fields: [] },
      data: new Float32Array(0),
    };
  }

  const view = new DataView(arrayBuffer);
  const headerLen = view.getUint32(0, true);
  const payloadOffset = 4 + headerLen;

  if (payloadOffset > arrayBuffer.byteLength) {
    throw new Error(`二进制图层 ${layer} 头长度越界 (${headerLen} bytes)`);
  }

  const headerBytes = new Uint8Array(arrayBuffer, 4, headerLen);
  const headerText = new TextDecoder("utf-8").decode(headerBytes);
  const header = JSON.parse(headerText) as BinaryLayerHeader;

  const floatByteLength = arrayBuffer.byteLength - payloadOffset;
  let floatArray: Float32Array;
  if (payloadOffset % 4 === 0) {
    floatArray = new Float32Array(arrayBuffer, payloadOffset, Math.floor(floatByteLength / 4));
  } else {
    const alignedSlice = arrayBuffer.slice(payloadOffset);
    floatArray = new Float32Array(alignedSlice, 0, Math.floor(alignedSlice.byteLength / 4));
  }

  return {
    header,
    data: floatArray,
  };
}

/**
 * Returns the Mapbox Vector Tile (.pbf) URL template for MapLibre GL `vector` source.
 */
export function getMvtTileUrl(layer: string): string {
  const origin =
    runtimeBaseUrl ||
    (typeof window !== "undefined" && window.location?.origin
      ? window.location.origin
      : "http://127.0.0.1:8765");
  const baseTilePath = `${origin}/api/v1/diagnosis/tiles/${encodeURIComponent(
    layer
  )}/{z}/{x}/{y}.pbf`;
  const token = getSessionToken();
  return token ? `${baseTilePath}?token=${encodeURIComponent(token)}` : baseTilePath;
}

/**
 * Native Desktop IPC Helpers (with graceful web fallback)
 */
export async function pickLocalFile(options?: UdPickFileOptions): Promise<string[]> {
  if (typeof window !== "undefined" && window.udDesktop?.pickFile) {
    return window.udDesktop.pickFile(options);
  }
  return [];
}

export async function pickLocalDirectory(title?: string): Promise<string | null> {
  if (typeof window !== "undefined" && window.udDesktop?.pickDirectory) {
    return window.udDesktop.pickDirectory({ title });
  }
  return null;
}

export async function saveLocalFileAs(options?: UdSaveFileOptions): Promise<string | null> {
  if (typeof window !== "undefined" && window.udDesktop?.saveFileAs) {
    return window.udDesktop.saveFileAs(options);
  }
  return null;
}

export async function openInExplorer(targetPath: string): Promise<boolean> {
  if (!targetPath) return false;
  if (typeof window !== "undefined" && window.udDesktop?.openInExplorer) {
    return window.udDesktop.openInExplorer(targetPath);
  }
  return false;
}

export async function openDatavPopout(projectId?: string): Promise<boolean> {
  if (typeof window !== "undefined" && window.udDesktop?.openDatavPopoutWindow) {
    return window.udDesktop.openDatavPopoutWindow(projectId);
  }
  if (typeof window !== "undefined") {
    const token = getSessionToken();
    const qs = new URLSearchParams();
    if (projectId) qs.set("project", projectId);
    if (token) qs.set("token", token);
    window.open(
      `${window.location.origin}${window.location.pathname}#/datav-popout?${qs.toString()}`,
      "_blank",
      "width=1440,height=900"
    );
    return true;
  }
  return false;
}

export function resolveDroppedFilePath(file: File): string {
  if (typeof window !== "undefined" && window.udDesktop?.getPathForFile) {
    return window.udDesktop.getPathForFile(file);
  }
  return (file as any)?.path || "";
}
