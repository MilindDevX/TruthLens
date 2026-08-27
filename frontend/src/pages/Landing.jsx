/**
 * Landing page — hero, stats, how-it-works, feature cards, footer.
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

const stats = [
  { value: '91.3%', label: 'F1-Score', detail: 'DistilBERT fine-tuned' },
  { value: '<300ms', label: 'Inference', detail: 'CPU — no GPU needed' },
  { value: '10K', label: 'Training Samples', detail: 'Balanced dataset' },
  { value: '93.1%', label: 'Accuracy', detail: 'Multi-genre tested' },
];

const steps = [
  {
    num: '01',
    title: 'Paste Text',
    desc: 'Drop any article, post, or message you want to verify.',
    icon: '📝',
  },
  {
    num: '02',
    title: 'AI Analysis',
    desc: 'Dual-model inference with baseline + transformer ensemble.',
    icon: '⚡',
  },
  {
    num: '03',
    title: 'Get Explanation',
    desc: 'Token-level heatmap shows exactly why the text was flagged.',
    icon: '🔬',
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
          TruthLens uses multi-model AI to detect misinformation, identify AI-generated content,
          and provide transparent explanations for every prediction.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link
            to={isAuthenticated ? '/dashboard' : '/register'}
            className="btn-gradient text-base px-8 py-3.5"
          >
            Start Analyzing →
          </Link>
          <a
            href="#how-it-works"
            className="btn-ghost text-base px-8 py-3.5"
          >
            How It Works
          </a>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="pb-16 animate-slide-up" style={{ animationDelay: '100ms', animationFillMode: 'both' }}>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {stats.map((s) => (
            <div key={s.label} className="glass-card text-center py-5 px-3">
              <p className="text-2xl sm:text-3xl font-black bg-gradient-to-r from-accent-cyan to-accent-violet bg-clip-text text-transparent">
                {s.value}
              </p>
              <p className="text-sm font-semibold text-slate-200 mt-1">{s.label}</p>
              <p className="text-xs text-slate-500 mt-0.5">{s.detail}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="pb-20">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-100">How It Works</h2>
          <p className="text-slate-400 mt-2 max-w-lg mx-auto">Three steps from suspicion to certainty</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {steps.map((step, i) => (
            <div
              key={step.num}
              className="relative glass-card text-center animate-slide-up"
              style={{ animationDelay: `${i * 120}ms`, animationFillMode: 'both' }}
            >
              <span className="text-4xl mb-3 block">{step.icon}</span>
              <span className="absolute top-4 right-5 text-xs font-bold text-accent-cyan/40 tracking-wider">
                {step.num}
              </span>
              <h3 className="text-base font-semibold text-slate-100 mb-2">{step.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{step.desc}</p>

              {/* Connector line (hidden on last) */}
              {i < steps.length - 1 && (
                <div className="hidden sm:block absolute top-1/2 -right-3 w-6 border-t border-dashed border-border-glass" />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Feature Cards */}
      <section id="features" className="pb-20">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-100">Core Capabilities</h2>
          <p className="text-slate-400 mt-2 max-w-lg mx-auto">Production-grade AI with explainability built in</p>
        </div>
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
      <section className="text-center pb-8 border-t border-border-glass pt-12">
        <p className="text-xs text-slate-500 uppercase tracking-widest mb-4">Built With</p>
        <div className="flex items-center justify-center gap-4 sm:gap-8 text-slate-500 text-sm font-medium flex-wrap">
          <span>FastAPI</span>
          <span className="text-border-glass">·</span>
          <span>DistilBERT</span>
          <span className="text-border-glass">·</span>
          <span>SHAP</span>
          <span className="text-border-glass">·</span>
          <span>React</span>
          <span className="text-border-glass">·</span>
          <span>PyTorch</span>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border-glass pt-8 pb-10">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-accent-cyan to-accent-violet flex items-center justify-center text-white font-bold text-[10px]">
              TL
            </div>
            <span className="text-sm text-slate-400">
              © {new Date().getFullYear()} TruthLens. Built by{' '}
              <a
                href="https://github.com/MilindDevX"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-cyan hover:text-accent-violet transition-colors"
              >
                Milind Bansal
              </a>
            </span>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/MilindDevX/TruthLens"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-slate-500 hover:text-accent-cyan transition-colors"
            >
              GitHub →
            </a>
            <a
              href="https://www.linkedin.com/in/milind-bansal-177606244/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-slate-500 hover:text-accent-cyan transition-colors"
            >
              LinkedIn →
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
