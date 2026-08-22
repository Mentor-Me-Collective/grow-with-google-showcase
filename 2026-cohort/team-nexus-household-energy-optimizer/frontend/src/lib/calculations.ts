import type { Appliance, BaselineProfile } from "../types";

const DAYS_PER_MONTH = 30;

/** Clamps hours/day input so edge values (0, 24, negatives, NaN) never crash or go negative. */
export function clampHours(hours: number, appliance: Appliance): number {
  if (Number.isNaN(hours)) return appliance.defaultHours;
  return Math.min(appliance.maxHours, Math.max(appliance.minHours, hours));
}

export function monthlyKwh(watts: number, hoursPerDay: number): number {
  return (watts * hoursPerDay * DAYS_PER_MONTH) / 1000;
}

/** Per-unit watts times how many identical units the user has (e.g. 2 TVs). */
export function effectiveWatts(appliance: Appliance): number {
  return appliance.watts * (appliance.quantity ?? 1);
}

export function monthlyCost(kwh: number, rate: number): number {
  return kwh * rate;
}

export function monthlyCarbonLbs(kwh: number, factor: number): number {
  return kwh * factor;
}

export type HoursByCategory = Record<string, number>;

/**
 * Starting-point hours for a home-size profile: uses the profile's own hours
 * for appliances it specifies, and falls back to that appliance's own
 * default for anything the profile doesn't mention (a laptop doesn't stop
 * existing just because a profile forgot to list it).
 */
export function buildProfileHours(appliances: Appliance[], profile: BaselineProfile): HoursByCategory {
  return appliances.reduce((acc, appliance) => {
    acc[appliance.id] = profile.hoursByAppliance[appliance.id] ?? appliance.defaultHours;
    return acc;
  }, {} as HoursByCategory);
}

export interface ApplianceBreakdown {
  appliance: Appliance;
  hours: number;
  kwh: number;
  cost: number;
}

export function buildBreakdown(
  hoursByCategory: HoursByCategory,
  appliances: Appliance[],
  rate: number,
): ApplianceBreakdown[] {
  return appliances.map((appliance) => {
    const hours = clampHours(hoursByCategory[appliance.id], appliance);
    const kwh = monthlyKwh(effectiveWatts(appliance), hours);
    return {
      appliance,
      hours,
      kwh,
      cost: monthlyCost(kwh, rate),
    };
  });
}

export function totalKwh(breakdown: ApplianceBreakdown[]): number {
  return breakdown.reduce((sum, item) => sum + item.kwh, 0);
}

export function topEnergyHogs(breakdown: ApplianceBreakdown[], count = 3): ApplianceBreakdown[] {
  return [...breakdown].sort((a, b) => b.kwh - a.kwh).slice(0, count);
}

/**
 * Score of 1-100 relative to a regional baseline. Matching the baseline
 * lands at 100; every 1% above baseline usage costs one point, floored at 1
 * so it never crashes into zero or negative territory.
 */
export function energyScore(userKwh: number, baselineKwh: number): number {
  if (baselineKwh <= 0) return userKwh <= 0 ? 100 : 1;
  const ratio = userKwh / baselineKwh;
  const raw = 100 - (ratio - 1) * 100;
  return Math.min(100, Math.max(1, Math.round(raw)));
}

export function formatCurrency(value: number, currency = "USD", locale = "en-US"): string {
  return value.toLocaleString(locale, { style: "currency", currency });
}

export function formatKwh(value: number): string {
  return `${value.toLocaleString("en-US", { maximumFractionDigits: 0 })} kWh`;
}

export interface StatDelta {
  text: string;
  isGood: boolean;
  direction: "up" | "down";
}

/** Compares a current value to the default-usage baseline for a stat tile's delta badge. */
export function buildDelta(
  current: number,
  base: number,
  format: (value: number) => string,
): StatDelta {
  const diff = current - base;
  if (Math.abs(diff) < 0.01) {
    return { text: "On par with default", isGood: true, direction: "down" };
  }
  const direction = diff > 0 ? "up" : "down";
  const sign = diff > 0 ? "+" : "-";
  return { text: `${sign}${format(Math.abs(diff))} vs default`, isGood: diff <= 0, direction };
}
