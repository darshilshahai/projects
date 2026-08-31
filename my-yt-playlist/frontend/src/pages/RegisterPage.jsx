import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Video, User, Mail, Lock, Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);

    if (formData.password !== formData.confirm_password) {
      setErrorMsg('Passwords do not match.');
      return;
    }

    if (formData.password.length < 8) {
      setErrorMsg('Password must be at least 8 characters long.');
      return;
    }

    setIsSubmitting(true);

    try {
      await register({
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
      });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setErrorMsg(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[hsl(var(--bg-app))] px-4 py-12">
      <div className="w-full max-w-md space-y-8 bg-[hsl(var(--bg-surface))] p-8 rounded-2xl border border-[hsl(var(--border-muted))] shadow-2xl">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[hsl(var(--primary))/0.1] text-[hsl(var(--primary))] mb-2">
            <Video className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-[hsl(var(--text-primary))] tracking-tight">
            Create your account
          </h1>
          <p className="text-sm text-[hsl(var(--text-secondary))]">
            Start saving and organizing YouTube videos privately
          </p>
        </div>

        {/* Error Alert Card */}
        {errorMsg && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p>{errorMsg}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-medium text-[hsl(var(--text-secondary))] uppercase tracking-wider mb-2">
              Full Name
            </label>
            <div className="relative">
              <User className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
              <input
                type="text"
                required
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="Darshil Shah"
                className="w-full pl-11 pr-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[hsl(var(--text-secondary))] uppercase tracking-wider mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="user@example.com"
                className="w-full pl-11 pr-4 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[hsl(var(--text-secondary))] uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Minimum 8 characters"
                className="w-full pl-11 pr-11 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] transition-colors"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[hsl(var(--text-secondary))] uppercase tracking-wider mb-2">
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={formData.confirm_password}
                onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                placeholder="Re-enter password"
                className="w-full pl-11 pr-11 py-2.5 bg-[hsl(var(--bg-input))] border border-[hsl(var(--border-muted))] rounded-xl text-[hsl(var(--text-primary))] placeholder-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--border-focus))] focus:ring-2 focus:ring-[hsl(var(--border-focus))/0.2] transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-slate-950 font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-[hsl(var(--primary))/0.2] mt-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Creating Account...</span>
              </>
            ) : (
              <span>Create Account</span>
            )}
          </button>
        </form>

        {/* Footer Link */}
        <p className="text-center text-sm text-[hsl(var(--text-secondary))]">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-medium text-[hsl(var(--primary))] hover:underline transition-all"
          >
            Sign in instead
          </Link>
        </p>
      </div>
    </div>
  );
}
