import React, { useState } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import AppRoutes from './routes/AppRoutes';
import AddVideoModal from './components/video/AddVideoModal';
import KeyboardShortcuts from './components/common/KeyboardShortcuts';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export default function App() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <KeyboardShortcuts onOpenAddModal={() => setIsAddModalOpen(true)} />
          <AppRoutes onOpenAddModal={() => setIsAddModalOpen(true)} />
          <AddVideoModal
            isOpen={isAddModalOpen}
            onClose={() => setIsAddModalOpen(false)}
          />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
