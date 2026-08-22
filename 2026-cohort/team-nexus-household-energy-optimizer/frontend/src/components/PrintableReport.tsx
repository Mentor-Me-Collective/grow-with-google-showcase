import { formatKwh, type ApplianceBreakdown } from "../lib/calculations";

interface PrintableReportProps {
  score: number;
  baselineLabel: string;
  regionLabel: string;
  formatCost: (value: number) => string;
  userCost: number;
  userKwh: number;
  carbonLbs: number;
  userBreakdown: ApplianceBreakdown[];
  hogs: ApplianceBreakdown[];
}

export function PrintableReport({
  score,
  baselineLabel,
  regionLabel,
  formatCost,
  userCost,
  userKwh,
  carbonLbs,
  userBreakdown,
  hogs,
}: PrintableReportProps) {
  const generatedOn = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="print-report">
      <div className="print-report-header">
        <img src="/favicon.svg" alt="" width={28} height={27} />
        <div>
          <div className="print-report-title">Tenant Power Tracker, Energy Report</div>
          <div className="print-report-meta">
            Generated {generatedOn} &middot; benchmarked against {baselineLabel} &middot;{" "}
            {regionLabel} rates
          </div>
        </div>
      </div>

      <div className="print-stats">
        <div>
          <span>Energy Score</span>
          <strong>{score}/100</strong>
        </div>
        <div>
          <span>Monthly cost</span>
          <strong>{formatCost(userCost)}</strong>
        </div>
        <div>
          <span>Monthly usage</span>
          <strong>{formatKwh(userKwh)}</strong>
        </div>
        <div>
          <span>Carbon footprint</span>
          <strong>{carbonLbs.toFixed(0)} lbs CO2</strong>
        </div>
      </div>

      <div className="print-section-title">Usage by appliance</div>
      <table className="print-table">
        <thead>
          <tr>
            <th>Appliance</th>
            <th>Qty</th>
            <th>Hours/day</th>
            <th>kWh/mo</th>
            <th>Cost/mo</th>
          </tr>
        </thead>
        <tbody>
          {userBreakdown.map((item) => (
            <tr key={item.appliance.id}>
              <td>{item.appliance.label}</td>
              <td>{item.appliance.quantity ?? 1}</td>
              <td>{item.hours > 0 && item.hours < 1 ? item.hours.toFixed(2) : item.hours.toFixed(0)}</td>
              <td>{item.kwh.toFixed(0)}</td>
              <td>{formatCost(item.cost)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="print-section-title">Top energy hogs &amp; tips</div>
      <ol className="print-hogs">
        {hogs.map((hog) => (
          <li key={hog.appliance.id}>
            <strong>{hog.appliance.label}</strong>, {formatKwh(hog.kwh)},{" "}
            {formatCost(hog.cost)}/mo
            <p>{hog.appliance.tip}</p>
          </li>
        ))}
      </ol>

      <p className="print-disclaimer">
        Figures are estimates benchmarked against sample EIA.gov usage data, not a
        live utility feed.
      </p>
    </div>
  );
}
