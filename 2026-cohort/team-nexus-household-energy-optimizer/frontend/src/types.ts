/** Peace's EIA dataset groups appliances into one of these six categories. */
export type ApplianceCategory = "Kitchen" | "HVAC" | "Laundry" | "Entertainment" | "Office" | "Lighting";

export interface Appliance {
  /** A stable slug (e.g. "air-conditioner"), or a generated id for a user-added appliance. */
  id: string;
  label: string;
  watts: number;
  defaultHours: number;
  minHours: number;
  maxHours: number;
  tip: string;
  /** Built-in appliances carry Peace's category, used for icon/color grouping. Custom appliances have none. */
  category?: ApplianceCategory;
  /** How many identical units the user has (e.g. 2 TVs). Undefined behaves as 1. */
  quantity?: number;
}

export interface BaselineProfile {
  id: string;
  label: string;
  /** Typical hours/day for this home size, keyed by appliance id. Appliances not listed use their own default. */
  hoursByAppliance: Record<string, number>;
}

export interface Region {
  id: string;
  label: string;
  /** In the region's own local currency. */
  ratePerKwh: number;
  carbonLbsPerKwh: number;
  /** ISO 4217 currency code, used with locale to format cost via Intl.NumberFormat. */
  currency: string;
  /** BCP 47 locale for currency formatting. */
  locale: string;
}
