import React, { useState } from 'react';
import { Clock, Star, CheckCircle2, ExternalLink, Play } from 'lucide-react';
import { formatDuration, formatDate } from '../../utils/formatters';
import VideoPlayerModal from './VideoPlayerModal';

export default function VideoCard({
  userVideo,
  onToggleFavourite,
  onToggleWatchLater,
  onToggleWatched,
  onSelectVideo,
}) {
  const { video, status, is_favourite, is_watch_later, added_at } = userVideo;

  const [isPlayerOpen, setIsPlayerOpen] = useState(false);
  const isWatched = status === 'watched';

  const handleCardClick = () => {
    if (onSelectVideo) {
      onSelectVideo(userVideo);
    } else {
      setIsPlayerOpen(true);
    }
  };

  return (
    <>
      <div
        onClick={handleCardClick}
        className="group/card bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] hover:border-[hsl(var(--border-focus))] rounded-xl shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col relative"
      >
        {/* Thumbnail Container (16:9 Aspect Ratio) */}
        <div className="relative w-full aspect-video bg-slate-900 overflow-hidden rounded-t-xl group/thumb">
          <img
            src={video.thumbnail_url}
            alt={video.title}
            loading="lazy"
            className="w-full h-full object-cover group-hover/card:scale-105 transition-transform duration-300"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?q=80&w=600&auto=format&fit=crop';
            }}
          />

          {/* Hover Streaming Play Button Overlay */}
          <div
            onClick={(e) => {
              e.stopPropagation();
              setIsPlayerOpen(true);
            }}
            className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover/thumb:opacity-100 transition-opacity flex items-center justify-center"
            title="Stream Video Now"
          >
            <div className="w-12 h-12 rounded-full bg-[hsl(var(--primary))] text-slate-950 flex items-center justify-center shadow-2xl transform scale-90 group-hover/thumb:scale-100 transition-transform">
              <Play className="w-6 h-6 fill-slate-950 ml-0.5" />
            </div>
          </div>

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
            <h3 className="font-semibold text-sm text-[hsl(var(--text-primary))] line-clamp-2 leading-snug group-hover/card:text-[hsl(var(--primary))] transition-colors">
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
              <div className="relative group/tooltip">
                <button
                  onClick={() => onToggleFavourite && onToggleFavourite(userVideo)}
                  aria-label={is_favourite ? 'Remove from Favourites' : 'Add to Favourites'}
                  className={`p-1.5 rounded-lg transition-colors ${
                    is_favourite
                      ? 'text-[hsl(var(--favourite))] bg-[hsl(var(--favourite))/0.15]'
                      : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))]'
                  }`}
                >
                  <Star className={`w-4 h-4 ${is_favourite ? 'fill-[hsl(var(--favourite))]' : ''}`} />
                </button>

                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-2 py-1 bg-slate-900 border border-[hsl(var(--border-muted))] text-slate-100 text-[10px] font-semibold rounded-md opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-xl z-30">
                  {is_favourite ? 'Remove Favourite' : 'Add Favourite'}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[1px] border-4 border-transparent border-t-slate-900" />
                </div>
              </div>

              {/* Watch Later Clock */}
              <div className="relative group/tooltip">
                <button
                  onClick={() => onToggleWatchLater && onToggleWatchLater(userVideo)}
                  aria-label={is_watch_later ? 'Remove from Watch Later' : 'Add to Watch Later'}
                  className={`p-1.5 rounded-lg transition-colors ${
                    is_watch_later
                      ? 'text-[hsl(var(--watch-later))] bg-[hsl(var(--watch-later))/0.15]'
                      : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))]'
                  }`}
                >
                  <Clock className="w-4 h-4" />
                </button>

                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-2 py-1 bg-slate-900 border border-[hsl(var(--border-muted))] text-slate-100 text-[10px] font-semibold rounded-md opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-xl z-30">
                  {is_watch_later ? 'Remove Watch Later' : 'Add Watch Later'}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[1px] border-4 border-transparent border-t-slate-900" />
                </div>
              </div>

              {/* Watched Checkmark */}
              <div className="relative group/tooltip">
                <button
                  onClick={() => onToggleWatched && onToggleWatched(userVideo)}
                  aria-label={isWatched ? 'Mark as Unwatched' : 'Mark as Watched'}
                  className={`p-1.5 rounded-lg transition-colors ${
                    isWatched
                      ? 'text-[hsl(var(--watched))] bg-[hsl(var(--watched))/0.15]'
                      : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))]'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                </button>

                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-2 py-1 bg-slate-900 border border-[hsl(var(--border-muted))] text-slate-100 text-[10px] font-semibold rounded-md opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-xl z-30">
                  {isWatched ? 'Mark Unwatched' : 'Mark Watched'}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[1px] border-4 border-transparent border-t-slate-900" />
                </div>
              </div>

              {/* Stream Video Button */}
              <div className="relative group/tooltip">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsPlayerOpen(true);
                  }}
                  aria-label="Stream Video in App"
                  className="p-1.5 rounded-lg text-[hsl(var(--primary))] bg-[hsl(var(--primary))/0.15] hover:bg-[hsl(var(--primary))] hover:text-slate-950 transition-colors flex items-center justify-center"
                >
                  <Play className="w-4 h-4 fill-current" />
                </button>

                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-2 py-1 bg-slate-900 border border-[hsl(var(--border-muted))] text-slate-100 text-[10px] font-semibold rounded-md opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-xl z-30">
                  Stream Video
                  <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[1px] border-4 border-transparent border-t-slate-900" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Inline Video Player Modal */}
      <VideoPlayerModal
        userVideo={userVideo}
        isOpen={isPlayerOpen}
        onClose={() => setIsPlayerOpen(false)}
        onToggleFavourite={onToggleFavourite}
        onToggleWatchLater={onToggleWatchLater}
        onToggleWatched={onToggleWatched}
      />
    </>
  );
}
