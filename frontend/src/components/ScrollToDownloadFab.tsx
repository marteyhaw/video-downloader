import { type RefObject } from "react";
import { useIntersectionVisibility } from "../hooks/useIntersectionVisibility";
import { MIN_ITEMS_FOR_FAB } from "../utils/format";
import { ScrollFab } from "./ScrollFab";

interface Props {
  targetRef: RefObject<HTMLElement | null>;
  enabled: boolean;
  itemCount: number;
}

export function ScrollToDownloadFab({ targetRef, enabled, itemCount }: Props) {
  const mounted = itemCount > 0;
  const active = enabled && itemCount >= MIN_ITEMS_FOR_FAB;
  const visible = useIntersectionVisibility(targetRef, {
    enabled: active,
    rootMargin: "0px 0px -40px 0px",
  });

  return (
    <ScrollFab
      direction="down"
      targetRef={targetRef}
      visible={visible}
      mounted={mounted}
      ariaLabel="Scroll to download options"
      positionClass="bottom-6 right-6"
    />
  );
}
