import React from 'react';
import { Tag as TagIcon, X } from 'lucide-react';

export default function TagChip({ tag, isSelected = false, onClick, onDelete }) {
  return (
    <div
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer select-none ${
        isSelected
          ? 'bg-[hsl(var(--primary))] text-slate-950 shadow-sm'
          : 'bg-[hsl(var(--bg-surface))] text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] border border-[hsl(var(--border-muted))]'
      }`}
    >
      <TagIcon className="w-3.5 h-3.5" />
      <span>#{tag.name}</span>
      {tag.usage_count !== undefined && (
        <span
          className={`px-1.5 py-0.2 rounded-md font-mono text-[10px] ${
            isSelected ? 'bg-slate-950/20 text-slate-950' : 'bg-[hsl(var(--bg-input))] text-[hsl(var(--text-muted))]'
          }`}
        >
          {tag.usage_count}
        </span>
      )}
      {onDelete && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(tag);
          }}
          title="Delete Tag"
          className="ml-1 hover:text-red-400 transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
