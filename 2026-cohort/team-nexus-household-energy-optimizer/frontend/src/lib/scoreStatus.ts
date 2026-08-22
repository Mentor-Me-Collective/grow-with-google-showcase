export interface ScoreStatus {
  color: string;
  label: string;
}

export function scoreStatus(score: number): ScoreStatus {
  if (score >= 80) return { color: "var(--status-good)", label: "Better than baseline" };
  if (score >= 50) return { color: "var(--status-warning)", label: "Room to improve" };
  return { color: "var(--status-critical)", label: "High usage" };
}
