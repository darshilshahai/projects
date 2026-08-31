import React from 'react';
import { SORT_OPTIONS } from '../../constants';
import { Search, Filter, Star, Clock, X } from 'lucide-react';

export default function FilterBar({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  isFavouriteOnly,
  onToggleFavouriteOnly,
  isWatchLaterOnly,
  onToggleWatchLaterOnly,
  sortBy,
  order,
  onSortChange,
  onResetFilters,
}) {
  const hasActiveFilters =
    searchQuery ||
    statusFilter !== 'all' ||
    isFavouriteOnly ||
    isWatchLaterOnly ||
    sortBy !== 'added_at' ||
    order !== 'desc';

  return (
    <div className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl p-4 shadow-md space-y-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search titles, channels, notes..."
            className="w-full pl-10 pr-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all"
          />
        </div>

        {/* Sort Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-[hsl(var(--text-secondary))] shrink-0">
            Sort by:
          </span>
          <select
            value={`${sortBy}:${order}`}
            onChange={(e) => {
              const [sBy, ord] = e.target.value.split(':');
              onSortChange(sBy, ord);
            }}
            className="bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl px-3 py-2 text-xs font-medium text-[hsl(var(--text-primary))] focus:outline-none focus:border-[hsl(var(--border-focus))]"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={`${opt.value}:${opt.order}`} value={`${opt.value}:${opt.order}`}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Filter Quick Pills */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[hsl(var(--border-muted))/0.5]">
        <div className="flex flex-wrap items-center gap-2">
          {/* Status Pills */}
          {['all', 'unwatched', 'watching', 'watched'].map((st) => (
            <button
              key={st}
              onClick={() => onStatusChange(st)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg capitalize transition-all ${
                statusFilter === st
                  ? 'bg-[hsl(var(--primary))] text-slate-950 shadow-sm'
                  : 'bg-[hsl(var(--bg-input))] text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] border border-[hsl(var(--border-muted))/0.5]'
              }`}
            >
              {st}
            </button>
          ))}

          <div className="h-4 w-px bg-[hsl(var(--border-muted))] mx-1 hidden sm:block" />

          {/* Favourites Toggle */}
          <button
            onClick={onToggleFavouriteOnly}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              isFavouriteOnly
                ? 'bg-[hsl(var(--favourite))] text-slate-950 shadow-sm'
                : 'bg-[hsl(var(--bg-input))] text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] border border-[hsl(var(--border-muted))/0.5]'
            }`}
          >
            <Star className={`w-3.5 h-3.5 ${isFavouriteOnly ? 'fill-slate-950' : ''}`} />
            <span>Favourites</span>
          </button>

          {/* Watch Later Toggle */}
          <button
            onClick={onToggleWatchLaterOnly}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              isWatchLaterOnly
                ? 'bg-[hsl(var(--watch-later))] text-white shadow-sm'
                : 'bg-[hsl(var(--bg-input))] text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] border border-[hsl(var(--border-muted))/0.5]'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Watch Later</span>
          </button>
        </div>

        {/* Clear Filters CTA */}
        {hasActiveFilters && (
          <button
            onClick={onResetFilters}
            className="flex items-center gap-1 px-2.5 py-1 text-xs text-red-400 hover:text-red-300 transition-colors ml-auto"
          >
            <X className="w-3.5 h-3.5" />
            <span>Clear Filters</span>
          </button>
        )}
      </div>
    </div>
  );
}
