import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchHistory,
  getJob,
  startDownload,
  type MediaItem,
  type StartDownloadBody,
} from "../api/client";
import { maxHistoryId } from "../utils/historyReadState";
import { basenameFromPath } from "../utils/format";
import { useToasts, type PushToastInput } from "./useToasts";

export interface DownloadJobState {
  activeJobId: string | null;
  jobProgress: number;
  jobStage: string;
  jobError: string | null;
  downloading: boolean;
  handleDownload: (
    selected: MediaItem,
    opts: { container: string; includeAudio: boolean; filename: string },
    pageUrl: string,
  ) => void;
  toasts: ReturnType<typeof useToasts>["toasts"];
  pushToast: (input: PushToastInput) => void;
  dismissToast: (id: string) => void;
}

export function useDownloadJob(onHistoryUpdate: (maxId: number) => void): DownloadJobState {
  const queryClient = useQueryClient();
  const { toasts, pushToast, dismissToast } = useToasts();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobStage, setJobStage] = useState("");
  const [jobError, setJobError] = useState<string | null>(null);
  const lastFilenameRef = useRef("");

  const downloadMutation = useMutation({
    mutationFn: startDownload,
    onSuccess: (job) => {
      setActiveJobId(job.id);
      setJobError(null);
      setJobProgress(job.progress);
      setJobStage(job.stage);
    },
    onError: (error) => {
      setJobError((error as Error).message);
      pushToast({
        variant: "error",
        title: "Download failed",
        description: (error as Error).message,
      });
    },
  });

  const pollJob = useCallback(
    async (jobId: string) => {
      const job = await getJob(jobId);
      setJobProgress(job.progress);
      setJobStage(job.stage);

      if (job.state === "done") {
        setActiveJobId(null);
        setJobError(null);
        const entries = await queryClient.fetchQuery({
          queryKey: ["history"],
          queryFn: fetchHistory,
        });
        const maxId = maxHistoryId(entries);
        const description =
          (job.output_path ? basenameFromPath(job.output_path) : lastFilenameRef.current) ||
          undefined;

        pushToast({
          variant: "success",
          title: "Download complete",
          description,
          historyId: maxId > 0 ? maxId : undefined,
        });
        onHistoryUpdate(maxId);
        return true;
      }

      if (job.state === "error") {
        const message = job.error || "Download failed";
        setJobError(message);
        setActiveJobId(null);
        pushToast({
          variant: "error",
          title: "Download failed",
          description: job.error ?? undefined,
        });
        return true;
      }

      return false;
    },
    [queryClient, pushToast, onHistoryUpdate],
  );

  useEffect(() => {
    if (!activeJobId) return;
    let polling = false;
    const interval = setInterval(async () => {
      if (polling) return;
      polling = true;
      try {
        const done = await pollJob(activeJobId);
        if (done) clearInterval(interval);
      } finally {
        polling = false;
      }
    }, 800);
    return () => clearInterval(interval);
  }, [activeJobId, pollJob]);

  const handleDownload = useCallback(
    (
      selected: MediaItem,
      opts: { container: string; includeAudio: boolean; filename: string },
      pageUrl: string,
    ) => {
      lastFilenameRef.current = opts.filename;
      const body: StartDownloadBody = {
        item_id: selected.id,
        title: selected.title,
        url: selected.url,
        manifest_url: selected.manifest_url,
        ext: selected.ext,
        source: selected.source,
        format_id: selected.format_id,
        include_audio: opts.includeAudio,
        container: opts.container,
        page_url: pageUrl,
        webpage_url: selected.webpage_url ?? undefined,
        filename: opts.filename,
      };
      downloadMutation.mutate(body);
    },
    [downloadMutation],
  );

  return {
    activeJobId,
    jobProgress,
    jobStage,
    jobError,
    downloading: downloadMutation.isPending || !!activeJobId,
    handleDownload,
    toasts,
    pushToast,
    dismissToast,
  };
}
