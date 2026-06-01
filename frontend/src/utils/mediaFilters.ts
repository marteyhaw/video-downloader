import { MediaItem } from "../api/client";

export type AudioFilter = "audio" | "no-audio";
export type FilesizeFilter = "has-size" | "no-size";
export type DeliveryKind = "dash" | "hls" | "http" | "other";

export type FilterGroupId =
  | "sources"
  | "heights"
  | "exts"
  | "delivery"
  | "codecs"
  | "audio"
  | "filesize";

export type FilterValue =
  | MediaItem["source"]
  | number
  | string
  | AudioFilter
  | FilesizeFilter
  | DeliveryKind;

export interface MediaFilterState {
  sources: Set<MediaItem["source"]>;
  heights: Set<number>;
  exts: Set<string>;
  delivery: Set<DeliveryKind>;
  codecs: Set<string>;
  audio: Set<AudioFilter>;
  filesize: Set<FilesizeFilter>;
}

export interface FilterGroupMeta {
  id: FilterGroupId;
  label: string;
  dynamic: boolean;
}

export interface ActiveFilterChip {
  group: FilterGroupId;
  value: FilterValue;
  label: string;
  activeClass: string;
}

export interface FilterAvailability {
  sources: Record<MediaItem["source"], boolean>;
  heights: Record<number, boolean>;
  exts: Record<string, boolean>;
  delivery: Record<DeliveryKind, boolean>;
  codecs: Record<string, boolean>;
  audio: Record<AudioFilter, boolean>;
  filesize: Record<FilesizeFilter, boolean>;
}

export const STATIC_SOURCES: MediaItem["source"][] = ["ytdlp", "playwright"];
export const STATIC_DELIVERY: DeliveryKind[] = ["dash", "hls", "http"];
export const STATIC_CODECS = ["H.264", "VP9", "AV1", "HEVC"] as const;
export const STATIC_AUDIO: AudioFilter[] = ["audio", "no-audio"];
export const STATIC_FILESIZE: FilesizeFilter[] = ["has-size", "no-size"];

export const FILTER_GROUPS: FilterGroupMeta[] = [
  { id: "sources", label: "Source", dynamic: false },
  { id: "heights", label: "Resolution", dynamic: true },
  { id: "exts", label: "Format", dynamic: true },
  { id: "delivery", label: "Delivery", dynamic: true },
  { id: "codecs", label: "Codec", dynamic: false },
  { id: "audio", label: "Audio", dynamic: false },
  { id: "filesize", label: "Size", dynamic: false },
];

export function deliveryKindLabel(kind: DeliveryKind): string {
  switch (kind) {
    case "dash":
      return "DASH";
    case "hls":
      return "HLS";
    case "http":
      return "HTTP";
    case "other":
      return "other";
  }
}

export function deriveDeliveryKind(item: MediaItem): DeliveryKind {
  const fid = (item.format_id || "").toLowerCase();
  if (fid.startsWith("dash-")) return "dash";
  if (fid.startsWith("hls-")) return "hls";
  if (fid.startsWith("http-") || fid.startsWith("https-")) return "http";

  if (item.source === "playwright") {
    if (item.ext === "m3u8" || item.manifest_url) return "hls";
    return "http";
  }

  if (item.manifest_url || item.ext === "m3u8") return "hls";

  try {
    const path = new URL(item.url).pathname.toLowerCase();
    if (path.includes(".mpd")) return "dash";
  } catch {
    // ignore invalid URL
  }

  if (item.source === "ytdlp" && !item.manifest_url && item.ext !== "m3u8") {
    return "http";
  }

  return "other";
}

export function emptyFilters(): MediaFilterState {
  return {
    sources: new Set(),
    heights: new Set(),
    exts: new Set(),
    delivery: new Set(),
    codecs: new Set(),
    audio: new Set(),
    filesize: new Set(),
  };
}

export function hasActiveFilters(state: MediaFilterState): boolean {
  return countActiveFilters(state) > 0;
}

export function countActiveFilters(state: MediaFilterState): number {
  return (
    state.sources.size +
    state.heights.size +
    state.exts.size +
    state.delivery.size +
    state.codecs.size +
    state.audio.size +
    state.filesize.size
  );
}

export function getFilterChipMeta(
  group: FilterGroupId,
  value: FilterValue,
): { label: string; activeClass: string } {
  switch (group) {
    case "sources": {
      const source = value as MediaItem["source"];
      return {
        label: source === "ytdlp" ? "ytdlp" : "network",
        activeClass:
          source === "ytdlp"
            ? "bg-badge-ytdlp/15 text-badge-ytdlp"
            : "bg-badge-playwright/15 text-badge-playwright",
      };
    }
    case "heights":
      return {
        label: `${value}p`,
        activeClass: "bg-badge-resolution/15 text-badge-resolution",
      };
    case "exts":
    case "codecs":
      return {
        label: String(value),
        activeClass: "bg-badge-muted/15 text-badge-muted",
      };
    case "delivery":
      return {
        label: deliveryKindLabel(value as DeliveryKind),
        activeClass: "bg-badge-muted/15 text-badge-muted",
      };
    case "audio":
      return {
        label: value === "audio" ? "audio" : "no audio track",
        activeClass:
          value === "audio"
            ? "bg-badge-audio/15 text-badge-audio"
            : "bg-badge-audio-warn/15 text-badge-audio-warn",
      };
    case "filesize":
      return {
        label: value === "has-size" ? "has size" : "no size",
        activeClass: "bg-accent-muted text-accent-hover",
      };
  }
}

export function listDeliveryFilterValues(
  availability: FilterAvailability,
): { value: DeliveryKind; available: boolean }[] {
  const kinds: DeliveryKind[] = [...STATIC_DELIVERY];
  if (availability.delivery.other) kinds.push("other");
  return kinds.map((value) => ({
    value,
    available: availability.delivery[value] ?? false,
  }));
}

export function listCodecFilterValues(
  availability: FilterAvailability,
): { value: string; available: boolean }[] {
  const staticValues = STATIC_CODECS.map((codec) => ({
    value: codec,
    available: availability.codecs[codec] ?? false,
  }));
  const dynamicKeys = Object.keys(availability.codecs)
    .filter((codec) => !STATIC_CODECS.includes(codec as (typeof STATIC_CODECS)[number]))
    .sort();
  const dynamicValues = dynamicKeys.map((codec) => ({
    value: codec,
    available: true,
  }));
  return [...staticValues, ...dynamicValues];
}

export function deriveFilterAvailability(items: MediaItem[]): FilterAvailability {
  const sources: Record<MediaItem["source"], boolean> = {
    ytdlp: false,
    playwright: false,
  };
  const heights: Record<number, boolean> = {};
  const exts: Record<string, boolean> = {};
  const delivery: Record<DeliveryKind, boolean> = {
    dash: false,
    hls: false,
    http: false,
    other: false,
  };
  const codecs: Record<string, boolean> = {};
  const audio: Record<AudioFilter, boolean> = {
    audio: false,
    "no-audio": false,
  };
  const filesize: Record<FilesizeFilter, boolean> = {
    "has-size": false,
    "no-size": false,
  };

  for (const item of items) {
    sources[item.source] = true;
    if (item.height != null) heights[item.height] = true;
    exts[item.ext] = true;
    delivery[deriveDeliveryKind(item)] = true;
    if (item.video_codec) codecs[item.video_codec] = true;
    if (item.has_audio) audio.audio = true;
    else audio["no-audio"] = true;
    if (item.filesize != null) filesize["has-size"] = true;
    else filesize["no-size"] = true;
  }

  return { sources, heights, exts, delivery, codecs, audio, filesize };
}

export function listActiveFilterChips(state: MediaFilterState): ActiveFilterChip[] {
  const chips: ActiveFilterChip[] = [];

  for (const source of state.sources) {
    const meta = getFilterChipMeta("sources", source);
    chips.push({ group: "sources", value: source, ...meta });
  }
  for (const height of state.heights) {
    const meta = getFilterChipMeta("heights", height);
    chips.push({ group: "heights", value: height, ...meta });
  }
  for (const ext of state.exts) {
    const meta = getFilterChipMeta("exts", ext);
    chips.push({ group: "exts", value: ext, ...meta });
  }
  for (const kind of state.delivery) {
    const meta = getFilterChipMeta("delivery", kind);
    chips.push({ group: "delivery", value: kind, ...meta });
  }
  for (const codec of state.codecs) {
    const meta = getFilterChipMeta("codecs", codec);
    chips.push({ group: "codecs", value: codec, ...meta });
  }
  for (const tag of state.audio) {
    const meta = getFilterChipMeta("audio", tag);
    chips.push({ group: "audio", value: tag, ...meta });
  }
  for (const tag of state.filesize) {
    const meta = getFilterChipMeta("filesize", tag);
    chips.push({ group: "filesize", value: tag, ...meta });
  }

  return chips;
}

export function removeFilterChip(
  state: MediaFilterState,
  group: FilterGroupId,
  value: FilterValue,
): MediaFilterState {
  const next = cloneFilters(state);
  switch (group) {
    case "sources":
      next.sources.delete(value as MediaItem["source"]);
      break;
    case "heights":
      next.heights.delete(value as number);
      break;
    case "exts":
      next.exts.delete(value as string);
      break;
    case "delivery":
      next.delivery.delete(value as DeliveryKind);
      break;
    case "codecs":
      next.codecs.delete(value as string);
      break;
    case "audio":
      next.audio.delete(value as AudioFilter);
      break;
    case "filesize":
      next.filesize.delete(value as FilesizeFilter);
      break;
  }
  return next;
}

export function matchesFilters(item: MediaItem, state: MediaFilterState): boolean {
  if (state.sources.size > 0 && !state.sources.has(item.source)) {
    return false;
  }
  if (state.heights.size > 0) {
    if (item.height == null || !state.heights.has(item.height)) {
      return false;
    }
  }
  if (state.exts.size > 0 && !state.exts.has(item.ext)) {
    return false;
  }
  if (state.delivery.size > 0 && !state.delivery.has(deriveDeliveryKind(item))) {
    return false;
  }
  if (state.codecs.size > 0) {
    if (!item.video_codec || !state.codecs.has(item.video_codec)) {
      return false;
    }
  }
  if (state.audio.size > 0) {
    const audioTag: AudioFilter = item.has_audio ? "audio" : "no-audio";
    if (!state.audio.has(audioTag)) return false;
  }
  if (state.filesize.size > 0) {
    const sizeTag: FilesizeFilter = item.filesize != null ? "has-size" : "no-size";
    if (!state.filesize.has(sizeTag)) return false;
  }
  return true;
}

export function filterMediaItems(items: MediaItem[], state: MediaFilterState): MediaItem[] {
  if (!hasActiveFilters(state)) return items;
  return items.filter((item) => matchesFilters(item, state));
}

export function cloneFilters(state: MediaFilterState): MediaFilterState {
  return {
    sources: new Set(state.sources),
    heights: new Set(state.heights),
    exts: new Set(state.exts),
    delivery: new Set(state.delivery),
    codecs: new Set(state.codecs),
    audio: new Set(state.audio),
    filesize: new Set(state.filesize),
  };
}
