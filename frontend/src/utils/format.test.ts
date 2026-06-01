import { describe, expect, it } from "vitest";
import { basenameFromPath, formatSize, MIN_ITEMS_FOR_FAB } from "./format";

describe("basenameFromPath", () => {
  it("extracts filename from unix path", () => {
    expect(basenameFromPath("/home/user/video.mp4")).toBe("video.mp4");
  });

  it("extracts filename from windows path", () => {
    expect(basenameFromPath("C:\\Users\\user\\video.mp4")).toBe("video.mp4");
  });

  it("returns path if no separator", () => {
    expect(basenameFromPath("video.mp4")).toBe("video.mp4");
  });

  it("handles trailing separator by returning full path", () => {
    expect(basenameFromPath("/home/user/")).toBe("/home/user/");
  });
});

describe("formatSize", () => {
  it("returns dash for null", () => {
    expect(formatSize(null)).toBe("—");
  });

  it("returns dash for zero", () => {
    expect(formatSize(0)).toBe("—");
  });

  it("formats KB", () => {
    expect(formatSize(512 * 1024)).toBe("512.0 KB");
  });

  it("formats MB", () => {
    expect(formatSize(5 * 1024 * 1024)).toBe("5.0 MB");
  });
});

describe("MIN_ITEMS_FOR_FAB", () => {
  it("is a positive number", () => {
    expect(MIN_ITEMS_FOR_FAB).toBeGreaterThan(0);
  });
});
