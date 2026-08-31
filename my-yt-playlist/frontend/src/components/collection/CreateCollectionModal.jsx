import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createCollectionApi, updateCollectionApi } from '../../api/collections.api';
import { X, FolderPlus, Loader2, AlertCircle } from 'lucide-react';

export default function CreateCollectionModal({ isOpen, onClose, collectionToEdit = null }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);

  const queryClient = useQueryClient();

  useEffect(() => {
    if (collectionToEdit) {
      setName(collectionToEdit.name || '');
      setDescription(collectionToEdit.description || '');
    } else {
      setName('');
      setDescription('');
    }
    setErrorMsg(null);
  }, [collectionToEdit, isOpen]);

  const collectionMutation = useMutation({
    mutationFn: (data) => {
      if (collectionToEdit) {
        return updateCollectionApi(collectionToEdit.id, data);
      }
      return createCollectionApi(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setErrorMsg(null);
      onClose();
    },
    onError: (err) => {
      if (err.code === 'DUPLICATE_RESOURCE') {
        setErrorMsg('A collection with this name already exists.');
      } else {
        setErrorMsg(err.message || 'Failed to save collection.');
      }
    },
  });

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrorMsg(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setErrorMsg('Collection name is required.');
      return;
    }

    collectionMutation.mutate({
      name: trimmedName,
      description: description.trim() || undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Box */}
      <div className="relative w-full max-w-md bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl shadow-2xl p-6 space-y-6 z-10 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] flex items-center justify-center">
              <FolderPlus className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[hsl(var(--text-primary))]">
                {collectionToEdit ? 'Edit Collection' : 'New Collection'}
              </h2>
              <p className="text-xs text-[hsl(var(--text-secondary))]">
                Organize videos into custom playlists
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p>{errorMsg}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-secondary))] mb-2">
              Collection Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Python Masterclass, System Design"
              disabled={collectionMutation.isPending}
              className="w-full px-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-secondary))] mb-2">
              Description (Optional)
            </label>
            <textarea
              rows="3"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief summary of videos inside this collection..."
              disabled={collectionMutation.isPending}
              className="w-full px-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all disabled:opacity-50"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={collectionMutation.isPending}
              className="px-4 py-2.5 text-sm font-medium text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] rounded-xl transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={collectionMutation.isPending || !name.trim()}
              className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all disabled:opacity-50 shadow-md shadow-[hsl(var(--primary))/0.2]"
            >
              {collectionMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>{collectionToEdit ? 'Save Changes' : 'Create Collection'}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
