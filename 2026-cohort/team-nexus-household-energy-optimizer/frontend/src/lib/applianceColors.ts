/**
 * Fixed per-appliance color assignment, drawn from the app's 8-slot validated
 * categorical palette (index.css --series-*). Deliberately hardcoded, never
 * generated: a categorical palette caps at 8 CVD-safe hues, and with 11
 * built-in appliances 3 pairs necessarily share a hue (Microwave/Air
 * Conditioner, Dishwasher/Washing Machine, LED Lights/Television) - each
 * pair is spread apart in appliance order so they're rarely adjacent
 * segments, and the hover/focus highlight plus legend make identity exact
 * even when two segments do share a color.
 */
const APPLIANCE_COLORS: Record<string, string> = {
  refrigerator: "var(--series-green)",
  "air-conditioner": "var(--series-blue)",
  "washing-machine": "var(--series-magenta)",
  television: "var(--series-yellow)",
  laptop: "var(--series-violet)",
  "gaming-console": "var(--series-orange)",
  microwave: "var(--series-blue)",
  dishwasher: "var(--series-magenta)",
  "led-lights": "var(--series-yellow)",
  "clothes-dryer": "var(--series-aqua)",
  router: "var(--series-red)",
};

/** Custom (user-added) appliances aren't in the fixed set, and share one neutral color. */
const CUSTOM_COLOR = "var(--text-secondary)";

export function getApplianceColor(id: string): string {
  return APPLIANCE_COLORS[id] ?? CUSTOM_COLOR;
}
