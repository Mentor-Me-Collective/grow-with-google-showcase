import { TrendingDown, TrendingUp, type LucideIcon } from "lucide-react";
import type { StatDelta } from "../lib/calculations";

interface StatTileProps {
  icon: LucideIcon;
  label: string;
  value: string;
  delta?: StatDelta;
}

export function StatTile({ icon: Icon, label, value, delta }: StatTileProps) {
  const DeltaIcon = delta?.direction === "up" ? TrendingUp : TrendingDown;
  return (
    <div className="card stat-tile">
      <Icon className="stat-icon" size={20} strokeWidth={1.75} />
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {delta && (
        <div
          className="stat-delta"
          style={{ color: delta.isGood ? "var(--status-good)" : "var(--status-critical)" }}
        >
          <DeltaIcon size={13} strokeWidth={2} />
          {delta.text}
        </div>
      )}
    </div>
  );
}
