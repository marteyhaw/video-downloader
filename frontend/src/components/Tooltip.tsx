import { autoUpdate, flip, offset, shift, useFloating, type Placement } from "@floating-ui/react";
import { useId, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

interface Props {
  text: string;
  children: ReactNode;
  className?: string;
  variant?: "text" | "floating";
  placement?: Placement;
}

export function Tooltip({
  text,
  children,
  className = "",
  variant = "text",
  placement = "top",
}: Props) {
  if (!text) {
    return <>{children}</>;
  }

  if (variant === "text") {
    return (
      <span className={`tooltip-wrap ${className}`.trim()} data-tooltip={text}>
        {children}
      </span>
    );
  }

  return (
    <FloatingTooltip text={text} className={className} placement={placement}>
      {children}
    </FloatingTooltip>
  );
}

function FloatingTooltip({
  text,
  children,
  className,
  placement,
}: {
  text: string;
  children: ReactNode;
  className: string;
  placement: Placement;
}) {
  const [open, setOpen] = useState(false);
  const tooltipId = useId();

  const { refs, floatingStyles } = useFloating({
    open,
    onOpenChange: setOpen,
    placement,
    whileElementsMounted: autoUpdate,
    middleware: [offset(6), flip(), shift({ padding: 8 })],
  });

  return (
    <>
      <span
        ref={refs.setReference}
        className={`inline-flex shrink-0 ${className}`.trim()}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocusCapture={() => setOpen(true)}
        onBlurCapture={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
            setOpen(false);
          }
        }}
        aria-describedby={open ? tooltipId : undefined}
      >
        {children}
      </span>
      {open &&
        createPortal(
          <div
            ref={refs.setFloating}
            id={tooltipId}
            role="tooltip"
            style={floatingStyles}
            className="z-[200] max-w-[min(90vw,20rem)] whitespace-nowrap rounded-md border border-border bg-surface-hover px-2.5 py-1.5 text-xs font-normal leading-normal text-foreground shadow-lg"
          >
            {text}
          </div>,
          document.body,
        )}
    </>
  );
}
