import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ingestVideoApi } from '../../api/videos.api';
import { X, Link2, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function AddVideoModal({ isOpen, onClose }) {
  const [url, setUrl] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const queryClient = useQueryClient();

  // Escape key handler for accessible modal closing
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const ingestMutation = useMutation({
    mutationFn: (videoUrl) => ingestVideoApi(videoUrl),
    onSuccess: (data) => {
      setSuccessMsg(`"${data.video.title}" saved to your library!`);
      setErrorMsg(null);
      setUrl('');
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['quickQueue'] });

      setTimeout(() => {
        setSuccessMsg(null);
        onClose();
      }, 1500);
    },
    onError: (err) => {
      setSuccessMsg(null);
      if (err.code === 'DUPLICATE_RESOURCE') {
        setErrorMsg('This video is already in your library.');
      } else if (err.code === 'INVALID_YOUTUBE_URL') {
        setErrorMsg('Please enter a valid YouTube URL (video link, short, or embed link).');
      } else if (err.code === 'YOUTUBE_VIDEO_NOT_FOUND') {
        setErrorMsg('YouTube video not found or private.');
      } else {
        setErrorMsg(err.message || 'Failed to add video. Please try again.');
      }
    },
  });

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setErrorMsg('Please enter a YouTube link.');
      return;
    }

    ingestMutation.mutate(trimmed);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-video-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Box */}
      <div className="relative w-full max-w-lg bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl shadow-2xl p-6 space-y-6 z-10 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] flex items-center justify-center">
              <Link2 className="w-5 h-5" />
            </div>
            <div>
              <h2 id="add-video-title" className="text-lg font-bold text-[hsl(var(--text-primary))]">
                Save YouTube Video
              </h2>
              <p className="text-xs text-[hsl(var(--text-secondary))]">
                Paste any YouTube video link to add to your library
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close Modal"
            className="p-1 rounded-lg text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Alert Notifications */}
        {errorMsg && (
          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p>{errorMsg}</p>
          </div>
        )}

        {successMsg && (
          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <p>{successMsg}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-secondary))] mb-2">
              YouTube Video URL
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
              disabled={ingestMutation.isPending}
              className="w-full px-4 py-3 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all disabled:opacity-50"
            />
            <p className="text-xs text-[hsl(var(--text-muted))] mt-2">
              Metadata (title, channel, duration, thumbnail) will be automatically extracted.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={ingestMutation.isPending}
              className="px-4 py-2.5 text-sm font-medium text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] rounded-xl transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={ingestMutation.isPending || !url.trim()}
              className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-[hsl(var(--primary))/0.2]"
            >
              {ingestMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Fetching Metadata...</span>
                </>
              ) : (
                <span>Save Video</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
