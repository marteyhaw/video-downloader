import { SlidersHorizontal, X } from "lucide-react";
import {
  countActiveFilters,
  emptyFilters,
  hasActiveFilters,
  listActiveFilterChips,
  MediaFilterState,
  removeFilterChip,
} from "../utils/mediaFilters";
import { btnSecondaryClass, filterChipClass, sectionTitleClass } from "./ui";

interface SummaryProps {
  title: string;
  filters: MediaFilterState;
  onOpenModal: () => void;
}

export function MediaFilterSummary({ title, filters, onOpenModal }: SummaryProps) {
  const activeCount = countActiveFilters(filters);

  return (
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
      <h2 className={`${sectionTitleClass} mb-0`}>{title}</h2>
      <button
        type="button"
        className={`${btnSecondaryClass} inline-flex shrink-0 items-center gap-2`}
        onClick={onOpenModal}
      >
        <SlidersHorizontal size={16} aria-hidden />
        Filters
        {activeCount > 0 && (
          <span className="rounded-full bg-accent px-1.5 py-0.5 text-[0.65rem] font-bold text-white">
            {activeCount}
          </span>
        )}
      </button>
    </div>
  );
}

interface ChipRowProps {
  filters: MediaFilterState;
  onChange: (filters: MediaFilterState) => void;
}

export function MediaFilterChipRow({ filters, onChange }: ChipRowProps) {
  const chips = listActiveFilterChips(filters);

  if (chips.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 mb-2">
      {chips.map((chip) => (
        <span
          key={`${chip.group}-${String(chip.value)}`}
          className={`filter-chip-enter inline-flex items-center gap-1 ${filterChipClass(true, chip.activeClass)}`}
        >
          {chip.label}
          <button
            type="button"
            className="rounded p-0.5 opacity-70 hover:opacity-100"
            aria-label={`Remove ${chip.label} filter`}
            onClick={() => onChange(removeFilterChip(filters, chip.group, chip.value))}
          >
            <X size={12} aria-hidden />
          </button>
        </span>
      ))}
      {hasActiveFilters(filters) && (
        <button
          type="button"
          className="text-xs font-semibold text-accent hover:text-accent-hover"
          onClick={() => onChange(emptyFilters())}
        >
          Clear all
        </button>
      )}
    </div>
  );
}
