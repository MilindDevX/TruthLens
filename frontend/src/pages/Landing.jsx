/**
 * Landing page — hero, stats, how-it-works, feature cards, footer.
 */

import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import TelemetryPanel from '../components/TelemetryPanel';

const features = [
  {
    icon: '🔍',
    title: 'Misinformation Detection',
    desc: 'Baseline TF-IDF analysis for fake-news signals.',
  },
  {
    icon: '🧠',
    title: 'Explainability',
    desc: 'See exactly which words influenced the prediction with SHAP.',
  },
  {
    icon: '📊',
    title: 'Probability Estimate',
    desc: 'See the model’s estimated probability that text is real.',
  },
  {
    icon: '🛡️',
    title: 'Drift Monitoring',
    desc: 'Real-time KL divergence tracking ensures model performance stays calibrated.',
  },
];

const stats = [
  { value: 'TF-IDF', label: 'Model', detail: 'Logistic regression baseline' },
  { value: 'SHAP', label: 'Explanation', detail: 'Token-level signals' },
  { value: 'News', label: 'Scope', detail: 'Fake-news classification' },
  { value: '503', label: 'Safety', detail: 'No result without a model' },
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
    title: 'Model Analysis',
    desc: 'Baseline fake-news classification runs on your text.',
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
      <section className="landing-hero">
        <div className="landing-hero__copy">
          <p className="telemetry-kicker">TRUTHLENS / SIGNAL REVIEW</p>
          <h1>Verify the signal.<br /><em>Keep the evidence.</em></h1>
          <p className="landing-hero__lede">
            A restrained fake-news estimate, an explainable model signal, and published fact checks where they exist.
          </p>
          <div className="flex items-center gap-4 flex-wrap">
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
        </div>
        <TelemetryPanel />
      </section>

      <section className="evidence-ledger" aria-labelledby="evidence-ledger-title">
        <div>
          <p className="telemetry-kicker">METHOD / 01—03</p>
          <h2 id="evidence-ledger-title">Evidence stays<br />in the record.</h2>
        </div>
        <ol>
          <li><span>01</span><div><strong>Signal</strong><p>A baseline model estimates fake-news risk. It is not a final fact verdict.</p></div></li>
          <li><span>02</span><div><strong>Trace</strong><p>Token explanations show what influenced the estimate.</p></div></li>
          <li><span>03</span><div><strong>Review</strong><p>Published ClaimReview evidence is linked separately when available.</p></div></li>
        </ol>
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
          <span>scikit-learn</span>
          <span className="text-border-glass">·</span>
          <span>SHAP</span>
          <span className="text-border-glass">·</span>
          <span>React</span>
          <span className="text-border-glass">·</span>
          <span>Logistic Regression</span>
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
