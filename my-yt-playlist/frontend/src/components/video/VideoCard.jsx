import React from 'react';
import { Clock, Star, CheckCircle2, ExternalLink } from 'lucide-react';
import { formatDuration, formatDate } from '../../utils/formatters';

export default function VideoCard({
  userVideo,
  onToggleFavourite,
  onToggleWatchLater,
  onToggleWatched,
  onSelectVideo,
}) {
  const { video, status, is_favourite, is_watch_later, added_at } = userVideo;

  const isWatched = status === 'watched';

  return (
    <div
      onClick={() => onSelectVideo && onSelectVideo(userVideo)}
      className="group bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] hover:border-[hsl(var(--border-focus))] rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col"
    >
      {/* Thumbnail Container (16:9 Aspect Ratio) */}
      <div className="relative w-full aspect-video bg-slate-900 overflow-hidden">
        <img
          src={video.thumbnail_url}
          alt={video.title}
          loading="lazy"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?q=80&w=600&auto=format&fit=crop';
          }}
        />

        {/* Duration Badge */}
        <div className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-slate-950/85 backdrop-blur-sm text-slate-100 text-xs font-mono rounded shadow">
          {formatDuration(video.duration_seconds)}
        </div>

        {/* Unavailable Banner */}
        {video.is_unavailable && (
          <div className="absolute top-2 left-2 px-2 py-0.5 bg-red-500/90 text-white text-[10px] font-bold rounded uppercase tracking-wider">
            Private / Unavailable
          </div>
        )}
      </div>

      {/* Card Content Body */}
      <div className="p-3.5 flex-1 flex flex-col justify-between space-y-3">
        <div>
          <h3 className="font-semibold text-sm text-[hsl(var(--text-primary))] line-clamp-2 leading-snug group-hover:text-[hsl(var(--primary))] transition-colors">
            {video.title}
          </h3>
          <p className="text-xs text-[hsl(var(--text-secondary))] line-clamp-1 mt-1 font-medium">
            {video.channel_name}
          </p>
        </div>

        {/* Footer Meta & Toggle Controls */}
        <div className="pt-2.5 border-t border-[hsl(var(--border-muted))/0.5] flex items-center justify-between text-xs text-[hsl(var(--text-muted))]">
          <span>{formatDate(added_at)}</span>

          {/* Quick Action Icon Toggles */}
          <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
            {/* Favourite Star */}
            <button
              onClick={() => onToggleFavourite && onToggleFavourite(userVideo)}
              title={is_favourite ? 'Remove from Favourites' : 'Add to Favourites'}
              className={`p-1.5 rounded-lg transition-colors ${
                is_favourite
                  ? 'text-[hsl(var(--favourite))] bg-[hsl(var(--favourite))/0.15]'
                  : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))]'
              }`}
            >
              <Star className={`w-4 h-4 ${is_favourite ? 'fill-[hsl(var(--favourite))]' : ''}`} />
            </button>

            {/* Watch Later Clock */}
            <button
              onClick={() => onToggleWatchLater && onToggleWatchLater(userVideo)}
              title={is_watch_later ? 'Remove from Watch Later' : 'Add to Watch Later'}
              className={`p-1.5 rounded-lg transition-colors ${
                is_watch_later
                  ? 'text-[hsl(var(--watch-later))] bg-[hsl(var(--watch-later))/0.15]'
                  : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))]'
              }`}
            >
              <Clock className="w-4 h-4" />
            </button>

            {/* Watched Checkmark */}
            <button
              onClick={() => onToggleWatched && onToggleWatched(userVideo)}
              title={isWatched ? 'Mark as Unwatched' : 'Mark as Watched'}
              className={`p-1.5 rounded-lg transition-colors ${
                isWatched
                  ? 'text-[hsl(var(--watched))] bg-[hsl(var(--watched))/0.15]'
                  : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))]'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
            </button>

            {/* External YouTube Link */}
            <a
              href={video.youtube_url}
              target="_blank"
              rel="noopener noreferrer"
              title="Open on YouTube"
              className="p-1.5 rounded-lg text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
