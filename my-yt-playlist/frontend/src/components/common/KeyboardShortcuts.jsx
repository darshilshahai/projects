import React, { useEffect } from 'react';

export default function KeyboardShortcuts({ onOpenAddModal }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Cmd+K or Ctrl+K or Cmd+N to open Add Video Modal
      if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'n')) {
        e.preventDefault();
        onOpenAddModal();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onOpenAddModal]);

  return null;
}
