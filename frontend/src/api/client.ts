export interface MediaItem {
  id: string;
  title: string;
  url: string;
  manifest_url: string | null;
  ext: string;
  height: number | null;
  width: number | null;
  has_audio: boolean;
  source: "ytdlp" | "playwright";
  format_id: string | null;
  thumbnail: string | null;
  filesize: number | null;
  video_codec: string | null;
  bandwidth: number | null;
  webpage_url?: string | null;
}

export interface ScanResponse {
  items: MediaItem[];
  page_title: string;
  warning?: string | null;
}

export interface JobStatus {
  id: string;
  state: "pending" | "running" | "done" | "error";
  progress: number;
  stage: string;
  output_path: string | null;
  error: string | null;
}

export interface HistoryEntry {
  id: number;
  title: string;
  display_name: string;
  file_path: string;
  source_url: string | null;
  file_size: number | null;
  created_at: string;
  file_status: "ok" | "missing" | "moved";
  resolved_path: string | null;
}

export interface FilenameCheckResponse {
  requested: string;
  exists: boolean;
  suggested: string;
}

export interface HealthResponse {
  status: string;
  ffmpeg_available: boolean;
  ytdlp_impersonate_enabled: boolean;
  ytdlp_impersonate_available: boolean;
  downloads_dir: string;
  database_path: string;
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).join(", ")
          : res.statusText || "Request failed";
    throw new Error(message);
  }
  return res.json();
}

export interface ScanProgressEvent {
  stage: string;
  message: string;
  data?: ScanResponse;
  status_code?: number;
}

export interface StartDownloadBody {
  item_id: string;
  title: string;
  url: string;
  manifest_url?: string | null;
  ext: string;
  source: "ytdlp" | "playwright";
  format_id?: string | null;
  include_audio: boolean;
  container: string;
  page_url?: string;
  webpage_url?: string;
  filename?: string;
}

export function scanUrlStream(
  url: string,
  onProgress: (event: ScanProgressEvent) => void,
  signal?: AbortSignal,
): Promise<ScanResponse> {
  return new Promise((resolve, reject) => {
    const es = new EventSource(`/api/scan/stream?url=${encodeURIComponent(url)}`);

    const cleanup = () => {
      es.close();
    };

    signal?.addEventListener("abort", () => {
      cleanup();
      reject(new DOMException("Scan aborted", "AbortError"));
    });

    es.onmessage = (msg) => {
      let event: ScanProgressEvent;
      try {
        event = JSON.parse(msg.data) as ScanProgressEvent;
      } catch {
        return;
      }

      if (event.stage === "done") {
        cleanup();
        return;
      }

      onProgress(event);

      if (event.stage === "result" && event.data) {
        cleanup();
        resolve(event.data);
        return;
      }

      if (event.stage === "error") {
        cleanup();
        reject(new Error(event.message || "Scan failed"));
      }
    };

    es.onerror = () => {
      cleanup();
      reject(new Error("Scan connection lost"));
    };
  });
}

export const startDownload = (body: StartDownloadBody) =>
  api<JobStatus>("/api/download", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const getJob = (id: string) => api<JobStatus>(`/api/jobs/${id}`);

export const checkDownloadFilename = (filename: string) =>
  api<FilenameCheckResponse>(
    `/api/download/filename-check?filename=${encodeURIComponent(filename)}`,
  );

export const fetchHistory = () => api<HistoryEntry[]>("/api/history");

export const renameHistory = (id: number, display_name: string) =>
  api<HistoryEntry>(`/api/history/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ display_name }),
  });

export const revealInFolder = (id: number) =>
  api<{ path: string }>(`/api/history/${id}/reveal`, { method: "POST" });

export const deleteHistory = (id: number, deleteFile = false) =>
  api<{ deleted: boolean; id: number }>(
    `/api/history/${id}?delete_file=${deleteFile ? "true" : "false"}`,
    { method: "DELETE" },
  );

export const fetchHealth = () => api<HealthResponse>("/api/health");
