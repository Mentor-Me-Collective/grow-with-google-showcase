import type { Appliance, BaselineProfile, Region } from "./types";
import type { ApplianceBreakdown, HoursByCategory } from "./lib/calculations";

export interface NewApplianceInput {
  label: string;
  watts: number;
}

export interface EnergyContext {
  hours: HoursByCategory;
  onHoursChange: (id: string, hours: number) => void;
  baselineProfile: BaselineProfile;
  region: Region;
  /** Formats a number as currency in the selected region's local currency and locale. */
  formatCost: (value: number) => string;
  defaultBreakdown: ApplianceBreakdown[];
  userBreakdown: ApplianceBreakdown[];
  defaultCost: number;
  userCost: number;
  defaultKwh: number;
  userKwh: number;
  defaultCarbonLbs: number;
  carbonLbs: number;
  score: number;
  hogs: ApplianceBreakdown[];
  /** The full live list, built-in and user-added alike, all editable and removable. */
  appliances: Appliance[];
  onAddAppliance: (input: NewApplianceInput) => void;
  onRemoveAppliance: (id: string) => void;
  onUpdateWatts: (id: string, watts: number) => void;
  onUpdateQuantity: (id: string, quantity: number) => void;
  onClearAll: () => void;
  /** Built-in appliances the user removed, offered back as one-tap re-add suggestions. */
  removedBuiltins: Appliance[];
  onReAddAppliance: (id: string) => void;
}
