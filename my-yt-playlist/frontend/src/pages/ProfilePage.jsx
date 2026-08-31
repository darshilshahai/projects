import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { updateProfileApi, changePasswordApi } from '../api/auth.api';
import { User, Mail, ShieldCheck, Lock, KeyRound, Loader2, AlertCircle, CheckCircle2, LogOut } from 'lucide-react';
import { formatDate } from '../utils/formatters';

export default function ProfilePage() {
  const { user, updateUser, logout } = useAuth();

  // Profile Form State
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [profileSuccessMsg, setProfileSuccessMsg] = useState(null);
  const [profileErrorMsg, setProfileErrorMsg] = useState(null);

  // Security Form State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [securitySuccessMsg, setSecuritySuccessMsg] = useState(null);
  const [securityErrorMsg, setSecurityErrorMsg] = useState(null);

  // Update Profile Submit
  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileErrorMsg(null);
    setProfileSuccessMsg(null);

    const trimmed = fullName.trim();
    if (!trimmed) {
      setProfileErrorMsg('Full name cannot be empty.');
      return;
    }

    setIsUpdatingProfile(true);

    try {
      const updated = await updateProfileApi({ full_name: trimmed });
      updateUser(updated);
      setProfileSuccessMsg('Profile updated successfully!');
      setTimeout(() => setProfileSuccessMsg(null), 3000);
    } catch (err) {
      setProfileErrorMsg(err.message || 'Failed to update profile.');
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  // Change Password Submit
  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setSecurityErrorMsg(null);
    setSecuritySuccessMsg(null);

    if (newPassword !== confirmPassword) {
      setSecurityErrorMsg('New passwords do not match.');
      return;
    }

    if (newPassword.length < 8) {
      setSecurityErrorMsg('New password must be at least 8 characters long.');
      return;
    }

    setIsChangingPassword(true);

    try {
      await changePasswordApi({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSecuritySuccessMsg('Password updated successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setSecuritySuccessMsg(null), 3000);
    } catch (err) {
      if (err.code === 'INVALID_CREDENTIALS') {
        setSecurityErrorMsg('Current password is incorrect.');
      } else {
        setSecurityErrorMsg(err.message || 'Failed to change password.');
      }
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[hsl(var(--text-primary))] tracking-tight flex items-center gap-2.5">
          <User className="w-6 h-6 text-[hsl(var(--primary))]" />
          <span>Profile & Account Settings</span>
        </h1>
        <p className="text-sm text-[hsl(var(--text-secondary))] mt-0.5">
          Manage your personal details and security preferences
        </p>
      </div>

      {/* Overview Card */}
      <div className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl p-6 shadow-md space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[hsl(var(--text-muted))]">
          Account Overview
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
          <div className="bg-[hsl(var(--bg-input))] p-3.5 rounded-xl border border-[hsl(var(--border-muted))/0.5]">
            <span className="text-xs text-[hsl(var(--text-muted))] block">Account Email</span>
            <span className="text-sm font-semibold text-[hsl(var(--text-primary))] truncate block mt-0.5">
              {user?.email}
            </span>
          </div>

          <div className="bg-[hsl(var(--bg-input))] p-3.5 rounded-xl border border-[hsl(var(--border-muted))/0.5]">
            <span className="text-xs text-[hsl(var(--text-muted))] block">Member Since</span>
            <span className="text-sm font-semibold text-[hsl(var(--text-primary))] block mt-0.5">
              {formatDate(user?.created_at)}
            </span>
          </div>

          <div className="bg-[hsl(var(--bg-input))] p-3.5 rounded-xl border border-[hsl(var(--border-muted))/0.5]">
            <span className="text-xs text-[hsl(var(--text-muted))] block">Account Status</span>
            <span className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-400 mt-1">
              <ShieldCheck className="w-4 h-4" />
              <span>Active & Verified</span>
            </span>
          </div>
        </div>
      </div>

      {/* Edit Profile Section */}
      <div className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl p-6 shadow-md space-y-6">
        <h2 className="text-base font-bold text-[hsl(var(--text-primary))]">Personal Information</h2>

        {profileErrorMsg && (
          <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 p-3 rounded-xl border border-red-500/20">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{profileErrorMsg}</span>
          </div>
        )}

        {profileSuccessMsg && (
          <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 p-3 rounded-xl border border-emerald-500/20">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{profileSuccessMsg}</span>
          </div>
        )}

        <form onSubmit={handleProfileSubmit} className="space-y-4 max-w-lg">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-secondary))] mb-2">
              Full Name
            </label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-secondary))] mb-2">
              Email Address (Immutable)
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
              <input
                type="email"
                disabled
                value={user?.email || ''}
                className="w-full pl-10 pr-4 py-2.5 bg-[hsl(var(--bg-input))/0.5] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-muted))] cursor-not-allowed"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isUpdatingProfile || fullName.trim() === user?.full_name}
            className="flex items-center gap-2 px-5 py-2.5 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all disabled:opacity-50 shadow-md shadow-[hsl(var(--primary))/0.2]"
          >
            {isUpdatingProfile ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Update Profile</span>}
          </button>
        </form>
      </div>

      {/* Security & Password Change */}
      <div className="bg-[hsl(var(--bg-surface))] border border-[hsl(var(--border-muted))] rounded-2xl p-6 shadow-md space-y-6">
        <h2 className="text-base font-bold text-[hsl(var(--text-primary))] flex items-center gap-2">
          <KeyRound className="w-5 h-5 text-[hsl(var(--primary))]" />
          <span>Security & Password</span>
        </h2>

        {securityErrorMsg && (
          <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 p-3 rounded-xl border border-red-500/20">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{securityErrorMsg}</span>
          </div>
        )}

        {securitySuccessMsg && (
          <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 p-3 rounded-xl border border-emerald-500/20">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{securitySuccessMsg}</span>
          </div>
        )}

        <form onSubmit={handlePasswordSubmit} className="space-y-4 max-w-lg">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-secondary))] mb-2">
              Current Password
            </label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-secondary))] mb-2">
              New Password
            </label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              className="w-full px-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--text-secondary))] mb-2">
              Confirm New Password
            </label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter new password"
              className="w-full px-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-sm text-[hsl(var(--text-primary))]"
            />
          </div>

          <button
            type="submit"
            disabled={isChangingPassword || !currentPassword || !newPassword}
            className="flex items-center gap-2 px-5 py-2.5 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold text-sm rounded-xl transition-all disabled:opacity-50 shadow-md shadow-[hsl(var(--primary))/0.2]"
          >
            {isChangingPassword ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Change Password</span>}
          </button>
        </form>
      </div>

      {/* Account Danger Zone */}
      <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 space-y-4">
        <h2 className="text-base font-bold text-red-400">Sign Out Session</h2>
        <p className="text-xs text-[hsl(var(--text-secondary))]">
          End your active session on this device. Your refresh tokens will be revoked.
        </p>

        <button
          onClick={logout}
          className="flex items-center gap-2 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white font-semibold text-xs rounded-xl transition-all shadow-md shadow-red-500/20"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out Now</span>
        </button>
      </div>
    </div>
  );
}
