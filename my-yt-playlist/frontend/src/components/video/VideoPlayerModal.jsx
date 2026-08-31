import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createNoteApi, deleteNoteApi } from '../../api/videos.api';
import { extractYouTubeId, formatDuration } from '../../utils/formatters';
import {
  X,
  Star,
  Clock,
  CheckCircle2,
  StickyNote,
  Play,
  Plus,
  Trash2,
  Loader2,
  Bold,
  Italic,
  List,
  Code,
} from 'lucide-react';

export default function VideoPlayerModal({
  userVideo,
  isOpen,
  onClose,
  initialTimestampSeconds = 0,
  onToggleFavourite,
  onToggleWatchLater,
  onToggleWatched,
}) {
  const [startTime, setStartTime] = useState(initialTimestampSeconds);
  const [noteText, setNoteText] = useState('');
  const [noteTimestampSeconds, setNoteTimestampSeconds] = useState(0);

  const queryClient = useQueryClient();

  useEffect(() => {
    setStartTime(initialTimestampSeconds || 0);
  }, [initialTimestampSeconds, isOpen]);

  // Mutation to Add Video Note
  const addNoteMutation = useMutation({
    mutationFn: (data) => createNoteApi(userVideo?.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['quickQueue'] });
      setNoteText('');
      setNoteTimestampSeconds(0);
    },
  });

  // Mutation to Delete Note
  const deleteNoteMutation = useMutation({
    mutationFn: (noteId) => deleteNoteApi(userVideo?.id, noteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['quickQueue'] });
    },
  });

  // Escape key handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !userVideo) return null;

  const { video, status, is_favourite, is_watch_later, timestamp_notes = [] } = userVideo;
  const youtubeId = video.youtube_id || extractYouTubeId(video.youtube_url);
  const isWatched = status === 'watched';

  const handleAddNote = (e) => {
    e.preventDefault();
    if (!noteText.trim()) return;

    addNoteMutation.mutate({
      timestamp_seconds: Number(noteTimestampSeconds) || 0,
      note_text: noteText.trim(),
    });
  };

  // Formatting Toolbox Helpers
  const handleInsertFormatting = (prefix, suffix = '') => {
    const textarea = document.getElementById('video-note-textarea');
    if (!textarea) return;

    const start = textarea.selectionStart || 0;
    const end = textarea.selectionEnd || 0;
    const selectedText = noteText.substring(start, end);

    const replacement = `${prefix}${selectedText || 'text'}${suffix}`;
    const updatedText = noteText.substring(0, start) + replacement + noteText.substring(end);
    setNoteText(updatedText);

    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + prefix.length, end + prefix.length);
    }, 50);
  };

  const handleInsertTimestampBadge = () => {
    const formatted = `[${formatDuration(startTime)}] `;
    setNoteText((prev) => prev + (prev.endsWith(' ') || !prev ? '' : ' ') + formatted);
  };

  // Construct iframe embed URL with optional start timestamp
  const embedUrl = `https://www.youtube-nocookie.com/embed/${youtubeId}?autoplay=1&rel=0&enablejsapi=1${
    startTime > 0 ? `&start=${startTime}` : ''
  }`;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="player-video-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 lg:p-6"
    >
      {/* Dark Cinema Overlay Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/90 backdrop-blur-md transition-opacity"
        onClick={onClose}
      />

      {/* Modal Container (Wide Cinema Split Layout) */}
      <div className="relative w-full max-w-7xl bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl shadow-2xl overflow-hidden z-10 flex flex-col max-h-[95vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[hsl(var(--border-muted))/0.5] shrink-0 bg-[hsl(var(--bg-surface))]">
          <div className="min-w-0 pr-4">
            <h2 id="player-video-title" className="text-base sm:text-lg font-bold text-[hsl(var(--text-primary))] truncate">
              {video.title}
            </h2>
            <p className="text-xs text-[hsl(var(--primary))] font-semibold">
              {video.channel_name}
            </p>
          </div>

          <button
            onClick={onClose}
            aria-label="Close Video Player"
            className="p-1.5 rounded-xl text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] transition-colors shrink-0"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Scrollable Body (Cinema Split Grid) */}
        <div className="overflow-y-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* LEFT COLUMN: Video Stream Player & Quick Actions (lg:col-span-7) */}
          <div className="lg:col-span-7 space-y-4">
            {/* Cinema iFrame Video Stream Player */}
            <div className="relative w-full aspect-video bg-slate-950 rounded-xl overflow-hidden shadow-2xl border border-slate-800">
              {youtubeId ? (
                <iframe
                  key={`${youtubeId}-${startTime}`}
                  src={embedUrl}
                  title={video.title}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  className="w-full h-full border-0"
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-slate-400 text-sm space-y-2">
                  <Play className="w-12 h-12 text-red-500" />
                  <p>Unable to stream video embed. Invalid YouTube ID.</p>
                </div>
              )}
            </div>

            {/* Quick Action Toggle Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-[hsl(var(--bg-input))] rounded-xl border border-[hsl(var(--border-muted))/0.5]">
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => onToggleFavourite && onToggleFavourite(userVideo)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                    is_favourite
                      ? 'bg-[hsl(var(--favourite))] text-slate-950'
                      : 'bg-[hsl(var(--bg-surface))] text-[hsl(var(--text-secondary))] border border-[hsl(var(--border-muted))] hover:text-[hsl(var(--text-primary))]'
                  }`}
                >
                  <Star className={`w-3.5 h-3.5 ${is_favourite ? 'fill-slate-950' : ''}`} />
                  <span>{is_favourite ? 'Favourite' : 'Add Favourite'}</span>
                </button>

                <button
                  onClick={() => onToggleWatchLater && onToggleWatchLater(userVideo)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                    is_watch_later
                      ? 'bg-[hsl(var(--watch-later))] text-white'
                      : 'bg-[hsl(var(--bg-surface))] text-[hsl(var(--text-secondary))] border border-[hsl(var(--border-muted))] hover:text-[hsl(var(--text-primary))]'
                  }`}
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span>{is_watch_later ? 'Watch Later' : 'Add Watch Later'}</span>
                </button>

                <button
                  onClick={() => onToggleWatched && onToggleWatched(userVideo)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                    isWatched
                      ? 'bg-[hsl(var(--watched))] text-slate-950'
                      : 'bg-[hsl(var(--bg-surface))] text-[hsl(var(--text-secondary))] border border-[hsl(var(--border-muted))] hover:text-[hsl(var(--text-primary))]'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{isWatched ? 'Watched' : 'Mark Watched'}</span>
                </button>
              </div>

              {video.youtube_url && (
                <a
                  href={video.youtube_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-[hsl(var(--text-muted))] hover:text-[hsl(var(--primary))] transition-colors underline"
                >
                  Open on YouTube.com
                </a>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN: Real-Time Notes Taking Component & Toolbox (lg:col-span-5) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[hsl(var(--text-primary))] flex items-center gap-2">
                <StickyNote className="w-4 h-4 text-[hsl(var(--primary))]" />
                <span>Video Notes & Insights</span>
              </h3>
              <span className="text-[10px] text-[hsl(var(--text-muted))] font-medium">
                {timestamp_notes.length} {timestamp_notes.length === 1 ? 'note' : 'notes'} saved
              </span>
            </div>

            {/* Note Creation Form with Formatting Toolbox */}
            <form onSubmit={handleAddNote} className="space-y-3 bg-[hsl(var(--bg-input))] p-4 rounded-xl border border-[hsl(var(--border-muted))] shadow-sm">
              
              {/* Formatting Toolbox Bar */}
              <div className="flex items-center justify-between pb-2 border-b border-[hsl(var(--border-muted))/0.5]">
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => handleInsertFormatting('**', '**')}
                    title="Bold (**text**)"
                    className="p-1.5 rounded-md text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface))] transition-colors"
                  >
                    <Bold className="w-3.5 h-3.5" />
                  </button>

                  <button
                    type="button"
                    onClick={() => handleInsertFormatting('*', '*')}
                    title="Italic (*text*)"
                    className="p-1.5 rounded-md text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface))] transition-colors"
                  >
                    <Italic className="w-3.5 h-3.5" />
                  </button>

                  <button
                    type="button"
                    onClick={() => handleInsertFormatting('\n• ')}
                    title="Bullet List (• item)"
                    className="p-1.5 rounded-md text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface))] transition-colors"
                  >
                    <List className="w-3.5 h-3.5" />
                  </button>

                  <button
                    type="button"
                    onClick={() => handleInsertFormatting('`', '`')}
                    title="Inline Code (`code`)"
                    className="p-1.5 rounded-md text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface))] transition-colors"
                  >
                    <Code className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Insert Timestamp Shortcut Button */}
                <button
                  type="button"
                  onClick={handleInsertTimestampBadge}
                  title="Insert current timestamp into notes"
                  className="flex items-center gap-1 px-2 py-1 bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] hover:bg-[hsl(var(--primary))] hover:text-slate-950 text-[10px] font-semibold rounded-md transition-colors"
                >
                  <Clock className="w-3 h-3" />
                  <span>Insert [{formatDuration(startTime)}]</span>
                </button>
              </div>

              {/* Multiline Textarea for Note Taking */}
              <div>
                <textarea
                  id="video-note-textarea"
                  rows={5}
                  required
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Write detailed notes, thoughts, or key takeaways for this video..."
                  className="w-full px-3 py-2.5 bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-xl text-xs text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--primary))] transition-all resize-y leading-relaxed font-sans"
                />
              </div>

              {/* Timestamp Seconds & Submit Button */}
              <div className="flex items-center gap-3 pt-1">
                <div className="w-36">
                  <label className="block text-[10px] uppercase font-semibold text-[hsl(var(--text-muted))] mb-1">
                    Timestamp (Secs)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={noteTimestampSeconds}
                    onChange={(e) => setNoteTimestampSeconds(e.target.value)}
                    placeholder="e.g. 120"
                    className="w-full px-2.5 py-1.5 bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-lg text-xs font-mono text-[hsl(var(--text-primary))]"
                  />
                </div>

                <div className="flex-1 pt-4">
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
                        <span>Save Note to Video</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>

            {/* List of Saved Timestamp Notes */}
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {timestamp_notes.length === 0 ? (
                <p className="text-xs text-[hsl(var(--text-muted))] text-center py-4 italic bg-[hsl(var(--bg-input))/0.5] rounded-xl border border-[hsl(var(--border-muted))/0.5]">
                  No notes saved for this video yet. Use the editor above to take notes while watching!
                </p>
              ) : (
                timestamp_notes.map((note) => (
                  <div
                    key={note.id}
                    className="flex items-start justify-between gap-3 p-3 bg-[hsl(var(--bg-input))] hover:bg-[hsl(var(--bg-surface-hover))] border border-[hsl(var(--border-muted))/0.5] hover:border-[hsl(var(--primary))/0.5] rounded-xl text-xs transition-all"
                  >
                    <button
                      onClick={() => setStartTime(note.timestamp_seconds)}
                      className="flex items-start gap-2.5 min-w-0 flex-1 text-left group"
                      title="Seek video to timestamp"
                    >
                      <span className="px-2 py-0.5 bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] font-mono font-bold rounded shrink-0 group-hover:bg-[hsl(var(--primary))] group-hover:text-slate-950 transition-colors mt-0.5">
                        {formatDuration(note.timestamp_seconds)}
                      </span>
                      <p className="text-[hsl(var(--text-primary))] whitespace-pre-wrap leading-relaxed group-hover:text-[hsl(var(--primary))] transition-colors">
                        {note.note_text}
                      </p>
                    </button>

                    <button
                      onClick={() => deleteNoteMutation.mutate(note.id)}
                      title="Delete Note"
                      className="p-1 text-[hsl(var(--text-muted))] hover:text-red-400 transition-colors shrink-0 mt-0.5"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
