import { ChevronDown } from "lucide-react";
import type { SelectHTMLAttributes } from "react";
import { selectClass, selectClassCompact } from "./ui";

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  compact?: boolean;
  wrapperClassName?: string;
}

export function SelectField({ compact = false, wrapperClassName, className, ...props }: Props) {
  const selectCn = compact ? selectClassCompact : selectClass;
  return (
    <div className={wrapperClassName ? `relative ${wrapperClassName}` : "relative"}>
      <select {...props} className={className ? `${selectCn} ${className}` : selectCn} />
      <ChevronDown
        size={16}
        className="pointer-events-none absolute top-1/2 right-2.5 -translate-y-1/2 text-muted"
        aria-hidden
      />
    </div>
  );
}
