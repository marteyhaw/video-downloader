import { describe, expect, it } from "vitest";
import type { MediaItem } from "../api/client";
import { deriveDeliveryKind, emptyFilters, matchesFilters } from "./mediaFilters";

function item(partial: Partial<MediaItem> & Pick<MediaItem, "id">): MediaItem {
  return {
    title: "Test",
    url: "https://example.com/video.mp4",
    manifest_url: null,
    ext: "mp4",
    height: 240,
    width: 426,
    has_audio: true,
    source: "ytdlp",
    format_id: null,
    thumbnail: null,
    filesize: null,
    video_codec: "H.264",
    bandwidth: null,
    ...partial,
  };
}

describe("deriveDeliveryKind", () => {
  it("classifies yt-dlp format_id prefixes", () => {
    expect(deriveDeliveryKind(item({ id: "1", format_id: "dash-video-332" }))).toBe("dash");
    expect(deriveDeliveryKind(item({ id: "2", format_id: "hls-399-0" }))).toBe("hls");
    expect(deriveDeliveryKind(item({ id: "3", format_id: "hls-399-1" }))).toBe("hls");
    expect(deriveDeliveryKind(item({ id: "4", format_id: "http-240p" }))).toBe("http");
  });

  it("classifies playwright network captures", () => {
    expect(
      deriveDeliveryKind(
        item({
          id: "pw1",
          source: "playwright",
          ext: "m3u8",
          url: "https://cdn.example.com/master.m3u8",
          manifest_url: "https://cdn.example.com/master.m3u8",
        }),
      ),
    ).toBe("hls");
    expect(
      deriveDeliveryKind(
        item({
          id: "pw2",
          source: "playwright",
          ext: "mp4",
          url: "https://cdn.example.com/video.mp4",
        }),
      ),
    ).toBe("http");
  });

  it("classifies manifest and mpd URLs", () => {
    expect(
      deriveDeliveryKind(
        item({
          id: "m1",
          format_id: "99",
          manifest_url: "https://cdn.example.com/index.m3u8",
        }),
      ),
    ).toBe("hls");
    expect(
      deriveDeliveryKind(
        item({
          id: "m2",
          format_id: "100",
          url: "https://cdn.example.com/stream.mpd",
        }),
      ),
    ).toBe("dash");
  });
});

describe("matchesFilters delivery", () => {
  const dash = item({ id: "d", format_id: "dash-video-332" });
  const hls = item({ id: "h", format_id: "hls-399-0" });
  const http = item({ id: "p", format_id: "http-240p" });

  it("filters by delivery kind", () => {
    const state = emptyFilters();
    state.delivery.add("http");
    expect(matchesFilters(dash, state)).toBe(false);
    expect(matchesFilters(hls, state)).toBe(false);
    expect(matchesFilters(http, state)).toBe(true);
  });
});
