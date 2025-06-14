/**
 * Lightweight toast notification system.
 * Shows temporary messages at the bottom of the screen.
 *
 * Usage:
 *   import { toast } from './components/Toast';
 *   toast.error('Something went wrong');
 *   toast.success('Analysis complete');
 *   toast.warn('Backend is slow');
 */

import { useState, useEffect, useCallback } from 'react';

let toastListener = null;

// Global toast API (works outside React)
export const toast = {
  _emit(type, message, duration = 4000) {
    toastListener?.({ type, message, duration, id: Date.now() });
  },
  success: (message, duration) => toast._emit('success', message, duration),
  error: (message, duration) => toast._emit('error', message, duration),
  warn: (message, duration) => toast._emit('warn', message, duration),
  info: (message, duration) => toast._emit('info', message, duration),
};

const ICONS = {
  success: '✓',
  error: '✗',
  warn: '⚠',
  info: 'ℹ',
};

const COLORS = {
  success: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
  error: 'bg-red-500/15 border-red-500/30 text-red-400',
  warn: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
  info: 'bg-accent-cyan-dim border-accent-cyan/30 text-accent-cyan',
};

export default function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((t) => {
    setToasts((prev) => [...prev.slice(-4), t]); // max 5 visible
    setTimeout(() => {
      setToasts((prev) => prev.filter((x) => x.id !== t.id));
    }, t.duration);
  }, []);

  useEffect(() => {
    toastListener = addToast;
    return () => { toastListener = null; };
  }, [addToast]);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto px-4 py-3 rounded-xl border backdrop-blur-xl text-sm font-medium shadow-lg
            animate-slide-up ${COLORS[t.type] || COLORS.info}`}
        >
          <span className="mr-2">{ICONS[t.type]}</span>
          {t.message}
        </div>
      ))}
    </div>
  );
}
