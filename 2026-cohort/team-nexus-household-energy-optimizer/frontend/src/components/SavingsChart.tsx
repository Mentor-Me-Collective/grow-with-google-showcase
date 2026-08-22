interface SavingsChartProps {
  defaultCost: number;
  simulatedCost: number;
  formatCost: (value: number) => string;
}

function niceCeiling(value: number): number {
  if (value <= 0) return 25;
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
  const residual = value / magnitude;
  let niceResidual = 10;
  if (residual <= 1) niceResidual = 1;
  else if (residual <= 2) niceResidual = 2;
  else if (residual <= 5) niceResidual = 5;
  return niceResidual * magnitude;
}

const CHART_HEIGHT = 160;
const BAR_WIDTH = 24;

export function SavingsChart({ defaultCost, simulatedCost, formatCost }: SavingsChartProps) {
  const maxValue = niceCeiling(Math.max(defaultCost, simulatedCost) * 1.15);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((fraction) => Math.round(maxValue * fraction));

  const bars = [
    { key: "default", label: "Default usage", value: defaultCost, color: "var(--baseline)" },
    { key: "simulated", label: "Your scenario", value: simulatedCost, color: "var(--series-blue)" },
  ];

  const bandWidth = 140;
  const chartWidth = bandWidth * bars.length + 40;

  return (
    <div className="card">
      <div className="card-title">Savings visualizer</div>
      <p className="card-subtitle">Monthly cost, default appliance usage vs. your scenario.</p>
      <div className="chart-legend">
        {bars.map((bar) => (
          <span className="legend-item" key={bar.key}>
            <span className="legend-swatch" style={{ background: bar.color }} />
            {bar.label}
          </span>
        ))}
      </div>
      <svg
        viewBox={`0 0 ${chartWidth} ${CHART_HEIGHT + 40}`}
        width="100%"
        role="img"
        aria-label={`Default usage costs ${formatCost(defaultCost)} per month. Your scenario costs ${formatCost(simulatedCost)} per month.`}
      >
        {ticks.map((tick) => {
          const y = CHART_HEIGHT - (tick / maxValue) * CHART_HEIGHT + 10;
          return (
            <g key={tick}>
              <line
                x1={40}
                x2={chartWidth}
                y1={y}
                y2={y}
                stroke="var(--gridline)"
                strokeWidth={1}
              />
              <text x={0} y={y + 4} fontSize={11} fill="var(--text-muted)">
                {formatCost(tick).replace(/\.\d+/, "")}
              </text>
            </g>
          );
        })}
        {bars.map((bar, index) => {
          const barHeight = Math.max(0, (bar.value / maxValue) * CHART_HEIGHT);
          const bandX = 40 + index * bandWidth;
          const barX = bandX + (bandWidth - BAR_WIDTH) / 2;
          const barY = CHART_HEIGHT - barHeight + 10;
          return (
            <g key={bar.key} className="chart-bar-group">
              <title>{`${bar.label}: ${formatCost(bar.value)} per month`}</title>
              <rect
                x={barX}
                y={barY}
                width={BAR_WIDTH}
                height={barHeight}
                rx={4}
                fill={bar.color}
              />
              <text
                x={barX + BAR_WIDTH / 2}
                y={barY - 8}
                fontSize={13}
                fontWeight={600}
                textAnchor="middle"
                fill="var(--text-primary)"
              >
                {formatCost(bar.value)}
              </text>
              <text
                x={barX + BAR_WIDTH / 2}
                y={CHART_HEIGHT + 30}
                fontSize={12}
                textAnchor="middle"
                fill="var(--text-secondary)"
              >
                {bar.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
