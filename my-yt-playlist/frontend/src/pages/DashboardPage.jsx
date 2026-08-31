import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getVideosApi, updateVideoApi } from '../api/videos.api';
import { getCollectionsApi } from '../api/collections.api';
import { useAuth } from '../contexts/AuthContext';
import QuickQueueSection from '../components/video/QuickQueueSection';
import VideoCard from '../components/video/VideoCard';
import VideoCardSkeleton from '../components/video/VideoCardSkeleton';
import {
  Library,
  Clock,
  Star,
  CheckCircle2,
  FolderKanban,
  ArrowRight,
  Plus,
} from 'lucide-react';

export default function DashboardPage({ onOpenAddModal }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Query Total Saved Videos (Page 1 size 1 to get meta count)
  const { data: libraryData } = useQuery({
    queryKey: ['videos', 'stats', 'total'],
    queryFn: () => getVideosApi({ page: 1, size: 1 }),
  });

  // Query Watch Later Videos Count
  const { data: watchLaterData } = useQuery({
    queryKey: ['videos', 'stats', 'watchLater'],
    queryFn: () => getVideosApi({ page: 1, size: 1, is_watch_later: true }),
  });

  // Query Favourites Count
  const { data: favouritesData } = useQuery({
    queryKey: ['videos', 'stats', 'favourites'],
    queryFn: () => getVideosApi({ page: 1, size: 1, is_favourite: true }),
  });

  // Query Watched Count
  const { data: watchedData } = useQuery({
    queryKey: ['videos', 'stats', 'watched'],
    queryFn: () => getVideosApi({ page: 1, size: 1, status: 'watched' }),
  });

  // Query Recently Saved Videos
  const { data: recentVideosData, isLoading: isLoadingRecent } = useQuery({
    queryKey: ['videos', 'recent'],
    queryFn: () => getVideosApi({ page: 1, size: 6, sort_by: 'added_at', order: 'desc' }),
  });

  // Query Collections
  const { data: collections = [] } = useQuery({
    queryKey: ['collections'],
    queryFn: getCollectionsApi,
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

  const totalSaved = libraryData?.meta?.total_items || 0;
  const watchLaterCount = watchLaterData?.meta?.total_items || 0;
  const favouritesCount = favouritesData?.meta?.total_items || 0;
  const watchedCount = watchedData?.meta?.total_items || 0;

  const recentVideos = recentVideosData?.items || [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-[hsl(var(--bg-surface))] to-[hsl(var(--bg-surface-hover))] p-6 rounded-2xl border border-[hsl(var(--border-muted))] shadow-xl">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-[hsl(var(--text-primary))] tracking-tight">
            Welcome back, {user?.full_name?.split(' ')[0] || 'User'} 👋
          </h1>
          <p className="text-sm text-[hsl(var(--text-secondary))]">
            Manage your personal video library and quick queue
          </p>
        </div>

        <button
          onClick={onOpenAddModal}
          className="flex items-center justify-center gap-2 py-2.5 px-4 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all shadow-md shadow-[hsl(var(--primary))/0.2] shrink-0"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>Save YouTube Video</span>
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => navigate('/library')}
          className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] p-4 rounded-xl shadow-sm hover:border-[hsl(var(--border-focus))] cursor-pointer transition-all space-y-2"
        >
          <div className="flex items-center justify-between text-[hsl(var(--primary))]">
            <span className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-muted))]">
              Total Library
            </span>
            <Library className="w-5 h-5" />
          </div>
          <p className="text-2xl font-bold text-[hsl(var(--text-primary))]">{totalSaved}</p>
        </div>

        <div
          onClick={() => navigate('/watch-later')}
          className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] p-4 rounded-xl shadow-sm hover:border-[hsl(var(--border-focus))] cursor-pointer transition-all space-y-2"
        >
          <div className="flex items-center justify-between text-[hsl(var(--watch-later))]">
            <span className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-muted))]">
              Watch Later
            </span>
            <Clock className="w-5 h-5" />
          </div>
          <p className="text-2xl font-bold text-[hsl(var(--text-primary))]">{watchLaterCount}</p>
        </div>

        <div
          onClick={() => navigate('/favourites')}
          className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] p-4 rounded-xl shadow-sm hover:border-[hsl(var(--border-focus))] cursor-pointer transition-all space-y-2"
        >
          <div className="flex items-center justify-between text-[hsl(var(--favourite))]">
            <span className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-muted))]">
              Favourites
            </span>
            <Star className="w-5 h-5 fill-[hsl(var(--favourite))]" />
          </div>
          <p className="text-2xl font-bold text-[hsl(var(--text-primary))]">{favouritesCount}</p>
        </div>

        <div
          onClick={() => navigate('/watched')}
          className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] p-4 rounded-xl shadow-sm hover:border-[hsl(var(--border-focus))] cursor-pointer transition-all space-y-2"
        >
          <div className="flex items-center justify-between text-[hsl(var(--watched))]">
            <span className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-muted))]">
              Watched
            </span>
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <p className="text-2xl font-bold text-[hsl(var(--text-primary))]">{watchedCount}</p>
        </div>
      </div>

      {/* V1 Unique Feature 2: Smart Quick Queue */}
      <QuickQueueSection
        onToggleFavourite={handleToggleFavourite}
        onToggleWatchLater={handleToggleWatchLater}
        onToggleWatched={handleToggleWatched}
      />

      {/* Recently Saved Videos */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-[hsl(var(--text-primary))]">Recently Saved</h2>
          <button
            onClick={() => navigate('/library')}
            className="flex items-center gap-1.5 text-xs font-semibold text-[hsl(var(--primary))] hover:underline"
          >
            <span>View All Library</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {isLoadingRecent ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <VideoCardSkeleton />
            <VideoCardSkeleton />
            <VideoCardSkeleton />
          </div>
        ) : recentVideos.length === 0 ? (
          <div className="p-8 text-center bg-[hsl(var(--bg-surface))] rounded-2xl border border-[hsl(var(--border-muted))] space-y-3">
            <p className="text-sm text-[hsl(var(--text-secondary))]">
              Your library is currently empty.
            </p>
            <button
              onClick={onOpenAddModal}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[hsl(var(--primary))] text-slate-950 text-xs font-bold rounded-xl"
            >
              <Plus className="w-4 h-4 stroke-[3]" />
              <span>Add Your First Video</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentVideos.map((uv) => (
              <VideoCard
                key={uv.id}
                userVideo={uv}
                onToggleFavourite={handleToggleFavourite}
                onToggleWatchLater={handleToggleWatchLater}
                onToggleWatched={handleToggleWatched}
              />
            ))}
          </div>
        )}
      </div>

      {/* Collections Preview */}
      {collections.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[hsl(var(--text-primary))]">Your Collections</h2>
            <button
              onClick={() => navigate('/collections')}
              className="flex items-center gap-1.5 text-xs font-semibold text-[hsl(var(--primary))] hover:underline"
            >
              <span>Manage Collections</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {collections.slice(0, 3).map((col) => (
              <div
                key={col.id}
                onClick={() => navigate(`/collections`)}
                className="flex items-center gap-4 p-4 bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] hover:border-[hsl(var(--border-focus))] rounded-xl cursor-pointer transition-all"
              >
                <div className="w-10 h-10 rounded-xl bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] flex items-center justify-center shrink-0">
                  <FolderKanban className="w-5 h-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-sm text-[hsl(var(--text-primary))] truncate">
                    {col.name}
                  </h3>
                  <p className="text-xs text-[hsl(var(--text-secondary))]">
                    {col.video_count} {col.video_count === 1 ? 'video' : 'videos'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
