import type { Appliance, ApplianceCategory, BaselineProfile, Region } from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:5050";

interface ApiAppliance {
  id: string;
  label: string;
  watts: number;
  default_hours: number;
  min_hours: number;
  max_hours: number;
  tip: string;
  category: ApplianceCategory;
}

interface ApiBaselineProfile {
  id: string;
  label: string;
  hours_by_appliance: Record<string, number>;
}

interface ApiRegion {
  id: string;
  label: string;
  rate_per_kwh: number;
  carbon_lbs_per_kwh: number;
  currency: string;
  locale: string;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    throw new Error(`${path} failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchAppliances(): Promise<Appliance[]> {
  const appliances = await getJson<ApiAppliance[]>("/api/simulator/appliances");
  return appliances.map((item) => ({
    id: item.id,
    label: item.label,
    watts: item.watts,
    defaultHours: item.default_hours,
    minHours: item.min_hours,
    maxHours: item.max_hours,
    tip: item.tip,
    category: item.category,
  }));
}

export async function fetchBaselineProfiles(): Promise<BaselineProfile[]> {
  const profiles = await getJson<ApiBaselineProfile[]>("/api/simulator/baseline-profiles");
  return profiles.map((item) => ({
    id: item.id,
    label: item.label,
    hoursByAppliance: item.hours_by_appliance,
  }));
}

export async function fetchRegions(): Promise<Region[]> {
  const regions = await getJson<ApiRegion[]>("/api/regions");
  return regions.map((item) => ({
    id: item.id,
    label: item.label,
    ratePerKwh: item.rate_per_kwh,
    carbonLbsPerKwh: item.carbon_lbs_per_kwh,
    currency: item.currency,
    locale: item.locale,
  }));
}
