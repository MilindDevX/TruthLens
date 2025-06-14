/**
 * History list item card — compact analysis result preview.
 */

import { Link } from 'react-router-dom';

export default function AnalysisCard({ item }) {
  const isFake = item.prediction === 'fake';
  const confidence = Math.round(item.confidence * 100);
  const credibility = Math.round(item.credibility_score * 100);
  const date = new Date(item.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <Link
      to={`/analysis/${item.id}`}
      className="glass-card block group no-underline"
    >
      <div className="flex items-start justify-between gap-4">
        {/* Left: preview + metadata */}
        <div className="flex-1 min-w-0">
          <p className="text-sm text-slate-300 line-clamp-2 leading-relaxed">
            {item.input_preview}
          </p>
          <div className="flex items-center gap-3 mt-3">
            <span className="text-xs text-slate-500">{date}</span>
            <span className="text-xs text-slate-600">·</span>
            <span className="text-xs text-slate-500">v{item.model_version}</span>
            {item.low_confidence_flag && (
              <span className="badge-warning text-[10px] px-2 py-0.5">Low Confidence</span>
            )}
          </div>
        </div>

        {/* Right: verdict + credibility */}
        <div className="flex flex-col items-end gap-2 shrink-0">
          <span className={isFake ? 'badge-fake' : 'badge-real'}>
            {item.prediction.toUpperCase()}
          </span>
          <div className="flex items-center gap-1.5">
            <div className="w-12 h-1.5 bg-white/5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${credibility > 70
                    ? 'bg-emerald-500'
                    : credibility > 40
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                  }`}
                style={{ width: `${credibility}%` }}
              />
            </div>
            <span className="text-xs text-slate-400 font-medium">{credibility}%</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
