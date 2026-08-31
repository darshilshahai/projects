import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getQuickQueueApi } from '../../api/videos.api';
import VideoCard from './VideoCard';
import VideoCardSkeleton from './VideoCardSkeleton';
import { Zap, Clock } from 'lucide-react';

export default function QuickQueueSection({ onSelectVideo, onToggleFavourite, onToggleWatchLater, onToggleWatched }) {
  const [maxMinutes, setMaxMinutes] = useState(15);

  const { data: videos = [], isLoading, error } = useQuery({
    queryKey: ['quickQueue', maxMinutes],
    queryFn: () => getQuickQueueApi(maxMinutes * 60, 6),
  });

  const timeOptions = [
    { label: '5 Mins', value: 5 },
    { label: '15 Mins', value: 15 },
    { label: '30 Mins', value: 30 },
  ];

  return (
    <div className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl p-5 shadow-lg space-y-4">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] flex items-center justify-center">
            <Zap className="w-5 h-5 fill-[hsl(var(--primary))]" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[hsl(var(--text-primary))] tracking-tight">
              Smart Quick Queue
            </h2>
            <p className="text-xs text-[hsl(var(--text-secondary))]">
              Unwatched videos fitting your available free time
            </p>
          </div>
        </div>

        {/* Minutes Filter Pills */}
        <div className="flex items-center gap-1.5 bg-[hsl(var(--bg-input))] p-1 rounded-xl border border-[hsl(var(--border-muted))/0.5]">
          <Clock className="w-4 h-4 text-[hsl(var(--text-muted))] ml-2 mr-1" />
          {timeOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setMaxMinutes(opt.value)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                maxMinutes === opt.value
                  ? 'bg-[hsl(var(--primary))] text-slate-950 shadow-sm'
                  : 'text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))]'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Video Content Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <VideoCardSkeleton />
          <VideoCardSkeleton />
          <VideoCardSkeleton />
        </div>
      ) : error ? (
        <p className="text-sm text-red-400 py-2">Failed to load quick queue videos.</p>
      ) : videos.length === 0 ? (
        <div className="p-6 text-center bg-[hsl(var(--bg-app))] rounded-xl border border-[hsl(var(--border-muted))/0.5]">
          <p className="text-sm font-medium text-[hsl(var(--text-secondary))]">
            No unwatched videos under {maxMinutes} minutes in your library!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {videos.map((uv) => (
            <VideoCard
              key={uv.id}
              userVideo={uv}
              onSelectVideo={onSelectVideo}
              onToggleFavourite={onToggleFavourite}
              onToggleWatchLater={onToggleWatchLater}
              onToggleWatched={onToggleWatched}
            />
          ))}
        </div>
      )}
    </div>
  );
}
