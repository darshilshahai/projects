import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getVideosApi, updateVideoApi } from '../api/videos.api';
import VideoCard from '../components/video/VideoCard';
import VideoCardSkeleton from '../components/video/VideoCardSkeleton';
import VideoDetailDrawer from '../components/video/VideoDetailDrawer';
import { Clock, ChevronLeft, ChevronRight, Plus } from 'lucide-react';

export default function WatchLaterPage({ onOpenAddModal }) {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const pageSize = 12;

  const queryParams = {
    page,
    size: pageSize,
    is_watch_later: true,
    sort_by: 'added_at',
    order: 'desc',
  };

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['videos', 'watchLater', queryParams],
    queryFn: () => getVideosApi(queryParams),
    keepPreviousData: true,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateVideoApi(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['quickQueue'] });
    },
  });

  const handleToggleFavourite = (uv) => {
    updateMutation.mutate({ id: uv.id, data: { is_favourite: !uv.is_favourite } });
  };

  const handleToggleWatchLater = (uv) => {
    updateMutation.mutate({ id: uv.id, data: { is_watch_later: !uv.is_watch_later } });
  };

  const handleToggleWatched = (uv) => {
    const nextStatus = uv.status === 'watched' ? 'unwatched' : 'watched';
    updateMutation.mutate({ id: uv.id, data: { status: nextStatus } });
  };

  const videos = data?.items || [];
  const meta = data?.meta || { total_items: 0, page: 1, total_pages: 1, has_next: false, has_previous: false };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[hsl(var(--text-primary))] tracking-tight flex items-center gap-2.5">
            <Clock className="w-6 h-6 text-[hsl(var(--watch-later))]" />
            <span>Watch Later Queue</span>
          </h1>
          <p className="text-sm text-[hsl(var(--text-secondary))] mt-0.5">
            {meta.total_items} {meta.total_items === 1 ? 'video' : 'videos'} queued to watch
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

      {/* Grid Area */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, idx) => <VideoCardSkeleton key={idx} />)}
        </div>
      ) : isError ? (
        <div className="p-8 text-center bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400">
          <p className="text-sm font-medium">Failed to load watch later queue.</p>
        </div>
      ) : videos.length === 0 ? (
        <div className="p-12 text-center bg-[hsl(var(--bg-surface))] rounded-2xl border border-[hsl(var(--border-muted))] space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-[hsl(var(--watch-later))/0.15] text-[hsl(var(--watch-later))] flex items-center justify-center mx-auto">
            <Clock className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-[hsl(var(--text-primary))]">
              Your Watch Later queue is empty
            </h3>
            <p className="text-sm text-[hsl(var(--text-secondary))] max-w-sm mx-auto">
              Click the clock icon on any video card in your library to add it to your Watch Later queue.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {videos.map((uv) => (
              <VideoCard
                key={uv.id}
                userVideo={uv}
                onSelectVideo={setSelectedVideo}
                onToggleFavourite={handleToggleFavourite}
                onToggleWatchLater={handleToggleWatchLater}
                onToggleWatched={handleToggleWatched}
              />
            ))}
          </div>

          {meta.total_pages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-[hsl(var(--border-muted))/0.5]">
              <span className="text-xs text-[hsl(var(--text-secondary))] font-medium">
                Page {meta.page} of {meta.total_pages}
              </span>
              <div className="flex gap-2">
                <button disabled={!meta.has_previous} onClick={() => setPage((p) => Math.max(1, p - 1))} className="px-3 py-1.5 bg-[hsl(var(--bg-surface))] text-xs font-medium rounded-xl disabled:opacity-40">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button disabled={!meta.has_next} onClick={() => setPage((p) => p + 1)} className="px-3 py-1.5 bg-[hsl(var(--bg-surface))] text-xs font-medium rounded-xl disabled:opacity-40">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Video Detail Drawer */}
      <VideoDetailDrawer
        userVideo={selectedVideo}
        isOpen={!!selectedVideo}
        onClose={() => setSelectedVideo(null)}
      />
    </div>
  );
}
