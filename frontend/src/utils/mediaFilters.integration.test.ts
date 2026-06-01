import { describe, expect, it } from "vitest";
import type { MediaItem } from "../api/client";
import {
  cloneFilters,
  countActiveFilters,
  emptyFilters,
  filterMediaItems,
  hasActiveFilters,
  listActiveFilterChips,
  matchesFilters,
  removeFilterChip,
} from "./mediaFilters";

const makeItem = (overrides: Partial<MediaItem> = {}): MediaItem => ({
  id: "test-1",
  title: "Test Video",
  url: "https://example.com/video.mp4",
  manifest_url: null,
  ext: "mp4",
  height: 720,
  width: 1280,
  has_audio: true,
  source: "ytdlp",
  format_id: "http-720",
  thumbnail: null,
  filesize: 1_000_000,
  video_codec: "H.264",
  bandwidth: null,
  ...overrides,
});

describe("filter toggle workflow", () => {
  it("filters by source", () => {
    const items = [
      makeItem({ id: "a", source: "ytdlp" }),
      makeItem({ id: "b", source: "playwright" }),
    ];
    const filters = emptyFilters();
    filters.sources.add("ytdlp");
    const result = filterMediaItems(items, filters);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("a");
  });

  it("filters by height", () => {
    const items = [makeItem({ id: "a", height: 720 }), makeItem({ id: "b", height: 1080 })];
    const filters = emptyFilters();
    filters.heights.add(1080);
    const result = filterMediaItems(items, filters);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("b");
  });

  it("clears filters returns all items", () => {
    const items = [makeItem({ id: "a" }), makeItem({ id: "b" })];
    expect(filterMediaItems(items, emptyFilters())).toHaveLength(2);
  });
});

describe("chip management", () => {
  it("lists active chips", () => {
    const filters = emptyFilters();
    filters.sources.add("ytdlp");
    filters.heights.add(1080);
    const chips = listActiveFilterChips(filters);
    expect(chips).toHaveLength(2);
  });

  it("removes a chip", () => {
    const filters = emptyFilters();
    filters.sources.add("ytdlp");
    filters.sources.add("playwright");
    const updated = removeFilterChip(filters, "sources", "ytdlp");
    expect(updated.sources.size).toBe(1);
    expect(updated.sources.has("playwright")).toBe(true);
  });
});

describe("clone and count", () => {
  it("clones are independent", () => {
    const original = emptyFilters();
    original.sources.add("ytdlp");
    const clone = cloneFilters(original);
    clone.sources.add("playwright");
    expect(original.sources.size).toBe(1);
    expect(clone.sources.size).toBe(2);
  });

  it("counts active filters", () => {
    const filters = emptyFilters();
    expect(countActiveFilters(filters)).toBe(0);
    filters.exts.add("mp4");
    filters.audio.add("audio");
    expect(countActiveFilters(filters)).toBe(2);
    expect(hasActiveFilters(filters)).toBe(true);
  });
});

describe("matchesFilters edge cases", () => {
  it("audio filter works with no-audio items", () => {
    const item = makeItem({ has_audio: false });
    const filters = emptyFilters();
    filters.audio.add("no-audio");
    expect(matchesFilters(item, filters)).toBe(true);
  });

  it("filesize filter distinguishes present vs absent", () => {
    const withSize = makeItem({ filesize: 100 });
    const noSize = makeItem({ filesize: null });
    const filters = emptyFilters();
    filters.filesize.add("has-size");
    expect(matchesFilters(withSize, filters)).toBe(true);
    expect(matchesFilters(noSize, filters)).toBe(false);
  });
});
