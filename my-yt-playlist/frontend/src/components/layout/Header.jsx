import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Video, Search, Plus, Menu } from 'lucide-react';
import UserMenu from './UserMenu';

export default function Header({ onOpenAddModal, onToggleMobileSidebar }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const currentQuery = searchParams.get('q') || '';

  const handleSearchChange = (e) => {
    const value = e.target.value;
    if (value) {
      navigate(`/library?q=${encodeURIComponent(value)}`);
    } else {
      navigate('/library');
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-[hsl(var(--bg-app))/0.9] backdrop-blur-md border-b border-[hsl(var(--border-muted))] px-4 lg:px-8 py-3">
      <div className="flex items-center justify-between gap-4">
        {/* Left: Mobile Menu Toggle & Brand Logo */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleMobileSidebar}
            className="lg:hidden p-2 rounded-xl text-[hsl(var(--text-secondary))] hover:bg-[hsl(var(--bg-surface-hover))] transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-[hsl(var(--primary))] text-slate-950 flex items-center justify-center shadow-lg shadow-[hsl(var(--primary))/0.2] group-hover:scale-105 transition-transform">
              <Video className="w-5 h-5 fill-slate-950" />
            </div>
            <span className="text-lg font-bold text-[hsl(var(--text-primary))] tracking-tight hidden sm:inline">
              My<span className="text-[hsl(var(--primary))]">YT</span>
            </span>
          </div>
        </div>

        {/* Center: Search Bar */}
        <div className="flex-1 max-w-xl mx-2">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
            <input
              type="text"
              defaultValue={currentQuery}
              onChange={handleSearchChange}
              placeholder="Search videos by title, channel, notes..."
              className="w-full pl-10 pr-4 py-2 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all"
            />
          </div>
        </div>

        {/* Right: Add Video CTA & User Menu */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenAddModal}
            className="flex items-center gap-2 py-2 px-3.5 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all shadow-md shadow-[hsl(var(--primary))/0.2]"
          >
            <Plus className="w-4 h-4 stroke-[3]" />
            <span className="hidden sm:inline">Save Video</span>
          </button>

          <UserMenu />
        </div>
      </div>
    </header>
  );
}
