import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/layout/Header';
import Sidebar from '../components/layout/Sidebar';
import MobileNav from '../components/layout/MobileNav';

export default function AppLayout({ onOpenAddModal }) {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[hsl(var(--bg-app))] flex flex-col font-sans">
      {/* Top Header Bar */}
      <Header
        onOpenAddModal={onOpenAddModal}
        onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
      />

      {/* Main Content Body */}
      <div className="flex-1 flex">
        {/* Navigation Sidebar */}
        <Sidebar
          isMobileOpen={isMobileSidebarOpen}
          onCloseMobile={() => setIsMobileSidebarOpen(false)}
        />

        {/* Main View Area */}
        <main className="flex-1 min-w-0 pb-20 lg:pb-8">
          <Outlet />
        </main>
      </div>

      {/* Fixed Bottom Mobile Navigation Bar */}
      <MobileNav />
    </div>
  );
}
