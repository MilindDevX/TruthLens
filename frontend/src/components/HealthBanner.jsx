/**
 * HealthBanner — polls the backend /health endpoint and shows
 * a warning banner if the server is unreachable.
 *
 * Design:
 * - Polls every 30s (configurable)
 * - Shows a sticky amber banner on failure
 * - Auto-hides when connection is restored
 * - Doesn't block the UI (non-modal)
 */

import { useState, useEffect, useRef } from 'react';

const HEALTH_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1')
  .replace('/api/v1', '/health');
const POLL_INTERVAL = 30_000;

export default function HealthBanner() {
  const [status, setStatus] = useState('ok'); // 'ok' | 'degraded' | 'down'
  const [retryIn, setRetryIn] = useState(0);
  const timerRef = useRef(null);
  const countdownRef = useRef(null);

  const checkHealth = async () => {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(HEALTH_URL, { signal: controller.signal });
      clearTimeout(timeout);

      if (res.ok) {
        const data = await res.json();
        setStatus(data.status === 'healthy' ? 'ok' : 'degraded');
      } else {
        setStatus('degraded');
      }
    } catch {
      setStatus('down');
    }
  };

  useEffect(() => {
    checkHealth();
    timerRef.current = setInterval(checkHealth, POLL_INTERVAL);
    return () => clearInterval(timerRef.current);
  }, []);

  // Countdown timer for visual feedback
  useEffect(() => {
    if (status !== 'ok') {
      setRetryIn(Math.round(POLL_INTERVAL / 1000));
      countdownRef.current = setInterval(() => {
        setRetryIn((prev) => (prev <= 1 ? Math.round(POLL_INTERVAL / 1000) : prev - 1));
      }, 1000);
    } else {
      setRetryIn(0);
      clearInterval(countdownRef.current);
    }
    return () => clearInterval(countdownRef.current);
  }, [status]);

  const handleRetryNow = () => {
    checkHealth();
    setRetryIn(Math.round(POLL_INTERVAL / 1000));
  };

  if (status === 'ok') return null;

  const isDown = status === 'down';
  const bgClass = isDown
    ? 'bg-red-500/10 border-red-500/30'
    : 'bg-amber-500/10 border-amber-500/30';
  const textClass = isDown ? 'text-red-400' : 'text-amber-400';
  const icon = isDown ? '🔴' : '🟡';

  return (
    <div
      id="health-banner"
      className={`sticky top-0 z-50 px-4 py-2.5 border-b backdrop-blur-xl transition-all duration-300 ${bgClass}`}
      role="alert"
    >
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="text-sm">{icon}</span>
          <span className={`text-sm font-medium ${textClass}`}>
            {isDown
              ? 'Backend unreachable — some features may not work'
              : 'Backend responding slowly — results may be delayed'}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">
            Retry in {retryIn}s
          </span>
          <button
            onClick={handleRetryNow}
            className="text-xs font-medium text-slate-300 hover:text-white transition-colors px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10"
          >
            Retry Now
          </button>
        </div>
      </div>
    </div>
  );
}
