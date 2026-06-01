import { memo } from "react";
import { MediaItem } from "../api/client";
import { deliveryKindLabel, deriveDeliveryKind } from "../utils/mediaFilters";
import { Tooltip } from "./Tooltip";

interface Props {
  item: MediaItem;
  selected: boolean;
  onSelect: (item: MediaItem) => void;
}

export const MediaCard = memo(function MediaCard({ item, selected, onSelect }: Props) {
  const delivery = deriveDeliveryKind(item);
  const deliveryLabel = deliveryKindLabel(delivery);
  const deliveryTitle =
    item.format_id && delivery !== "other"
      ? `${deliveryLabel} · ${item.format_id}`
      : delivery !== "other"
        ? deliveryLabel
        : undefined;

  return (
    <div
      className={`flex cursor-pointer gap-4 rounded-md border p-3.5 transition-[colors,opacity,transform] duration-300 ease-out ${
        selected ? "border-accent bg-accent-muted" : "border-border hover:bg-surface-hover"
      }`}
      onClick={() => onSelect(item)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(item);
        }
      }}
      role="button"
      tabIndex={0}
      aria-pressed={selected}
    >
      {item.thumbnail && (
        <img
          src={item.thumbnail}
          alt=""
          loading="lazy"
          className="h-11 w-20 shrink-0 rounded-sm bg-background object-cover"
        />
      )}
      <div className="min-w-0 flex-1">
        <div className="mb-0.5 flex min-w-0 items-center gap-2 font-medium">
          <Tooltip text={item.title} className="min-w-0 flex-1">
            <span className="tooltip-text block min-w-0">{item.title}</span>
          </Tooltip>
          {item.source === "ytdlp" ? (
            <span className="shrink-0 rounded px-1.5 py-0.5 text-[0.7rem] font-semibold uppercase bg-badge-ytdlp/15 text-badge-ytdlp">
              ytdlp
            </span>
          ) : (
            <span
              className="shrink-0 rounded px-1.5 py-0.5 text-[0.7rem] font-semibold uppercase bg-badge-playwright/15 text-badge-playwright"
              title="Captured from network traffic while the page loaded"
            >
              network
            </span>
          )}
        </div>
        <div className="mt-0.5 flex flex-wrap gap-1.5">
          {item.width != null && item.height != null && (
            <span className="rounded px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide bg-badge-resolution/15 text-badge-resolution">
              {item.width}×{item.height}
            </span>
          )}
          {item.height != null && item.width == null && (
            <span className="rounded px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide bg-badge-resolution/15 text-badge-resolution">
              {item.height}p
            </span>
          )}
          {item.bandwidth != null && (
            <span className="rounded px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide bg-badge-muted/15 text-badge-muted">
              {Math.round(item.bandwidth / 1000)}k
            </span>
          )}
          <span className="rounded px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide bg-badge-muted/15 text-badge-muted">
            {item.ext}
          </span>
          {delivery !== "other" && (
            <span
              className="rounded px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide bg-badge-muted/15 text-badge-muted"
              title={deliveryTitle}
            >
              {deliveryLabel}
            </span>
          )}
          {item.video_codec && (
            <span className="rounded px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide bg-badge-muted/15 text-badge-muted">
              {item.video_codec}
            </span>
          )}
          <span
            className={`rounded px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide ${
              item.has_audio
                ? "bg-badge-audio/15 text-badge-audio"
                : "bg-badge-audio-warn/15 text-badge-audio-warn"
            }`}
            title={
              item.source === "ytdlp" && item.has_audio
                ? "Audio merged on download when needed"
                : undefined
            }
          >
            {item.has_audio ? "audio" : "no audio track"}
          </span>
          {item.filesize != null && (
            <span className="rounded px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide bg-accent-muted text-accent-hover">
              {(item.filesize / 1_048_576).toFixed(1)} MB
            </span>
          )}
        </div>
      </div>
    </div>
  );
});
