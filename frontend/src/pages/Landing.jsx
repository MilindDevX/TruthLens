/**
 * Landing page — hero section with feature cards and CTA.
 */

import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

const features = [
  {
    icon: '🔍',
    title: 'Misinformation Detection',
    desc: 'Dual-model analysis using TF-IDF baseline and DistilBERT transformer.',
  },
  {
    icon: '🧠',
    title: 'Explainability',
    desc: 'See exactly which words influenced the prediction with SHAP and attention maps.',
  },
  {
    icon: '📊',
    title: 'Credibility Scoring',
    desc: 'Weighted credibility score combining multiple model perspectives.',
  },
  {
    icon: '🛡️',
    title: 'Drift Monitoring',
    desc: 'Real-time KL divergence tracking ensures model performance stays calibrated.',
  },
];

export default function Landing() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="page-container">
      {/* Hero */}
      <section className="text-center pt-16 pb-20 animate-fade-in">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-cyan-dim border border-accent-cyan/20 text-accent-cyan text-xs font-semibold mb-6">
          <span className="w-2 h-2 rounded-full bg-accent-cyan animate-pulse" />
          AI-Powered Content Verification
        </div>
        <h1 className="text-5xl sm:text-6xl font-black leading-tight mb-6">
          <span className="bg-gradient-to-r from-slate-100 via-accent-cyan to-accent-violet bg-clip-text text-transparent">
            Verify Truth.
          </span>
          <br />
          <span className="text-slate-300">
            Expose Deception.
          </span>
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          TruthLens X uses multi-model AI to detect misinformation, identify AI-generated content,
          and provide transparent explanations for every prediction.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            to={isAuthenticated ? '/dashboard' : '/register'}
            className="btn-gradient text-base px-8 py-3.5"
          >
            Start Analyzing →
          </Link>
          <a
            href="#features"
            className="btn-ghost text-base px-8 py-3.5"
          >
            Learn More
          </a>
        </div>
      </section>

      {/* Feature Cards */}
      <section id="features" className="pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map((f, i) => (
            <div
              key={f.title}
              className="glass-card animate-slide-up"
              style={{ animationDelay: `${i * 100}ms`, animationFillMode: 'both' }}
            >
              <span className="text-3xl mb-3 block">{f.icon}</span>
              <h3 className="text-base font-semibold text-slate-100 mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Trust bar */}
      <section className="text-center pb-16 border-t border-border-glass pt-12">
        <p className="text-xs text-slate-500 uppercase tracking-widest mb-4">Built With</p>
        <div className="flex items-center justify-center gap-8 text-slate-500 text-sm font-medium">
          <span>FastAPI</span>
          <span className="text-border-glass">·</span>
          <span>DistilBERT</span>
          <span className="text-border-glass">·</span>
          <span>SHAP</span>
          <span className="text-border-glass">·</span>
          <span>React</span>
        </div>
      </section>
    </div>
  );
}
