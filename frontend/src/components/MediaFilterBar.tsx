import { type ReactNode } from "react";
import { MediaItem } from "../api/client";
import {
  cloneFilters,
  deriveFilterAvailability,
  emptyFilters,
  FILTER_GROUPS,
  getFilterChipMeta,
  hasActiveFilters,
  listCodecFilterValues,
  listDeliveryFilterValues,
  MediaFilterState,
  STATIC_AUDIO,
  STATIC_FILESIZE,
  STATIC_SOURCES,
  type AudioFilter,
  type DeliveryKind,
  type FilesizeFilter,
  type FilterGroupId,
  type FilterValue,
} from "../utils/mediaFilters";
import { btnSecondaryClass, filterChipClass } from "./ui";

interface Props {
  items: MediaItem[];
  filters: MediaFilterState;
  onChange: (filters: MediaFilterState) => void;
  variant?: "inline" | "modal";
  onDone?: () => void;
}

function toggleInSet<T>(set: Set<T>, value: T): Set<T> {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

function FilterGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="w-full text-[0.65rem] font-semibold uppercase tracking-wide text-muted sm:w-auto sm:shrink-0">
        {label}
      </span>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function Chip({
  label,
  active,
  activeClass,
  disabled,
  onToggle,
}: {
  label: string;
  active: boolean;
  activeClass: string;
  disabled?: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      disabled={disabled}
      title={disabled ? "Not in current scan" : undefined}
      className={`${filterChipClass(active, activeClass)} ${
        disabled ? "cursor-not-allowed opacity-40 hover:bg-transparent hover:text-muted" : ""
      }`}
      onClick={onToggle}
    >
      {label}
    </button>
  );
}

function getValuesForGroup(
  groupId: FilterGroupId,
  availability: ReturnType<typeof deriveFilterAvailability>,
): { value: FilterValue; available: boolean }[] {
  switch (groupId) {
    case "sources":
      return STATIC_SOURCES.map((value) => ({
        value,
        available: availability.sources[value],
      }));
    case "heights":
      return Object.keys(availability.heights)
        .map(Number)
        .sort((a, b) => b - a)
        .map((value) => ({
          value,
          available: availability.heights[value] ?? false,
        }));
    case "exts":
      return Object.keys(availability.exts)
        .sort()
        .map((value) => ({
          value,
          available: availability.exts[value] ?? false,
        }));
    case "delivery":
      return listDeliveryFilterValues(availability);
    case "codecs":
      return listCodecFilterValues(availability);
    case "audio":
      return STATIC_AUDIO.map((value) => ({
        value,
        available: availability.audio[value],
      }));
    case "filesize":
      return STATIC_FILESIZE.map((value) => ({
        value,
        available: availability.filesize[value],
      }));
  }
}

function isActive(filters: MediaFilterState, groupId: FilterGroupId, value: FilterValue): boolean {
  switch (groupId) {
    case "sources":
      return filters.sources.has(value as MediaItem["source"]);
    case "heights":
      return filters.heights.has(value as number);
    case "exts":
      return filters.exts.has(value as string);
    case "delivery":
      return filters.delivery.has(value as DeliveryKind);
    case "codecs":
      return filters.codecs.has(value as string);
    case "audio":
      return filters.audio.has(value as AudioFilter);
    case "filesize":
      return filters.filesize.has(value as FilesizeFilter);
  }
}

export function MediaFilterBar({ items, filters, onChange, variant = "inline", onDone }: Props) {
  const availability = deriveFilterAvailability(items);

  const update = (patch: Partial<MediaFilterState>) => {
    onChange({ ...cloneFilters(filters), ...patch });
  };

  const toggle = (groupId: FilterGroupId, value: FilterValue) => {
    switch (groupId) {
      case "sources":
        update({
          sources: toggleInSet(filters.sources, value as MediaItem["source"]),
        });
        break;
      case "heights":
        update({ heights: toggleInSet(filters.heights, value as number) });
        break;
      case "exts":
        update({ exts: toggleInSet(filters.exts, value as string) });
        break;
      case "delivery":
        update({
          delivery: toggleInSet(filters.delivery, value as DeliveryKind),
        });
        break;
      case "codecs":
        update({ codecs: toggleInSet(filters.codecs, value as string) });
        break;
      case "audio":
        update({ audio: toggleInSet(filters.audio, value as AudioFilter) });
        break;
      case "filesize":
        update({
          filesize: toggleInSet(filters.filesize, value as FilesizeFilter),
        });
        break;
    }
  };

  const visibleGroups = FILTER_GROUPS.filter((group) => {
    if (!group.dynamic) return true;
    const values = getValuesForGroup(group.id, availability);
    return values.length > 0;
  });

  if (visibleGroups.length === 0) return null;

  const rootClass = variant === "modal" ? "flex flex-col gap-4" : "mb-4 flex flex-col gap-3";

  return (
    <div className={rootClass}>
      <div className="flex flex-col gap-3">
        {visibleGroups.map((group) => {
          const values = getValuesForGroup(group.id, availability);
          return (
            <FilterGroup key={group.id} label={group.label}>
              {values.map(({ value, available }) => {
                const { label, activeClass } = getFilterChipMeta(group.id, value);
                return (
                  <Chip
                    key={`${group.id}-${String(value)}`}
                    label={label}
                    active={isActive(filters, group.id, value)}
                    activeClass={activeClass}
                    disabled={!available}
                    onToggle={() => toggle(group.id, value)}
                  />
                );
              })}
            </FilterGroup>
          );
        })}
      </div>
      <div
        className={`flex flex-wrap items-center gap-2 ${
          variant === "modal" ? "justify-end border-t border-border pt-4" : ""
        }`}
      >
        {hasActiveFilters(filters) && (
          <button
            type="button"
            className="text-xs font-semibold text-accent hover:text-accent-hover"
            onClick={() => onChange(emptyFilters())}
          >
            Clear all
          </button>
        )}
        {variant === "modal" && onDone && (
          <button type="button" className={btnSecondaryClass} onClick={onDone}>
            Done
          </button>
        )}
      </div>
    </div>
  );
}
