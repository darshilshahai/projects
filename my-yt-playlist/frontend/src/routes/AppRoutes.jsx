import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import GuestRoute from './GuestRoute';
import AppLayout from '../layouts/AppLayout';
import { Loader2 } from 'lucide-react';

// Lazy-loaded page components for optimal bundle splitting
const LoginPage = lazy(() => import('../pages/LoginPage'));
const RegisterPage = lazy(() => import('../pages/RegisterPage'));
const DashboardPage = lazy(() => import('../pages/DashboardPage'));
const LibraryPage = lazy(() => import('../pages/LibraryPage'));
const FavouritesPage = lazy(() => import('../pages/FavouritesPage'));
const WatchLaterPage = lazy(() => import('../pages/WatchLaterPage'));
const WatchedPage = lazy(() => import('../pages/WatchedPage'));
const CollectionsPage = lazy(() => import('../pages/CollectionsPage'));
const CollectionDetailPage = lazy(() => import('../pages/CollectionDetailPage'));
const TagsPage = lazy(() => import('../pages/TagsPage'));
const ProfilePage = lazy(() => import('../pages/ProfilePage'));

// Fallback spinner during route chunk loading
function RouteLoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Loader2 className="w-8 h-8 animate-spin text-[hsl(var(--primary))]" />
    </div>
  );
}

export default function AppRoutes({ onOpenAddModal }) {
  return (
    <Suspense fallback={<RouteLoadingFallback />}>
      <Routes>
        {/* Root redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* Guest Authentication Routes */}
        <Route
          path="/login"
          element={
            <GuestRoute>
              <LoginPage />
            </GuestRoute>
          }
        />
        <Route
          path="/register"
          element={
            <GuestRoute>
              <RegisterPage />
            </GuestRoute>
          }
        />

        {/* Protected Application Layout & Pages */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout onOpenAddModal={onOpenAddModal} />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage onOpenAddModal={onOpenAddModal} />} />
          <Route path="/library" element={<LibraryPage onOpenAddModal={onOpenAddModal} />} />
          <Route path="/favourites" element={<FavouritesPage onOpenAddModal={onOpenAddModal} />} />
          <Route path="/watch-later" element={<WatchLaterPage onOpenAddModal={onOpenAddModal} />} />
          <Route path="/watched" element={<WatchedPage onOpenAddModal={onOpenAddModal} />} />
          <Route path="/collections" element={<CollectionsPage />} />
          <Route path="/collections/:id" element={<CollectionDetailPage onOpenAddModal={onOpenAddModal} />} />
          <Route path="/tags" element={<TagsPage onOpenAddModal={onOpenAddModal} />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>

        {/* 404 Fallback */}
        <Route
          path="*"
          element={
            <div className="min-h-screen flex items-center justify-center bg-[hsl(var(--bg-app))] text-[hsl(var(--text-primary))]">
              <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold text-[hsl(var(--primary))]">404</h1>
                <p className="text-lg text-[hsl(var(--text-secondary))]">Page Not Found</p>
              </div>
            </div>
          }
        />
      </Routes>
    </Suspense>
  );
}
