import { describe, it, expect, vi, beforeEach } from "vitest";

describe("api client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("should export required API functions", async () => {
    const client = await import("./client");
    expect(client.fetchHealth).toBeDefined();
    expect(client.fetchHistory).toBeDefined();
    expect(client.startDownload).toBeDefined();
    expect(client.getJob).toBeDefined();
    expect(client.scanUrlStream).toBeDefined();
    expect(client.renameHistory).toBeDefined();
    expect(client.revealInFolder).toBeDefined();
    expect(client.deleteHistory).toBeDefined();
  });

  it("should throw on non-ok response", async () => {
    const client = await import("./client");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Bad request" }),
      }),
    );
    await expect(client.fetchHealth()).rejects.toThrow();
  });

  it("scanUrlStream aborts: closes EventSource and rejects with AbortError", async () => {
    const closeSpy = vi.fn();
    class FakeEventSource {
      onmessage: ((e: { data: string }) => void) | null = null;
      onerror: (() => void) | null = null;
      readonly url: string;
      constructor(url: string) {
        this.url = url;
      }
      close = closeSpy;
    }
    vi.stubGlobal("EventSource", FakeEventSource);

    const client = await import("./client");
    const controller = new AbortController();
    const promise = client.scanUrlStream("https://example.com", () => {}, controller.signal);

    controller.abort();

    await expect(promise).rejects.toMatchObject({ name: "AbortError" });
    expect(closeSpy).toHaveBeenCalledTimes(1);
  });
});
