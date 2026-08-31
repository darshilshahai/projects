import React from 'react';

export default function VideoCardSkeleton() {
  return (
    <div className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-xl overflow-hidden shadow-sm animate-pulse">
      {/* 16:9 Thumbnail Placeholder */}
      <div className="w-full aspect-video bg-[hsl(var(--bg-surface-hover))]" />

      {/* Content Placeholder */}
      <div className="p-3.5 space-y-3">
        <div className="h-4 bg-[hsl(var(--bg-surface-hover))] rounded w-5/6" />
        <div className="h-3 bg-[hsl(var(--bg-surface-hover))] rounded w-1/2" />

        <div className="pt-2 border-t border-[hsl(var(--border-muted))/0.5] flex items-center justify-between">
          <div className="h-3 bg-[hsl(var(--bg-surface-hover))] rounded w-1/4" />
          <div className="flex gap-2">
            <div className="w-6 h-6 bg-[hsl(var(--bg-surface-hover))] rounded-lg" />
            <div className="w-6 h-6 bg-[hsl(var(--bg-surface-hover))] rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
}
