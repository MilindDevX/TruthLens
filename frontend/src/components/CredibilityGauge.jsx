/**
 * Animated SVG radial gauge showing credibility score (0–100%).
 *
 * Color:  red (<40%) → amber (40–70%) → green (>70%)
 * Animation: spring easing on mount.
 */

import { useEffect, useState } from 'react';

const RADIUS = 45;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function getColor(score) {
  if (score < 0.4) return { stroke: '#ef4444', text: 'text-red-400', label: 'Low' };
  if (score < 0.7) return { stroke: '#f59e0b', text: 'text-amber-400', label: 'Medium' };
  return { stroke: '#10b981', text: 'text-emerald-400', label: 'High' };
}

export default function CredibilityGauge({ score = 0, size = 160 }) {
  const [offset, setOffset] = useState(CIRCUMFERENCE);
  const { stroke, text, label } = getColor(score);
  const target = CIRCUMFERENCE - score * CIRCUMFERENCE;
  const percentage = Math.round(score * 100);

  useEffect(() => {
    // Trigger animation after mount
    const timer = setTimeout(() => setOffset(target), 100);
    return () => clearTimeout(timer);
  }, [target]);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox="0 0 100 100"
          className="transform -rotate-90"
        >
          {/* Background track */}
          <circle
            cx="50" cy="50" r={RADIUS}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="8"
          />
          {/* Score arc */}
          <circle
            cx="50" cy="50" r={RADIUS}
            fill="none"
            stroke={stroke}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            style={{
              transition: 'stroke-dashoffset 1s cubic-bezier(0.34, 1.56, 0.64, 1)',
              filter: `drop-shadow(0 0 6px ${stroke}40)`,
            }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${text}`}>{percentage}</span>
          <span className="text-xs text-slate-400 font-medium">/ 100</span>
        </div>
      </div>
      <div className="text-center">
        <span className={`text-sm font-semibold ${text}`}>{label} Credibility</span>
      </div>
    </div>
  );
}
