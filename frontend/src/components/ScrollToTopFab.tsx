import { type RefObject } from "react";
import { useIntersectionVisibility } from "../hooks/useIntersectionVisibility";
import { MIN_ITEMS_FOR_FAB } from "../utils/format";
import { ScrollFab } from "./ScrollFab";

interface Props {
  scrollTargetRef: RefObject<HTMLElement | null>;
  visibilityRef: RefObject<HTMLElement | null>;
  itemCount: number;
}

export function ScrollToTopFab({ scrollTargetRef, visibilityRef, itemCount }: Props) {
  const mounted = itemCount > 0;
  const active = itemCount >= MIN_ITEMS_FOR_FAB;
  const visible = useIntersectionVisibility(visibilityRef, {
    enabled: active,
    rootMargin: "-40px 0px 0px 0px",
  });

  return (
    <ScrollFab
      direction="up"
      targetRef={scrollTargetRef}
      visible={visible}
      mounted={mounted}
      ariaLabel="Scroll to top"
      positionClass="top-20 right-6"
    />
  );
}
