/**
 * Paginated analysis history page.
 */

import { useState, useEffect } from 'react';
import { historyAPI } from '../api/endpoints';
import AnalysisCard from '../components/AnalysisCard';

export default function History() {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const limit = 10;

  useEffect(() => {
    loadHistory();
  }, [page]);

  const loadHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await historyAPI.list(page, limit);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="page-container">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8 animate-fade-in">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-100 to-accent-cyan bg-clip-text text-transparent">
              Analysis History
            </h1>
            <p className="text-slate-400 mt-1">
              {total} total {total === 1 ? 'analysis' : 'analyses'}
            </p>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="px-5 py-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-6">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="w-10 h-10 border-2 border-border-glass border-t-accent-cyan rounded-full animate-spin" />
          </div>
        )}

        {/* Empty state */}
        {!loading && items.length === 0 && (
          <div className="text-center py-20 animate-fade-in">
            <p className="text-4xl mb-4">📭</p>
            <p className="text-lg text-slate-400 font-medium">No analyses yet</p>
            <p className="text-sm text-slate-500 mt-1">Go to the dashboard to analyze your first piece of content</p>
          </div>
        )}

        {/* List */}
        {!loading && items.length > 0 && (
          <div className="space-y-4 animate-slide-up">
            {items.map((item) => (
              <AnalysisCard key={item.id} item={item} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-ghost px-4 py-2 text-xs"
            >
              ← Prev
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const p = i + 1;
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-9 h-9 rounded-xl text-sm font-medium transition-all duration-200 ${p === page
                      ? 'bg-gradient-to-br from-accent-cyan to-accent-violet text-white'
                      : 'bg-surface-glass text-slate-400 hover:text-slate-200 border border-border-glass'
                    }`}
                >
                  {p}
                </button>
              );
            })}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-ghost px-4 py-2 text-xs"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
