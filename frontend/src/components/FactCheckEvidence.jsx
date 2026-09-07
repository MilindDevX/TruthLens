import { factCheckPresentation } from '../utils/factCheckPresentation';


const toneClasses = {
  positive: 'border-emerald-400/30 bg-emerald-400/5 text-emerald-300',
  neutral: 'border-slate-600/60 bg-slate-800/40 text-slate-200',
  warning: 'border-amber-400/30 bg-amber-400/5 text-amber-200',
};


export default function FactCheckEvidence({ result }) {
  const presentation = factCheckPresentation(result);

  return (
    <section
      aria-live="polite"
      className={`border px-5 py-4 ${toneClasses[presentation.tone]}`}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.16em]">External evidence</p>
      <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
        <div>
          <h3 className="text-base font-semibold">{presentation.title}</h3>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-400">{presentation.detail}</p>
        </div>
        {presentation.url && (
          <a
            href={presentation.url}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 text-sm font-semibold underline decoration-current/40 underline-offset-4 transition-opacity hover:opacity-75 focus:outline-none focus:ring-2 focus:ring-current focus:ring-offset-2 focus:ring-offset-slate-950"
          >
            {presentation.linkLabel}
          </a>
        )}
      </div>
    </section>
  );
}
