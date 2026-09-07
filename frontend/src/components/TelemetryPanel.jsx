const rows = [
  ['SOURCE TRACE', 'PUBLISHED', 'verified'],
  ['CLAIM REVIEW', 'PENDING', 'review'],
  ['MODEL SIGNAL', 'BASELINE', 'neutral'],
];

export default function TelemetryPanel() {
  return (
    <aside className="telemetry-panel" aria-label="TruthLens evidence telemetry">
      <div className="telemetry-panel__head">
        <span>TL / EVIDENCE TRACE</span>
        <span className="telemetry-panel__live">LIVE</span>
      </div>
      <div className="telemetry-panel__signal" aria-hidden="true">
        <i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i />
      </div>
      <div className="telemetry-panel__rows">
        {rows.map(([label, value, tone], index) => (
          <div className="telemetry-panel__row" key={label}>
            <span>0{index + 1}</span>
            <span>{label}</span>
            <strong data-tone={tone}>{value}</strong>
          </div>
        ))}
      </div>
      <p>External evidence is kept separate from model estimates.</p>
    </aside>
  );
}
