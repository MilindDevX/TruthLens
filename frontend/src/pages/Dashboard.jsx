/**
 * Dashboard — main analysis page.
 * Text input → analyze → live results with explainability.
 */

import { useState } from 'react';
import { analyzeAPI } from '../api/endpoints';
import CredibilityGauge from '../components/CredibilityGauge';
import TokenHeatmap from '../components/TokenHeatmap';
import ModelComparison from '../components/ModelComparison';

export default function Dashboard() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setError('');
    setLoading(true);
    setResult(null);

    try {
      const data = await analyzeAPI.text(text);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleAnalyze();
    }
  };

  const charCount = text.length;
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const isFake = result?.prediction === 'fake';

  return (
    <div className="page-container">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-100 to-accent-cyan bg-clip-text text-transparent">
            Analyze Content
          </h1>
          <p className="text-slate-400 mt-1">Paste text to check for misinformation or AI-generated content</p>
        </div>

        {/* Input Area */}
        <div className="glass-card mb-6 animate-slide-up">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            className="input-glass resize-y min-h-[180px] leading-relaxed"
            placeholder="Paste a news article, social media post, or any text you want to verify…"
            maxLength={30000}
          />

          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span>{wordCount.toLocaleString()} words</span>
              <span>{charCount.toLocaleString()} / 30,000 chars</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-600">⌘+Enter</span>
              <button
                onClick={handleAnalyze}
                disabled={loading || !text.trim()}
                className="btn-gradient px-8"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analyzing…
                  </span>
                ) : (
                  '🔍 Analyze'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="px-5 py-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-6 animate-fade-in">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6 animate-slide-up">
            {/* Verdict Banner */}
            <div
              className={`glass-card flex items-center gap-6 border-l-4 ${isFake ? 'border-l-red-500' : 'border-l-emerald-500'
                }`}
            >
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`text-2xl font-bold ${isFake ? 'text-red-400' : 'text-emerald-400'}`}>
                    {result.prediction.toUpperCase()}
                  </span>
                  <span className={isFake ? 'badge-fake' : 'badge-real'}>
                    {Math.round(result.confidence * 100)}% confidence
                  </span>
                  {result.low_confidence_flag && (
                    <span className="badge-warning">⚠ Low Confidence</span>
                  )}
                </div>
                <p className="text-xs text-slate-500 leading-relaxed max-w-xl">
                  {result.disclaimer}
                </p>
              </div>
              <CredibilityGauge score={result.credibility_score} size={120} />
            </div>

            {/* Model Comparison */}
            <div>
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Model Breakdown
              </h3>
              <ModelComparison modelScores={result.model_scores} />
            </div>

            {/* Explainability */}
            {result.explainability && (
              <div className="glass-card">
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
                  Why This Prediction?
                </h3>
                <TokenHeatmap
                  tokens={result.explainability.influential_tokens}
                  type={result.explainability.type}
                />
              </div>
            )}

            {/* Metadata */}
            <div className="flex items-center gap-4 text-xs text-slate-500 px-1">
              <span>Model: {result.model_version}</span>
              <span>·</span>
              <span>ID: {result.id?.slice(0, 8)}</span>
              <span>·</span>
              <span>{new Date(result.created_at).toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
