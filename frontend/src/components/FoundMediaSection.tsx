import { useCallback, useEffect, useMemo, useState } from "react";
import { MediaItem } from "../api/client";
import { useAnimatedList } from "../hooks/useAnimatedList";
import {
  emptyFilters,
  filterMediaItems,
  hasActiveFilters,
  MediaFilterState,
} from "../utils/mediaFilters";
import { MediaCard } from "./MediaCard";
import { MediaFilterModal } from "./MediaFilterModal";
import { MediaFilterChipRow, MediaFilterSummary } from "./MediaFilterSummary";
import { sectionClass } from "./ui";

interface Props {
  items: MediaItem[];
  selected: MediaItem | null;
  onSelect: (item: MediaItem | null) => void;
  filters: MediaFilterState;
  onFiltersChange: (filters: MediaFilterState) => void;
}

export function FoundMediaSection({ items, selected, onSelect, filters, onFiltersChange }: Props) {
  const [filterModalOpen, setFilterModalOpen] = useState(false);
  const itemsKey = items.map((i) => i.id).join(",");
  // auto-animate only observes direct children: outer = chip row, inner = cards
  const layoutRef = useAnimatedList(itemsKey);
  const listRef = useAnimatedList(itemsKey);

  const handleSelect = useCallback((item: MediaItem) => onSelect(item), [onSelect]);

  const filtered = useMemo(() => filterMediaItems(items, filters), [items, filters]);

  useEffect(() => {
    if (!selected) return;
    if (filtered.some((item) => item.id === selected.id)) return;
    onSelect(filtered[0] ?? null);
  }, [filtered, selected, onSelect]);

  const title =
    hasActiveFilters(filters) && filtered.length !== items.length
      ? `Found media (${filtered.length} of ${items.length})`
      : `Found media (${items.length})`;

  return (
    <section className={sectionClass}>
      <MediaFilterSummary
        title={title}
        filters={filters}
        onOpenModal={() => setFilterModalOpen(true)}
      />
      <MediaFilterModal
        open={filterModalOpen}
        items={items}
        filters={filters}
        onChange={onFiltersChange}
        onClose={() => setFilterModalOpen(false)}
      />
      <div ref={layoutRef} className="flex flex-col gap-2">
        <MediaFilterChipRow filters={filters} onChange={onFiltersChange} />
        <div ref={listRef} className="flex flex-col">
          {filtered.length === 0 ? (
            <div key="empty" className="py-6 text-center text-sm text-muted">
              <p className="m-0">No items match the current filters.</p>
              <button
                type="button"
                className="mt-2 text-xs font-semibold text-accent hover:text-accent-hover"
                onClick={() => onFiltersChange(emptyFilters())}
              >
                Clear filters
              </button>
            </div>
          ) : (
            filtered.map((item, index) => (
              <div key={item.id} className={index > 0 ? "mt-2.5" : undefined}>
                <MediaCard
                  item={item}
                  selected={selected?.id === item.id}
                  onSelect={handleSelect}
                />
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
