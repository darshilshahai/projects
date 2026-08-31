import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createNoteApi, deleteNoteApi, deleteVideoApi, updateVideoApi } from '../../api/videos.api';
import { formatDuration, formatDate } from '../../utils/formatters';
import ConfirmDialog from '../ui/ConfirmDialog';
import {
  X,
  Star,
  Clock,
  CheckCircle2,
  ExternalLink,
  Plus,
  Trash2,
  StickyNote,
  Loader2,
  Calendar,
  Tag,
} from 'lucide-react';

export default function VideoDetailDrawer({ userVideo, isOpen, onClose }) {
  if (!isOpen || !userVideo) return null;

  const { video, status, is_favourite, is_watch_later, notes, added_at, timestamp_notes = [] } = userVideo;

  const queryClient = useQueryClient();

  // Note form state
  const [noteText, setNoteText] = useState('');
  const [timestampSeconds, setTimestampSeconds] = useState(0);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);

  // Mutation to Add Timestamp Note
  const addNoteMutation = useMutation({
    mutationFn: (data) => createNoteApi(userVideo.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      setNoteText('');
      setTimestampSeconds(0);
    },
  });

  // Mutation to Delete Note
  const deleteNoteMutation = useMutation({
    mutationFn: (noteId) => deleteNoteApi(userVideo.id, noteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });

  // Mutation to Delete Video
  const deleteVideoMutation = useMutation({
    mutationFn: () => deleteVideoApi(userVideo.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['quickQueue'] });
      setIsDeleteConfirmOpen(false);
      onClose();
    },
  });

  // Mutation to Update Video State
  const updateMutation = useMutation({
    mutationFn: (data) => updateVideoApi(userVideo.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['quickQueue'] });
    },
  });

  const handleAddNote = (e) => {
    e.preventDefault();
    if (!noteText.trim()) return;

    addNoteMutation.mutate({
      timestamp_seconds: Number(timestampSeconds) || 0,
      note_text: noteText.trim(),
    });
  };

  const isWatched = status === 'watched';

  return (
    <>
      <div className="fixed inset-0 z-50 flex justify-end">
        {/* Backdrop Overlay */}
        <div
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />

        {/* Drawer Window */}
        <div className="relative w-full max-w-xl bg-[hsl(var(--bg-surface))] border-l border-[hsl(var(--border-muted))] h-full overflow-y-auto shadow-2xl p-6 space-y-6 z-10 animate-in slide-in-from-right duration-200">
          {/* Header Bar */}
          <div className="flex items-center justify-between pb-4 border-b border-[hsl(var(--border-muted))/0.5]">
            <span className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-muted))]">
              Video Detail View
            </span>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Large Video Preview Thumbnail */}
          <div className="relative w-full aspect-video rounded-xl overflow-hidden bg-slate-900 shadow-md">
            <img
              src={video.thumbnail_url}
              alt={video.title}
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-3 right-3 px-2 py-1 bg-slate-950/90 text-slate-100 text-xs font-mono rounded-lg">
              {formatDuration(video.duration_seconds)}
            </div>

            <a
              href={video.youtube_url}
              target="_blank"
              rel="noopener noreferrer"
              className="absolute inset-0 bg-slate-950/40 hover:bg-slate-950/20 transition-all flex items-center justify-center group"
            >
              <div className="flex items-center gap-2 py-2.5 px-4 bg-[hsl(var(--primary))] text-slate-950 font-bold text-xs rounded-xl shadow-lg group-hover:scale-105 transition-transform">
                <ExternalLink className="w-4 h-4" />
                <span>Watch on YouTube</span>
              </div>
            </a>
          </div>

          {/* Title & Metadata Details */}
          <div className="space-y-3">
            <h2 className="text-xl font-bold text-[hsl(var(--text-primary))] leading-snug">
              {video.title}
            </h2>
            <p className="text-sm font-semibold text-[hsl(var(--primary))]">
              {video.channel_name}
            </p>

            <div className="flex flex-wrap items-center gap-3 text-xs text-[hsl(var(--text-secondary))] pt-1">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-[hsl(var(--text-muted))]" />
                Saved {formatDate(added_at)}
              </span>
              {video.published_at && (
                <span>Published {formatDate(video.published_at)}</span>
              )}
            </div>
          </div>

          {/* Action Quick Toggle Buttons */}
          <div className="flex flex-wrap items-center gap-2 pt-2 pb-4 border-b border-[hsl(var(--border-muted))/0.5]">
            <button
              onClick={() => updateMutation.mutate({ is_favourite: !is_favourite })}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl transition-all ${
                is_favourite
                  ? 'bg-[hsl(var(--favourite))] text-slate-950'
                  : 'bg-[hsl(var(--bg-input))] text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] border border-[hsl(var(--border-muted))/0.5]'
              }`}
            >
              <Star className={`w-4 h-4 ${is_favourite ? 'fill-slate-950' : ''}`} />
              <span>{is_favourite ? 'Favourite' : 'Add Favourite'}</span>
            </button>

            <button
              onClick={() => updateMutation.mutate({ is_watch_later: !is_watch_later })}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl transition-all ${
                is_watch_later
                  ? 'bg-[hsl(var(--watch-later))] text-white'
                  : 'bg-[hsl(var(--bg-input))] text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] border border-[hsl(var(--border-muted))/0.5]'
              }`}
            >
              <Clock className="w-4 h-4" />
              <span>{is_watch_later ? 'Watch Later' : 'Add Watch Later'}</span>
            </button>

            <button
              onClick={() => updateMutation.mutate({ status: isWatched ? 'unwatched' : 'watched' })}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl transition-all ${
                isWatched
                  ? 'bg-[hsl(var(--watched))] text-slate-950'
                  : 'bg-[hsl(var(--bg-input))] text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] border border-[hsl(var(--border-muted))/0.5]'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{isWatched ? 'Watched' : 'Mark Watched'}</span>
            </button>
          </div>

          {/* Description Snippet */}
          {video.description && (
            <div className="space-y-1.5">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-muted))]">
                Description
              </h4>
              <p className="text-xs text-[hsl(var(--text-secondary))] line-clamp-4 leading-relaxed bg-[hsl(var(--bg-input))] p-3 rounded-xl border border-[hsl(var(--border-muted))/0.5]">
                {video.description}
              </p>
            </div>
          )}

          {/* Timestamped Video Notes Section */}
          <div className="space-y-4 pt-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[hsl(var(--text-primary))] flex items-center gap-2">
                <StickyNote className="w-4 h-4 text-[hsl(var(--primary))]" />
                <span>Timestamped Notes</span>
              </h3>
              <span className="text-xs text-[hsl(var(--text-muted))]">
                {timestamp_notes.length} {timestamp_notes.length === 1 ? 'note' : 'notes'}
              </span>
            </div>

            {/* Note Creation Form */}
            <form onSubmit={handleAddNote} className="space-y-3 bg-[hsl(var(--bg-input))] p-3.5 rounded-xl border border-[hsl(var(--border-muted))]">
              <div className="flex items-center gap-3">
                <div className="w-32">
                  <label className="block text-[10px] uppercase font-semibold text-[hsl(var(--text-muted))] mb-1">
                    Timestamp (Secs)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={timestampSeconds}
                    onChange={(e) => setTimestampSeconds(e.target.value)}
                    placeholder="e.g. 120"
                    className="w-full px-2.5 py-1.5 bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-lg text-xs font-mono text-[hsl(var(--text-primary))]"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-[10px] uppercase font-semibold text-[hsl(var(--text-muted))] mb-1">
                    Note Text
                  </label>
                  <input
                    type="text"
                    required
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Key concept or timestamp comment..."
                    className="w-full px-3 py-1.5 bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-lg text-xs text-[hsl(var(--text-primary))]"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={addNoteMutation.isPending || !noteText.trim()}
                className="w-full flex items-center justify-center gap-1.5 py-2 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-xs rounded-lg transition-all disabled:opacity-50"
              >
                {addNoteMutation.isPending ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <>
                    <Plus className="w-3.5 h-3.5 stroke-[3]" />
                    <span>Add Timestamp Note</span>
                  </>
                )}
              </button>
            </form>

            {/* List of Notes */}
            {timestamp_notes.length === 0 ? (
              <p className="text-xs text-[hsl(var(--text-muted))] text-center py-3 italic">
                No timestamped notes added yet.
              </p>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {timestamp_notes.map((n) => (
                  <div
                    key={n.id}
                    className="flex items-center justify-between gap-3 p-3 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))/0.5] rounded-xl text-xs"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="px-2 py-0.5 bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] font-mono font-bold rounded shrink-0">
                        {formatDuration(n.timestamp_seconds)}
                      </span>
                      <p className="text-[hsl(var(--text-primary))] truncate">{n.note_text}</p>
                    </div>

                    <button
                      onClick={() => deleteNoteMutation.mutate(n.id)}
                      title="Delete Note"
                      className="p-1 text-[hsl(var(--text-muted))] hover:text-red-400 transition-colors shrink-0"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Delete Video Danger Zone */}
          <div className="pt-6 border-t border-[hsl(var(--border-muted))/0.5]">
            <button
              onClick={() => setIsDeleteConfirmOpen(true)}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 font-semibold text-xs rounded-xl transition-all"
            >
              <Trash2 className="w-4 h-4" />
              <span>Remove Video from Library</span>
            </button>
          </div>
        </div>
      </div>

      {/* Delete Video Confirmation Modal */}
      <ConfirmDialog
        isOpen={isDeleteConfirmOpen}
        title="Remove Video"
        message={`Are you sure you want to remove "${video.title}" from your personal library?`}
        confirmText="Remove Video"
        isDangerous={true}
        isLoading={deleteVideoMutation.isPending}
        onConfirm={() => deleteVideoMutation.mutate()}
        onCancel={() => setIsDeleteConfirmOpen(false)}
      />
    </>
  );
}
