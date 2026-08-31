import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { User, Settings, LogOut, ChevronDown } from 'lucide-react';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
    navigate('/login');
  };

  const initial = user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U';

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2.5 p-1.5 rounded-xl hover:bg-[hsl(var(--bg-surface-hover))] transition-colors focus:outline-none"
      >
        <div className="w-8 h-8 rounded-lg bg-[hsl(var(--primary))] text-slate-950 font-bold text-sm flex items-center justify-center shadow-md">
          {initial}
        </div>
        <span className="hidden md:inline text-sm font-medium text-[hsl(var(--text-primary))] max-w-[120px] truncate">
          {user?.full_name || 'Account'}
        </span>
        <ChevronDown className="w-4 h-4 text-[hsl(var(--text-muted))]" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl shadow-2xl py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
          {/* User Info Header */}
          <div className="px-4 py-3 border-b border-[hsl(var(--border-muted))/0.5]">
            <p className="text-sm font-semibold text-[hsl(var(--text-primary))] truncate">
              {user?.full_name}
            </p>
            <p className="text-xs text-[hsl(var(--text-secondary))] truncate mt-0.5">
              {user?.email}
            </p>
          </div>

          {/* Menu Actions */}
          <div className="py-1">
            <Link
              to="/profile"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] transition-colors"
            >
              <User className="w-4 h-4" />
              <span>Profile & Settings</span>
            </Link>
          </div>

          <div className="border-t border-[hsl(var(--border-muted))/0.5] pt-1">
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors text-left"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
