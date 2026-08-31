import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { getVideosApi, updateVideoApi } from '../api/videos.api';
import FilterBar from '../components/video/FilterBar';
import VideoCard from '../components/video/VideoCard';
import VideoCardSkeleton from '../components/video/VideoCardSkeleton';
import { ChevronLeft, ChevronRight, Library, Plus } from 'lucide-react';

export default function LibraryPage({ onOpenAddModal }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();

  // Search & Filter State
  const initialQuery = searchParams.get('q') || '';
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);

  const [statusFilter, setStatusFilter] = useState('all');
  const [isFavouriteOnly, setIsFavouriteOnly] = useState(false);
  const [isWatchLaterOnly, setIsWatchLaterOnly] = useState(false);

  const [sortBy, setSortBy] = useState('added_at');
  const [order, setOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const pageSize = 12;

  // Sync searchQuery from URL params if updated by Header
  useEffect(() => {
    const q = searchParams.get('q') || '';
    setSearchQuery(q);
    setDebouncedQuery(q);
  }, [searchParams]);

  // Debounce search query changes by 350ms
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(searchQuery);
      setPage(1);
    }, 350);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  // Query Params Payload
  const queryParams = {
    page,
    size: pageSize,
    sort_by: sortBy,
    order,
    ...(debouncedQuery.trim() && { q: debouncedQuery.trim() }),
    ...(statusFilter !== 'all' && { status: statusFilter }),
    ...(isFavouriteOnly && { is_favourite: true }),
    ...(isWatchLaterOnly && { is_watch_later: true }),
  };

  // Fetch Library Videos with TanStack Query
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['videos', queryParams],
    queryFn: () => getVideosApi(queryParams),
    keepPreviousData: true,
  });

  // Mutation for Video Toggles
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateVideoApi(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['quickQueue'] });
    },
  });

  const handleToggleFavourite = (uv) => {
    updateMutation.mutate({
      id: uv.id,
      data: { is_favourite: !uv.is_favourite },
    });
  };

  const handleToggleWatchLater = (uv) => {
    updateMutation.mutate({
      id: uv.id,
      data: { is_watch_later: !uv.is_watch_later },
    });
  };

  const handleToggleWatched = (uv) => {
    const nextStatus = uv.status === 'watched' ? 'unwatched' : 'watched';
    updateMutation.mutate({
      id: uv.id,
      data: { status: nextStatus },
    });
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setDebouncedQuery('');
    setStatusFilter('all');
    setIsFavouriteOnly(false);
    setIsWatchLaterOnly(false);
    setSortBy('added_at');
    setOrder('desc');
    setPage(1);
    setSearchParams({});
  };

  const videos = data?.items || [];
  const meta = data?.meta || { total_items: 0, page: 1, total_pages: 1, has_next: false, has_previous: false };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[hsl(var(--text-primary))] tracking-tight flex items-center gap-2.5">
            <Library className="w-6 h-6 text-[hsl(var(--primary))]" />
            <span>Video Library</span>
          </h1>
          <p className="text-sm text-[hsl(var(--text-secondary))] mt-0.5">
            {meta.total_items} {meta.total_items === 1 ? 'video' : 'videos'} saved in your collection
          </p>
        </div>

        <button
          onClick={onOpenAddModal}
          className="flex items-center justify-center gap-2 py-2.5 px-4 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all shadow-md shadow-[hsl(var(--primary))/0.2] shrink-0"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>Save Video</span>
        </button>
      </div>

      {/* Filter & Search Controls */}
      <FilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        statusFilter={statusFilter}
        onStatusChange={(st) => { setStatusFilter(st); setPage(1); }}
        isFavouriteOnly={isFavouriteOnly}
        onToggleFavouriteOnly={() => { setIsFavouriteOnly(!isFavouriteOnly); setPage(1); }}
        isWatchLaterOnly={isWatchLaterOnly}
        onToggleWatchLaterOnly={() => { setIsWatchLaterOnly(!isWatchLaterOnly); setPage(1); }}
        sortBy={sortBy}
        order={order}
        onSortChange={(sBy, ord) => { setSortBy(sBy); setOrder(ord); setPage(1); }}
        onResetFilters={handleResetFilters}
      />

      {/* Video Content Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, idx) => (
            <VideoCardSkeleton key={idx} />
          ))}
        </div>
      ) : isError ? (
        <div className="p-8 text-center bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400">
          <p className="text-sm font-medium">Failed to load video library.</p>
          <p className="text-xs text-red-400/80 mt-1">{error?.message || 'Server error'}</p>
        </div>
      ) : videos.length === 0 ? (
        <div className="p-12 text-center bg-[hsl(var(--bg-surface))] rounded-2xl border border-[hsl(var(--border-muted))] space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-[hsl(var(--primary))/0.1] text-[hsl(var(--primary))] flex items-center justify-center mx-auto">
            <Library className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-[hsl(var(--text-primary))]">
              No videos found
            </h3>
            <p className="text-sm text-[hsl(var(--text-secondary))] max-w-sm mx-auto">
              {debouncedQuery || statusFilter !== 'all' || isFavouriteOnly || isWatchLaterOnly
                ? 'No saved videos match your search or filter criteria.'
                : 'Your library is currently empty. Paste a YouTube URL above to start building your collection.'}
            </p>
          </div>
          {debouncedQuery || statusFilter !== 'all' || isFavouriteOnly || isWatchLaterOnly ? (
            <button
              onClick={handleResetFilters}
              className="px-4 py-2 bg-[hsl(var(--bg-surface-hover))] text-[hsl(var(--text-primary))] text-xs font-semibold rounded-xl hover:bg-[hsl(var(--border-muted))]"
            >
              Clear Active Filters
            </button>
          ) : (
            <button
              onClick={onOpenAddModal}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-[hsl(var(--primary))] text-slate-950 text-xs font-bold rounded-xl"
            >
              <Plus className="w-4 h-4 stroke-[3]" />
              <span>Save Your First Video</span>
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {videos.map((uv) => (
              <VideoCard
                key={uv.id}
                userVideo={uv}
                onToggleFavourite={handleToggleFavourite}
                onToggleWatchLater={handleToggleWatchLater}
                onToggleWatched={handleToggleWatched}
              />
            ))}
          </div>

          {/* Server-Side Pagination Bar */}
          {meta.total_pages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-[hsl(var(--border-muted))/0.5]">
              <span className="text-xs text-[hsl(var(--text-secondary))] font-medium">
                Page {meta.page} of {meta.total_pages} ({meta.total_items} total items)
              </span>

              <div className="flex items-center gap-2">
                <button
                  disabled={!meta.has_previous}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="flex items-center gap-1 px-3 py-1.5 bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] text-xs font-medium text-[hsl(var(--text-primary))] rounded-xl hover:bg-[hsl(var(--bg-surface-hover))] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous</span>
                </button>

                <button
                  disabled={!meta.has_next}
                  onClick={() => setPage((p) => p + 1)}
                  className="flex items-center gap-1 px-3 py-1.5 bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] text-xs font-medium text-[hsl(var(--text-primary))] rounded-xl hover:bg-[hsl(var(--bg-surface-hover))] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
