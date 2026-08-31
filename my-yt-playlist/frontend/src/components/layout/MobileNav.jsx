import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Library, Clock, Star, FolderKanban } from 'lucide-react';

export default function MobileNav() {
  const items = [
    { label: 'Dash', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Library', path: '/library', icon: Library },
    { label: 'Later', path: '/watch-later', icon: Clock },
    { label: 'Favs', path: '/favourites', icon: Star },
    { label: 'Folders', path: '/collections', icon: FolderKanban },
  ];

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-[hsl(var(--bg-surface))/0.95] backdrop-blur-md border-t border-[hsl(var(--border-muted))] px-2 py-1 pb-[max(0.25rem,env(safe-area-inset-bottom))] shadow-2xl">
      <div className="flex items-center justify-around max-w-md mx-auto">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center min-h-[44px] min-w-[44px] gap-1 py-1.5 px-3 rounded-xl transition-all touch-manipulation active:scale-95 ${
                  isActive
                    ? 'text-[hsl(var(--primary))] font-bold bg-[hsl(var(--primary))/0.1]'
                    : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))]'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] tracking-tight">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
