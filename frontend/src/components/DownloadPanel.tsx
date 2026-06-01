import type { useDownloadJob } from "../hooks/useDownloadJob";
import type { useScan } from "../hooks/useScan";
import { DownloadOptions } from "./DownloadOptions";
import { FoundMediaSection } from "./FoundMediaSection";
import { ScanProgressPanel } from "./ScanProgressPanel";
import { ScrollToDownloadFab } from "./ScrollToDownloadFab";
import { ScrollToTopFab } from "./ScrollToTopFab";
import { Tooltip } from "./Tooltip";
import { btnPrimaryClass, btnStopClass, inputClass, sectionClass, sectionTitleClass } from "./ui";

type ScanState = ReturnType<typeof useScan>;
type DownloadState = ReturnType<typeof useDownloadJob>;

interface DownloadPanelProps {
  scan: ScanState;
  download: DownloadState;
  onDownload: (opts: { container: string; includeAudio: boolean; filename: string }) => void;
  pageTopRef: React.RefObject<HTMLDivElement>;
  scanSectionRef: React.RefObject<HTMLElement>;
  downloadSectionRef: React.RefObject<HTMLElement>;
}

export function DownloadPanel({
  scan,
  download,
  onDownload,
  pageTopRef,
  scanSectionRef,
  downloadSectionRef,
}: DownloadPanelProps) {
  return (
    <div role="tabpanel" id="panel-download" aria-labelledby="tab-download">
      <section ref={scanSectionRef} className={sectionClass}>
        <h2 className={sectionTitleClass}>Scan</h2>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            type="url"
            aria-label="Page URL to scan"
            className={inputClass}
            placeholder="https://example.com/video-page"
            value={scan.url}
            onChange={(e) => scan.setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && scan.handleScan()}
          />
          <button
            type="button"
            className={scan.pending ? btnStopClass : btnPrimaryClass}
            onClick={scan.pending ? scan.handleStop : scan.handleScan}
            aria-busy={scan.pending}
          >
            {scan.pending ? "Stop" : "Scan"}
          </button>
        </div>
        <ScanProgressPanel events={scan.progress} active={scan.pending} stopped={scan.stopped} />
        {scan.pageTitle && !scan.pending && (
          <Tooltip text={scan.pageTitle} className="mt-3 block max-w-full">
            <p className="my-1 text-sm text-muted">Page:</p>
            <p className="tooltip-text m-0 text-lg font-semibold text-foreground">
              {scan.pageTitle}
            </p>
          </Tooltip>
        )}
        {scan.warning && (
          <div className="mt-3 rounded-md border border-warn-border bg-warn/10 px-4 py-3 text-sm text-warn">
            {scan.warning}
          </div>
        )}
      </section>

      {scan.items.length > 0 && (
        <FoundMediaSection
          items={scan.items}
          selected={scan.selected}
          onSelect={scan.setSelected}
          filters={scan.mediaFilters}
          onFiltersChange={scan.setMediaFilters}
        />
      )}

      {scan.selected && (
        <section ref={downloadSectionRef} id="download-options" className={sectionClass}>
          <h2 className={sectionTitleClass}>Download options</h2>
          <DownloadOptions
            item={scan.selected}
            onDownload={onDownload}
            downloading={download.downloading}
          />
          {download.activeJobId && (
            <>
              <div className="mt-3 h-1.5 overflow-hidden rounded-sm bg-background">
                <div
                  className="h-full bg-accent transition-[width] duration-300"
                  style={{ width: `${Math.round(download.jobProgress * 100)}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-muted">{download.jobStage || "Working…"}</p>
            </>
          )}
        </section>
      )}

      <ScrollToTopFab
        scrollTargetRef={pageTopRef}
        visibilityRef={scanSectionRef}
        itemCount={scan.items.length}
      />
      <ScrollToDownloadFab
        targetRef={downloadSectionRef}
        enabled={scan.selected != null}
        itemCount={scan.items.length}
      />
    </div>
  );
}
