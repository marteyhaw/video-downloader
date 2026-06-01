# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

## Health

### `GET /api/health`

Returns system health and configuration status.

**Response:**
```json
{
  "status": "ok",
  "ffmpeg_available": true,
  "ytdlp_impersonate_enabled": true,
  "ytdlp_impersonate_available": true,
  "downloads_dir": "C:/…/downloads",
  "database_path": "C:/…/video_downloader.db"
}
```

## Scan

### `POST /api/scan`

Synchronous scan (returns all results at once).

**Request:**
```json
{ "url": "https://example.com/video-page" }
```

**Response:** `ScanResponse` (see below).

### `GET /api/scan/stream?url=…`

Server-Sent Events scan with real-time progress.

**SSE event format:**
```
data: {"stage": "ytdlp", "message": "Trying yt-dlp extractors…"}
data: {"stage": "result", "message": "Scan complete", "data": {…ScanResponse…}}
data: {"stage": "done", "message": ""}
```

Error events include `"stage": "error"` and `"status_code"`.

**ScanResponse shape:**
```json
{
  "items": [
    {
      "id": "abc123",
      "title": "Video 720p mp4 (http-720)",
      "url": "https://…/video.mp4",
      "manifest_url": null,
      "ext": "mp4",
      "height": 720,
      "width": 1280,
      "has_audio": true,
      "source": "ytdlp",
      "format_id": "http-720",
      "thumbnail": "https://…/thumb.jpg",
      "filesize": 12345678,
      "video_codec": "H.264",
      "bandwidth": null,
      "webpage_url": "https://example.com/video-page"
    }
  ],
  "page_title": "Example Video",
  "warning": null
}
```

## Download

### `POST /api/download`

Start a download job.

**Request:**
```json
{
  "item_id": "abc123",
  "title": "My Video",
  "url": "https://…/video.mp4",
  "manifest_url": null,
  "ext": "mp4",
  "source": "ytdlp",
  "format_id": "http-720",
  "include_audio": true,
  "container": "mp4",
  "page_url": "https://example.com/video-page",
  "webpage_url": "https://example.com/video-page",
  "filename": "my-video"
}
```

**Response:** `JobStatus`

### `GET /api/jobs/{job_id}`

Poll a download job.

**Response:**
```json
{
  "id": "uuid",
  "state": "running",
  "progress": 0.45,
  "stage": "Downloading via yt-dlp",
  "output_path": null,
  "error": null
}
```

States: `pending` → `running` → `done` | `error`

### `GET /api/download/filename-check?filename=…`

Check if a filename already exists in the downloads directory.

**Response:**
```json
{
  "requested": "my-video.mp4",
  "exists": true,
  "suggested": "my-video (1).mp4"
}
```

## History

### `GET /api/history?limit=200&offset=0`

List download history (paginated, ordered by newest first).

**Response:** array of `HistoryEntry`:
```json
[
  {
    "id": 1,
    "title": "My Video",
    "display_name": "my-video.mp4",
    "file_path": "C:/…/downloads/my-video.mp4",
    "source_url": "https://example.com",
    "file_size": 12345678,
    "created_at": "2025-01-15T12:00:00Z",
    "file_status": "ok",
    "resolved_path": null
  }
]
```

`file_status`: `"ok"` | `"missing"` | `"moved"` (resolved_path set when moved).

### `PATCH /api/history/{id}`

Rename a download.

**Request:** `{ "display_name": "new-name.mp4" }`

### `POST /api/history/{id}/reveal`

Open the file in the system file manager.

### `DELETE /api/history/{id}?delete_file=false`

Delete a history record (optionally the file too).
