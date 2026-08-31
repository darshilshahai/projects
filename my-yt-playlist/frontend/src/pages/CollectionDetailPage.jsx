import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCollectionByIdApi, removeVideoFromCollectionApi } from '../api/collections.api';
import { getVideosApi, updateVideoApi } from '../api/videos.api';
import VideoCard from '../components/video/VideoCard';
import VideoCardSkeleton from '../components/video/VideoCardSkeleton';
import VideoDetailDrawer from '../components/video/VideoDetailDrawer';
import { FolderKanban, ArrowLeft, Plus, Trash2 } from 'lucide-react';

export default function CollectionDetailPage({ onOpenAddModal }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedVideo, setSelectedVideo] = useState(null);

  // Fetch Collection Info
  const { data: collection, isLoading: isLoadingCol } = useQuery({
    queryKey: ['collections', id],
    queryFn: () => getCollectionByIdApi(id),
  });

  // Fetch Videos inside Collection
  const { data: videosData, isLoading: isLoadingVideos } = useQuery({
    queryKey: ['videos', 'collection', id],
    queryFn: () => getVideosApi({ collection_id: id, page: 1, size: 50 }),
  });

  // Mutation to Remove Video from Collection
  const removeMutation = useMutation({
    mutationFn: (userVideoId) => removeVideoFromCollectionApi(id, userVideoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos', 'collection', id] });
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    },
  });

  // Mutation for Quick Video State Updates
  const updateMutation = useMutation({
    mutationFn: ({ userVideoId, data }) => updateVideoApi(userVideoId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });

  const handleToggleFavourite = (uv) => {
    updateMutation.mutate({ userVideoId: uv.id, data: { is_favourite: !uv.is_favourite } });
  };

  const handleToggleWatchLater = (uv) => {
    updateMutation.mutate({ userVideoId: uv.id, data: { is_watch_later: !uv.is_watch_later } });
  };

  const handleToggleWatched = (uv) => {
    const nextStatus = uv.status === 'watched' ? 'unwatched' : 'watched';
    updateMutation.mutate({ userVideoId: uv.id, data: { status: nextStatus } });
  };

  const videos = videosData?.items || [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Back Button */}
      <button
        onClick={() => navigate('/collections')}
        className="inline-flex items-center gap-2 text-xs font-semibold text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Collections</span>
      </button>

      {/* Collection Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[hsl(var(--bg-surface))] p-6 rounded-2xl border border-[hsl(var(--border-muted))] shadow-lg">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] flex items-center justify-center shrink-0">
            <FolderKanban className="w-6 h-6" />
          </div>

          <div className="space-y-1">
            <h1 className="text-2xl font-bold text-[hsl(var(--text-primary))]">
              {collection?.name || 'Collection Details'}
            </h1>
            {collection?.description && (
              <p className="text-sm text-[hsl(var(--text-secondary))]">
                {collection.description}
              </p>
            )}
          </div>
        </div>

        <button
          onClick={onOpenAddModal}
          className="flex items-center justify-center gap-2 py-2.5 px-4 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all shrink-0"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>Save New Video</span>
        </button>
      </div>

      {/* Video Grid inside Collection */}
      {isLoadingVideos ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, idx) => <VideoCardSkeleton key={idx} />)}
        </div>
      ) : videos.length === 0 ? (
        <div className="p-12 text-center bg-[hsl(var(--bg-surface))] rounded-2xl border border-[hsl(var(--border-muted))] space-y-3">
          <p className="text-sm text-[hsl(var(--text-secondary))]">
            No videos in this collection yet.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {videos.map((uv) => (
            <div key={uv.id} className="relative group">
              <VideoCard
                userVideo={uv}
                onSelectVideo={setSelectedVideo}
                onToggleFavourite={handleToggleFavourite}
                onToggleWatchLater={handleToggleWatchLater}
                onToggleWatched={handleToggleWatched}
              />

              {/* Remove from Collection Action overlay */}
              <button
                onClick={() => removeMutation.mutate(uv.id)}
                title="Remove from Collection"
                className="absolute top-2 right-2 p-1.5 bg-slate-950/80 hover:bg-red-500 text-slate-200 hover:text-white rounded-lg opacity-0 group-hover:opacity-100 transition-all shadow-md z-10"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Detail Drawer */}
      <VideoDetailDrawer
        userVideo={selectedVideo}
        isOpen={!!selectedVideo}
        onClose={() => setSelectedVideo(null)}
      />
    </div>
  );
}
