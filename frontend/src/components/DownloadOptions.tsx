import { useEffect, useState } from "react";
import { checkDownloadFilename, MediaItem } from "../api/client";
import { SelectField } from "./SelectField";
import { btnPrimaryClass, inputClass, labelClass } from "./ui";

interface Props {
  item: MediaItem;
  onDownload: (opts: { container: string; includeAudio: boolean; filename: string }) => void;
  downloading: boolean;
}

function defaultNameFromTitle(title: string): string {
  const sanitized = title
    .slice(0, 120)
    .replace(/[<>:"/\\|?*]/g, "_")
    .trim();
  const stem = sanitized.replace(/\.[^.\\/]+$/, "") || "download";
  return stem;
}

const CONTAINER_OPTIONS = ["mp4", "webm", "mkv"] as const;

function defaultContainerFromItem(item: MediaItem): string {
  const ext = item.ext.toLowerCase().trim();
  if ((CONTAINER_OPTIONS as readonly string[]).includes(ext)) return ext;
  return "mp4";
}

export function DownloadOptions({ item, onDownload, downloading }: Props) {
  const [container, setContainer] = useState(() => defaultContainerFromItem(item));
  const [name, setName] = useState(() => defaultNameFromTitle(item.title));
  const [includeAudio, setIncludeAudio] = useState(item.source === "ytdlp" ? true : item.has_audio);
  const [collision, setCollision] = useState<{
    requested: string;
    suggested: string;
  } | null>(null);

  useEffect(() => {
    setContainer(defaultContainerFromItem(item));
    setName(defaultNameFromTitle(item.title));
    setIncludeAudio(item.source === "ytdlp" ? true : item.has_audio);
    setCollision(null);
  }, [item.id, item.title, item.source, item.has_audio, item.ext]);

  useEffect(() => {
    const stem = name.trim();
    if (!stem) {
      setCollision(null);
      return;
    }

    const fullFilename = `${stem}.${container}`;
    let cancelled = false;
    const timer = setTimeout(() => {
      void checkDownloadFilename(fullFilename)
        .then((result) => {
          if (cancelled) return;
          if (result.exists) {
            setCollision({
              requested: result.requested,
              suggested: result.suggested,
            });
          } else {
            setCollision(null);
          }
        })
        .catch(() => {
          if (!cancelled) setCollision(null);
        });
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [name, container]);

  return (
    <>
      <div className="mb-4 flex flex-col gap-4">
        <div>
          <label htmlFor="download-filename" className={labelClass}>
            Name
          </label>
          <input
            id="download-filename"
            type="text"
            className={inputClass}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="my-video"
          />
          {collision && (
            <p className="mt-1.5 mb-0 text-xs text-warn" role="status">
              {collision.requested} already exists. Will save as{" "}
              <span className="font-semibold">{collision.suggested}</span>.
            </p>
          )}
        </div>
        <div className="max-w-xs">
          <label htmlFor="container" className={labelClass}>
            Container
          </label>
          <SelectField
            id="container"
            value={container}
            onChange={(e) => setContainer(e.target.value)}
          >
            <option value="mp4">MP4</option>
            <option value="webm">WebM</option>
            <option value="mkv">MKV</option>
          </SelectField>
        </div>
      </div>
      {item.source === "playwright" && (item.ext === "m3u8" || item.url.includes(".m3u8")) && (
        <p className="mb-0 text-xs text-muted">
          HLS download uses the selected variant and page referer (audio merged when enabled).
        </p>
      )}
      <div className="mt-6 flex items-center gap-2">
        <input
          id="include-audio"
          type="checkbox"
          className="h-4 w-4 accent-accent"
          checked={includeAudio}
          onChange={(e) => setIncludeAudio(e.target.checked)}
        />
        <label htmlFor="include-audio" className="text-sm text-foreground">
          Include audio
          {item.has_audio && <span className="font-normal text-muted"> (merged on download)</span>}
        </label>
      </div>
      <button
        type="button"
        className={`${btnPrimaryClass} mt-4`}
        onClick={() =>
          onDownload({
            container,
            includeAudio,
            filename: name.trim() || defaultNameFromTitle(item.title),
          })
        }
        disabled={downloading || !name.trim()}
      >
        {downloading ? "Downloading…" : "Download"}
      </button>
    </>
  );
}
