/**
 * Cards for models that actually contributed to this result.
 */

export default function ModelComparison({ modelScores = {} }) {
  const modelDetails = {
    baseline: { label: 'Baseline', desc: 'TF-IDF + Logistic Regression', icon: '📊' },
    advanced: { label: 'Auxiliary', desc: 'Optional secondary model', icon: '🧠' },
  };
  const models = Object.keys(modelScores)
    .filter((key) => modelDetails[key])
    .map((key) => ({ key, ...modelDetails[key] }));

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {models.map(({ key, label, desc, icon }) => {
        const score = modelScores[key];
        if (!score) return null;

        const isFake = score.prediction === 'fake';
        const confidence = Math.round(score.confidence * 100);

        return (
          <div
            key={key}
            className="glass-card flex flex-col gap-3"
          >
            {/* Header */}
            <div className="flex items-center gap-2">
              <span className="text-xl">{icon}</span>
              <div>
                <h4 className="text-sm font-semibold text-slate-200">{label}</h4>
                <p className="text-xs text-slate-500">{desc}</p>
              </div>
            </div>

            {/* Prediction */}
            <div className="flex items-center justify-between">
              <span
                className={`text-lg font-bold ${isFake ? 'text-red-400' : 'text-emerald-400'
                  }`}
              >
                {score.prediction.toUpperCase()}
              </span>
              <span className={isFake ? 'badge-fake' : 'badge-real'}>
                {confidence}%
              </span>
            </div>

            {/* Confidence bar */}
            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out ${isFake ? 'bg-red-500' : 'bg-emerald-500'
                  }`}
                style={{ width: `${confidence}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
