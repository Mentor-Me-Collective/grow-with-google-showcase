import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { scoreStatus } from "../lib/scoreStatus";

interface ScoreSummaryBarProps {
  score: number;
  baselineLabel: string;
}

export function ScoreSummaryBar({ score, baselineLabel }: ScoreSummaryBarProps) {
  const status = scoreStatus(score);

  return (
    <div className="card score-banner">
      <div className="score-banner-left">
        <div className="score-banner-value" style={{ color: status.color }}>
          {score}
        </div>
        <div>
          <div className="score-banner-label">Personalized Energy Score</div>
          <div className="score-banner-sub">vs {baselineLabel}</div>
        </div>
        <span
          className="score-badge"
          style={{
            color: status.color,
            background: `color-mix(in srgb, ${status.color} 14%, transparent)`,
          }}
        >
          {status.label}
        </span>
      </div>
      <Link to="/score" className="btn btn-secondary">
        See your full breakdown
        <ArrowRight size={15} strokeWidth={2} />
      </Link>
    </div>
  );
}
