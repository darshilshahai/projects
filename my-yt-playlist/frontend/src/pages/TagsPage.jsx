import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTagsApi, createTagApi, deleteTagApi } from '../api/tags.api';
import { getVideosApi, updateVideoApi } from '../api/videos.api';
import TagChip from '../components/tag/TagChip';
import VideoCard from '../components/video/VideoCard';
import VideoCardSkeleton from '../components/video/VideoCardSkeleton';
import VideoDetailDrawer from '../components/video/VideoDetailDrawer';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { Tag as TagIcon, Plus, Loader2, AlertCircle } from 'lucide-react';

export default function TagsPage({ onOpenAddModal }) {
  const queryClient = useQueryClient();
  const [newTagName, setNewTagName] = useState('');
  const [selectedTag, setSelectedTag] = useState(null);
  const [tagToDelete, setTagToDelete] = useState(null);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Fetch Tags
  const { data: tags = [], isLoading: isLoadingTags } = useQuery({
    queryKey: ['tags'],
    queryFn: getTagsApi,
  });

  // Fetch Filtered Videos by Tag
  const { data: videosData, isLoading: isLoadingVideos } = useQuery({
    queryKey: ['videos', 'tag', selectedTag?.id],
    queryFn: () => getVideosApi({ tag_id: selectedTag?.id, page: 1, size: 50 }),
    enabled: !!selectedTag,
  });

  // Mutation to Create Tag
  const createTagMutation = useMutation({
    mutationFn: (name) => createTagApi({ name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      setNewTagName('');
      setErrorMsg(null);
    },
    onError: (err) => {
      if (err.code === 'DUPLICATE_RESOURCE') {
        setErrorMsg('Tag already exists.');
      } else {
        setErrorMsg(err.message || 'Failed to create tag.');
      }
    },
  });

  // Mutation to Delete Tag
  const deleteTagMutation = useMutation({
    mutationFn: (id) => deleteTagApi(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      if (selectedTag && selectedTag.id === tagToDelete?.id) {
        setSelectedTag(null);
      }
      setTagToDelete(null);
    },
  });

  // Mutation for Video Toggles
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateVideoApi(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });

  const handleCreateTag = (e) => {
    e.preventDefault();
    setErrorMsg(null);
    const trimmed = newTagName.trim();
    if (!trimmed) return;
    createTagMutation.mutate(trimmed);
  };

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

  const videos = videosData?.items || [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Title Header */}
      <div>
        <h1 className="text-2xl font-bold text-[hsl(var(--text-primary))] tracking-tight flex items-center gap-2.5">
          <TagIcon className="w-6 h-6 text-[hsl(var(--primary))]" />
          <span>Reusable Video Tags</span>
        </h1>
        <p className="text-sm text-[hsl(var(--text-secondary))] mt-0.5">
          Categorize videos using lightweight tags and keywords
        </p>
      </div>

      {/* Tag Creation Bar & Cloud */}
      <div className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl p-5 shadow-md space-y-5">
        {/* Inline Create Form */}
        <form onSubmit={handleCreateTag} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm font-semibold text-[hsl(var(--primary))]">
              #
            </span>
            <input
              type="text"
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              placeholder="Create tag (e.g. fastapi, tutorial, AI)..."
              disabled={createTagMutation.isPending}
              className="w-full pl-8 pr-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={createTagMutation.isPending || !newTagName.trim()}
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all disabled:opacity-50 shadow-md shadow-[hsl(var(--primary))/0.2] shrink-0"
          >
            {createTagMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Plus className="w-4 h-4 stroke-[3]" />
                <span>Add Tag</span>
              </>
            )}
          </button>
        </form>

        {errorMsg && (
          <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 p-2.5 rounded-xl border border-red-500/20">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Tag Cloud */}
        {isLoadingTags ? (
          <div className="flex flex-wrap gap-2">
            <div className="h-7 w-20 bg-[hsl(var(--bg-surface-hover))] rounded-xl animate-pulse" />
            <div className="h-7 w-24 bg-[hsl(var(--bg-surface-hover))] rounded-xl animate-pulse" />
            <div className="h-7 w-16 bg-[hsl(var(--bg-surface-hover))] rounded-xl animate-pulse" />
          </div>
        ) : tags.length === 0 ? (
          <p className="text-xs text-[hsl(var(--text-muted))] text-center py-2 italic">
            No tags created yet. Type a name above to create your first tag.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2 pt-2">
            {tags.map((tag) => (
              <TagChip
                key={tag.id}
                tag={tag}
                isSelected={selectedTag?.id === tag.id}
                onClick={() => setSelectedTag(selectedTag?.id === tag.id ? null : tag)}
                onDelete={(t) => setTagToDelete(t)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Filtered Tag Videos Section */}
      {selectedTag && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[hsl(var(--text-primary))] flex items-center gap-2">
              <span>Videos tagged with</span>
              <span className="text-[hsl(var(--primary))] font-mono">#{selectedTag.name}</span>
            </h2>
            <button
              onClick={() => setSelectedTag(null)}
              className="text-xs font-semibold text-[hsl(var(--text-secondary))] hover:underline"
            >
              Clear Tag Filter
            </button>
          </div>

          {isLoadingVideos ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, idx) => <VideoCardSkeleton key={idx} />)}
            </div>
          ) : videos.length === 0 ? (
            <div className="p-8 text-center bg-[hsl(var(--bg-surface))] rounded-2xl border border-[hsl(var(--border-muted))] space-y-2">
              <p className="text-sm text-[hsl(var(--text-secondary))]">
                No videos currently tagged with #{selectedTag.name}.
              </p>
            </div>
          ) : (
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
          )}
        </div>
      )}

      {/* Video Detail Drawer */}
      <VideoDetailDrawer
        userVideo={selectedVideo}
        isOpen={!!selectedVideo}
        onClose={() => setSelectedVideo(null)}
      />

      {/* Delete Tag Confirmation Modal */}
      <ConfirmDialog
        isOpen={!!tagToDelete}
        title="Delete Tag"
        message={`Are you sure you want to delete tag "#${tagToDelete?.name}"? It will be unattached from all tagged videos.`}
        confirmText="Delete Tag"
        isDangerous={true}
        isLoading={deleteTagMutation.isPending}
        onConfirm={() => deleteTagMutation.mutate(tagToDelete.id)}
        onCancel={() => setTagToDelete(null)}
      />
    </div>
  );
}
