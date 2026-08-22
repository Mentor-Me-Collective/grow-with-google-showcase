import type { ApplianceBreakdown } from "../lib/calculations";
import { formatKwh } from "../lib/calculations";
import { getApplianceColor } from "../lib/applianceColors";
import { getApplianceIcon } from "./applianceIcons";

interface TopHogsCardProps {
  hogs: ApplianceBreakdown[];
  formatCost: (value: number) => string;
}

export function TopHogsCard({ hogs, formatCost }: TopHogsCardProps) {
  if (hogs.length === 0) {
    return (
      <p className="muted-note">
        No appliances tracked yet, add one on the Simulator page to see your top energy hogs.
      </p>
    );
  }

  return (
    <div className="hogs-grid">
      {hogs.map((hog, index) => {
        const Icon = getApplianceIcon(hog.appliance.id, hog.appliance.category);
        const color = getApplianceColor(hog.appliance.id);
        return (
          <div className="card hog-card" key={hog.appliance.id}>
            <div className="hog-card-top">
              <span className="hog-rank">{index + 1}</span>
              <span
                className="hog-card-icon"
                style={{ background: `color-mix(in srgb, ${color} 16%, transparent)`, color }}
              >
                <Icon size={18} strokeWidth={1.75} />
              </span>
            </div>
            <div className="hog-card-name">{hog.appliance.label}</div>
            <div className="hog-card-metric">
              {formatKwh(hog.kwh)} &middot; {formatCost(hog.cost)}/mo
            </div>
            <p className="hog-card-tip">{hog.appliance.tip}</p>
          </div>
        );
      })}
    </div>
  );
}
