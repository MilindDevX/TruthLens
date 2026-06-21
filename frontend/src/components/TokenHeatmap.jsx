/**
 * Token Heatmap — explainability visualization.
 *
 * Renders influential tokens as colored pills:
 * - Red (positive impact → pushes "fake")
 * - Green (negative impact → pushes "real")
 * - Opacity proportional to |impact| magnitude
 * - Hover tooltip with exact score
 */

import { useState } from 'react';

export default function TokenHeatmap({ tokens = [], type = 'shap' }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  if (!tokens || tokens.length === 0) {
    return (
      <div className="text-sm text-slate-500 italic">
        No explainability data available
      </div>
    );
  }

  // Normalize impacts for opacity scaling
  const maxImpact = Math.max(...tokens.map((t) => Math.abs(t.impact)), 0.001);

  const typeLabels = {
    shap: { label: 'SHAP', color: 'text-accent-cyan' },
    attention: { label: 'Attention', color: 'text-accent-violet' },
    lime: { label: 'LIME', color: 'text-amber-400' },
  };
  const typeInfo = typeLabels[type] || typeLabels.shap;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className={`text-xs font-bold uppercase tracking-wider ${typeInfo.color}`}>
          {typeInfo.label}
        </span>
        <span className="text-xs text-slate-500">Influential Tokens</span>
      </div>

      {/* Token pills */}
      <div className="flex flex-wrap gap-2">
        {tokens.map((token, idx) => {
          const isFake = token.impact > 0;
          const normalizedOpacity = Math.abs(token.impact) / maxImpact;
          const opacity = 0.3 + normalizedOpacity * 0.7; // Min 30%, max 100%

          return (
            <div
              key={idx}
              className="relative"
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <span
                className={`inline-block px-3 py-1.5 rounded-lg text-sm font-medium cursor-default transition-all duration-200
                  ${isFake
                    ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  }
                  ${hoveredIdx === idx ? 'scale-110 shadow-lg z-10' : ''}
                `}
                style={{ opacity }}
              >
                {token.token}
              </span>

              {/* Tooltip */}
              {hoveredIdx === idx && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-slate-800 border border-border-glass rounded-lg text-xs whitespace-nowrap z-20 animate-fade-in shadow-lg">
                  <span className="text-slate-400">Impact: </span>
                  <span className={isFake ? 'text-red-400' : 'text-emerald-400'}>
                    {token.impact > 0 ? '+' : ''}{token.impact.toFixed(4)}
                  </span>
                  <span className="text-slate-500 ml-1">
                    ({isFake ? '→ fake' : '→ real'})
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-slate-500 pt-1">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-red-500/40" /> Pushes "fake"
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-emerald-500/40" /> Pushes "real"
        </span>
        <span className="text-slate-600">Opacity ∝ magnitude</span>
      </div>
    </div>
  );
}
