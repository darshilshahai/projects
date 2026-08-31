import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Library,
  Clock,
  Star,
  CheckCircle2,
  FolderKanban,
  Tag,
  X,
} from 'lucide-react';

export default function Sidebar({ isMobileOpen, onCloseMobile }) {
  const mainNavItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Library', path: '/library', icon: Library },
    { label: 'Watch Later', path: '/watch-later', icon: Clock },
    { label: 'Favourites', path: '/favourites', icon: Star },
    { label: 'Watched History', path: '/watched', icon: CheckCircle2 },
  ];

  const secondaryNavItems = [
    { label: 'Collections', path: '/collections', icon: FolderKanban },
    { label: 'Tags', path: '/tags', icon: Tag },
  ];

  const navLinkClasses = ({ isActive }) =>
    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all ${
      isActive
        ? 'bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] shadow-sm'
        : 'text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))]'
    }`;

  const sidebarContent = (
    <div className="flex flex-col h-full py-4 px-3 space-y-6">
      {/* Mobile Drawer Close Header */}
      <div className="flex items-center justify-between lg:hidden px-2 pb-2 border-b border-[hsl(var(--border-muted))/0.5]">
        <span className="font-bold text-lg text-[hsl(var(--text-primary))]">Navigation</span>
        <button
          onClick={onCloseMobile}
          className="p-1 rounded-lg text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))]"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Main Navigation Section */}
      <div className="space-y-1">
        <p className="px-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-muted))] mb-2">
          Menu
        </p>
        {mainNavItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onCloseMobile}
              className={navLinkClasses}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>

      {/* Organize Section */}
      <div className="space-y-1">
        <p className="px-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-muted))] mb-2">
          Organize
        </p>
        {secondaryNavItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onCloseMobile}
              className={navLinkClasses}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar (Fixed Left) */}
      <aside className="hidden lg:block w-64 shrink-0 bg-[hsl(var(--bg-surface))] border-r border-[hsl(var(--border-muted))] sticky top-[61px] h-[calc(100vh-61px)] overflow-y-auto">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-950/75 backdrop-blur-sm transition-opacity"
            onClick={onCloseMobile}
          />
          <div className="relative flex-1 max-w-xs w-full bg-[hsl(var(--bg-surface))] h-full z-10 border-r border-[hsl(var(--border-muted))] shadow-2xl">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
