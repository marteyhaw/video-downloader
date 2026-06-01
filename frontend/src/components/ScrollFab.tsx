import { ChevronDown, ChevronUp } from "lucide-react";
import { type RefObject } from "react";

interface Props {
  direction: "up" | "down";
  targetRef: RefObject<HTMLElement | null>;
  visible: boolean;
  mounted: boolean;
  ariaLabel: string;
  positionClass: string;
}

export function ScrollFab({
  direction,
  targetRef,
  visible,
  mounted,
  ariaLabel,
  positionClass,
}: Props) {
  const scrollToTarget = () => {
    targetRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const Icon = direction === "up" ? ChevronUp : ChevronDown;

  if (!mounted) return null;

  return (
    <button
      type="button"
      aria-label={ariaLabel}
      aria-hidden={!visible}
      tabIndex={visible ? 0 : -1}
      onClick={scrollToTarget}
      className={`scroll-fab fixed z-40 flex size-11 items-center justify-center rounded-full border border-border bg-surface text-foreground shadow-lg hover:bg-surface-hover ${positionClass} ${
        visible
          ? "translate-y-0 opacity-100"
          : direction === "up"
            ? "pointer-events-none -translate-y-2 opacity-0"
            : "pointer-events-none translate-y-2 opacity-0"
      }`}
    >
      <Icon size={22} aria-hidden />
    </button>
  );
}
