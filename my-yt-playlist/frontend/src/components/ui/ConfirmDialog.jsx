import React from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isDangerous = false,
  isLoading = false,
  onConfirm,
  onCancel,
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
        onClick={onCancel}
      />

      {/* Modal Dialog Box */}
      <div className="relative w-full max-w-md bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl shadow-2xl p-6 space-y-6 z-10 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-start gap-4">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              isDangerous
                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                : 'bg-[hsl(var(--primary))/0.15] text-[hsl(var(--primary))]'
            }`}
          >
            <AlertTriangle className="w-5 h-5" />
          </div>

          <div className="space-y-1">
            <h3 className="text-lg font-bold text-[hsl(var(--text-primary))]">{title}</h3>
            <p className="text-sm text-[hsl(var(--text-secondary))] leading-relaxed">
              {message}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-[hsl(var(--text-secondary))] hover:text-[hsl(var(--text-primary))] hover:bg-[hsl(var(--bg-surface-hover))] rounded-xl transition-colors disabled:opacity-50"
          >
            {cancelText}
          </button>

          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl transition-all disabled:opacity-50 shadow-md ${
              isDangerous
                ? 'bg-red-500 hover:bg-red-600 text-white shadow-red-500/20'
                : 'bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 shadow-[hsl(var(--primary))/0.2]'
            }`}
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>{confirmText}</span>}
          </button>
        </div>
      </div>
    </div>
  );
}
