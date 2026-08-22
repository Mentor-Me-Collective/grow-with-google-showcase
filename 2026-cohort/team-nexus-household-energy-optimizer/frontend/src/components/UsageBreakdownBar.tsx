import { useState } from "react";
import { formatKwh, type ApplianceBreakdown } from "../lib/calculations";
import { getApplianceColor } from "../lib/applianceColors";

interface UsageBreakdownBarProps {
  breakdown: ApplianceBreakdown[];
}

export function UsageBreakdownBar({ breakdown }: UsageBreakdownBarProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const total = breakdown.reduce((sum, item) => sum + item.kwh, 0);
  const active = breakdown.find((item) => item.appliance.id === activeId) ?? null;
  const activeShare = active && total > 0 ? active.kwh / total : 0;

  return (
    <div className="card">
      <div className="card-title">Usage breakdown</div>
      <p className="card-subtitle">Share of your total monthly kWh by appliance.</p>
      <div className="breakdown-bar" role="group" aria-label="Usage breakdown by appliance">
        {breakdown.map((item) => {
          const share = total > 0 ? item.kwh / total : 0;
          if (share <= 0) return null;
          const isActive = activeId === item.appliance.id;
          return (
            <button
              key={item.appliance.id}
              type="button"
              className={`breakdown-segment${isActive ? " is-active" : activeId ? " is-dimmed" : ""}`}
              style={{ width: `${share * 100}%`, background: getApplianceColor(item.appliance.id) }}
              onMouseEnter={() => setActiveId(item.appliance.id)}
              onMouseLeave={() => setActiveId(null)}
              onFocus={() => setActiveId(item.appliance.id)}
              onBlur={() => setActiveId(null)}
              aria-label={`${item.appliance.label}: ${Math.round(share * 100)}% of usage, ${formatKwh(item.kwh)} per month`}
            />
          );
        })}
      </div>

      {/* Visible on-page label, not just a native tooltip, so identity never depends on color alone. */}
      <p className="breakdown-callout" aria-live="polite">
        {active
          ? `${active.appliance.label} — ${Math.round(activeShare * 100)}% of usage (${formatKwh(active.kwh)}/mo)`
          : "Hover or tab through a segment below to see which appliance it is."}
      </p>

      <div className="breakdown-legend">
        {breakdown.map((item) => {
          const share = total > 0 ? item.kwh / total : 0;
          const isActive = activeId === item.appliance.id;
          return (
            <button
              key={item.appliance.id}
              type="button"
              className={`legend-item legend-item-interactive${isActive ? " is-active" : ""}`}
              onMouseEnter={() => setActiveId(item.appliance.id)}
              onMouseLeave={() => setActiveId(null)}
              onFocus={() => setActiveId(item.appliance.id)}
              onBlur={() => setActiveId(null)}
            >
              <span className="legend-swatch" style={{ background: getApplianceColor(item.appliance.id) }} />
              {item.appliance.label.split(" (")[0]}
              <span className="breakdown-pct">{Math.round(share * 100)}%</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
