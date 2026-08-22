import {
  Gamepad2,
  Laptop,
  Lightbulb,
  Package,
  Refrigerator,
  Router,
  Thermometer,
  Tv,
  WashingMachine,
  type LucideIcon,
} from "lucide-react";
import type { ApplianceCategory } from "../types";

/** Per-category fallback, used when an appliance id isn't one of the specific ones below. */
const CATEGORY_ICONS: Record<ApplianceCategory, LucideIcon> = {
  HVAC: Thermometer,
  Kitchen: Refrigerator,
  Laundry: WashingMachine,
  Entertainment: Tv,
  Office: Laptop,
  Lighting: Lightbulb,
};

/** A few appliances get their own icon rather than sharing their category's. */
const APPLIANCE_ICONS: Record<string, LucideIcon> = {
  "gaming-console": Gamepad2,
  router: Router,
  "led-lights": Lightbulb,
};

export function getApplianceIcon(id: string, category?: ApplianceCategory): LucideIcon {
  return APPLIANCE_ICONS[id] ?? (category ? CATEGORY_ICONS[category] : undefined) ?? Package;
}
