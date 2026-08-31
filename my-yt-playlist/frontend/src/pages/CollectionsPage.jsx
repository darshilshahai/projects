import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getCollectionsApi, deleteCollectionApi } from '../api/collections.api';
import CreateCollectionModal from '../components/collection/CreateCollectionModal';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { FolderKanban, Plus, Edit2, Trash2, ArrowRight } from 'lucide-react';

export default function CollectionsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [collectionToEdit, setCollectionToEdit] = useState(null);
  const [collectionToDelete, setCollectionToDelete] = useState(null);

  const { data: collections = [], isLoading, isError } = useQuery({
    queryKey: ['collections'],
    queryFn: getCollectionsApi,
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteCollectionApi(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setCollectionToDelete(null);
    },
  });

  const handleEdit = (col, e) => {
    e.stopPropagation();
    setCollectionToEdit(col);
    setIsCreateModalOpen(true);
  };

  const handleDelete = (col, e) => {
    e.stopPropagation();
    setCollectionToDelete(col);
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[hsl(var(--text-primary))] tracking-tight flex items-center gap-2.5">
            <FolderKanban className="w-6 h-6 text-[hsl(var(--primary))]" />
            <span>Custom Collections</span>
          </h1>
          <p className="text-sm text-[hsl(var(--text-secondary))] mt-0.5">
            Organize videos into topic-specific playlists and folders
          </p>
        </div>

        <button
          onClick={() => {
            setCollectionToEdit(null);
            setIsCreateModalOpen(true);
          }}
          className="flex items-center justify-center gap-2 py-2.5 px-4 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all shadow-md shadow-[hsl(var(--primary))/0.2] shrink-0"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>New Collection</span>
        </button>
      </div>

      {/* Grid Area */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div key={idx} className="h-36 bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-xl animate-pulse" />
          ))}
        </div>
      ) : isError ? (
        <div className="p-8 text-center bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400">
          <p className="text-sm font-medium">Failed to load collections.</p>
        </div>
      ) : collections.length === 0 ? (
        <div className="p-12 text-center bg-[hsl(var(--bg-surface))] rounded-2xl border border-[hsl(var(--border-muted))] space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] flex items-center justify-center mx-auto">
            <FolderKanban className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-[hsl(var(--text-primary))]">
              No collections created yet
            </h3>
            <p className="text-sm text-[hsl(var(--text-secondary))] max-w-sm mx-auto">
              Create collections to group related tutorials, podcasts, or interview prep videos.
            </p>
          </div>
          <button
            onClick={() => {
              setCollectionToEdit(null);
              setIsCreateModalOpen(true);
            }}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-[hsl(var(--primary))] text-slate-950 text-xs font-bold rounded-xl"
          >
            <Plus className="w-4 h-4 stroke-[3]" />
            <span>Create Your First Collection</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {collections.map((col) => (
            <div
              key={col.id}
              onClick={() => navigate(`/collections/${col.id}`)}
              className="group bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] hover:border-[hsl(var(--border-focus))] rounded-2xl p-5 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))] flex items-center justify-center group-hover:scale-105 transition-transform">
                    <FolderKanban className="w-5 h-5" />
                  </div>

                  <span className="px-2.5 py-1 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))/0.5] text-[hsl(var(--primary))] font-semibold text-xs rounded-lg">
                    {col.video_count} {col.video_count === 1 ? 'video' : 'videos'}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-base text-[hsl(var(--text-primary))] group-hover:text-[hsl(var(--primary))] transition-colors">
                    {col.name}
                  </h3>
                  {col.description && (
                    <p className="text-xs text-[hsl(var(--text-secondary))] line-clamp-2 mt-1 leading-relaxed">
                      {col.description}
                    </p>
                  )}
                </div>
              </div>

              {/* Action Buttons Footer */}
              <div className="pt-3 border-t border-[hsl(var(--border-muted))/0.5] flex items-center justify-between">
                <span className="flex items-center gap-1 text-xs font-semibold text-[hsl(var(--primary))] group-hover:underline">
                  <span>Open Collection</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>

                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => handleEdit(col, e)}
                    title="Edit Collection"
                    className="p-1.5 rounded-lg text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(col, e)}
                    title="Delete Collection"
                    className="p-1.5 rounded-lg text-[hsl(var(--text-muted))] hover:text-red-400 hover:bg-red-500/10 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Collection Modal */}
      <CreateCollectionModal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setCollectionToEdit(null);
        }}
        collectionToEdit={collectionToEdit}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmDialog
        isOpen={!!collectionToDelete}
        title="Delete Collection"
        message={`Are you sure you want to delete collection "${collectionToDelete?.name}"? Videos inside this collection will not be deleted from your main library.`}
        confirmText="Delete Collection"
        isDangerous={true}
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteMutation.mutate(collectionToDelete.id)}
        onCancel={() => setCollectionToDelete(null)}
      />
    </div>
  );
}
