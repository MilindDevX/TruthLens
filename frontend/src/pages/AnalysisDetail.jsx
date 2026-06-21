/**
 * Full analysis detail page with explainability visualization.
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { historyAPI } from '../api/endpoints';
import CredibilityGauge from '../components/CredibilityGauge';
import TokenHeatmap from '../components/TokenHeatmap';
import ModelComparison from '../components/ModelComparison';

export default function AnalysisDetail() {
  const { id } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadAnalysis();
  }, [id]);

  const loadAnalysis = async () => {
    try {
      const data = await historyAPI.get(id);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analysis');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-border-glass border-t-accent-cyan rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="max-w-2xl mx-auto text-center py-20">
          <p className="text-4xl mb-4">⚠️</p>
          <p className="text-lg text-red-400 font-medium">{error}</p>
          <Link to="/history" className="btn-ghost mt-6 inline-flex">
            ← Back to History
          </Link>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const isFake = result.prediction === 'fake';

  return (
    <div className="page-container">
      <div className="max-w-4xl mx-auto">
        {/* Breadcrumb */}
        <div className="mb-6 animate-fade-in">
          <Link to="/history" className="text-sm text-slate-500 hover:text-accent-cyan transition-colors">
            ← History
          </Link>
        </div>

        {/* Main Result */}
        <div className="space-y-6 animate-slide-up">
          {/* Verdict + Gauge */}
          <div
            className={`glass-card flex flex-col sm:flex-row items-center gap-6 border-l-4 ${isFake ? 'border-l-red-500' : 'border-l-emerald-500'
              }`}
          >
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className={`text-3xl font-bold ${isFake ? 'text-red-400' : 'text-emerald-400'}`}>
                  {result.prediction.toUpperCase()}
                </span>
                <span className={isFake ? 'badge-fake' : 'badge-real'}>
                  {Math.round(result.confidence * 100)}%
                </span>
                {result.low_confidence_flag && (
                  <span className="badge-warning">⚠ Low Confidence</span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-2">
                This is an AI-generated estimate. It does not replace professional fact-checking.
              </p>
            </div>
            <CredibilityGauge score={result.credibility_score} size={140} />
          </div>

          {/* Input Preview */}
          <div className="glass-card">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Analyzed Content
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed whitespace-pre-wrap">
              {result.input_preview}
            </p>
          </div>

          {/* Model Breakdown */}
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
                Explainability — Why This Prediction?
              </h3>
              <TokenHeatmap
                tokens={result.explainability.influential_tokens}
                type={result.explainability.type}
              />
            </div>
          )}

          {/* Metadata Footer */}
          <div className="glass-card bg-surface-glass/50">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-xs text-slate-500 mb-1">Content Type</p>
                <p className="text-sm font-semibold text-slate-200">{result.content_type}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Model Version</p>
                <p className="text-sm font-semibold text-slate-200">{result.model_version}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Analysis ID</p>
                <p className="text-sm font-mono text-slate-200">{result.id?.slice(0, 8)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Date</p>
                <p className="text-sm font-semibold text-slate-200">
                  {new Date(result.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
