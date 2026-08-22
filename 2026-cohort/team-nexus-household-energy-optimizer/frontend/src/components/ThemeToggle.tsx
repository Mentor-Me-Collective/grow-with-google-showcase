import { BookOpen, Moon, Monitor, Sun } from "lucide-react";
import type { ThemePreference } from "../lib/theme";

interface ThemeToggleProps {
  value: ThemePreference;
  onChange: (value: ThemePreference) => void;
  /** The compact top-bar toggle omits Sepia to save space; it's still reachable from the accessibility panel. */
  includeSepia?: boolean;
}

const BASE_OPTIONS: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: "system", label: "System theme", icon: Monitor },
  { value: "light", label: "Light theme", icon: Sun },
  { value: "dark", label: "Dark theme", icon: Moon },
];

const SEPIA_OPTION = { value: "sepia" as const, label: "Sepia theme (easier on the eyes)", icon: BookOpen };

export function ThemeToggle({ value, onChange, includeSepia = false }: ThemeToggleProps) {
  const options = includeSepia ? [...BASE_OPTIONS, SEPIA_OPTION] : BASE_OPTIONS;

  return (
    <div className="theme-toggle" role="radiogroup" aria-label="Color theme">
      {options.map((option) => {
        const Icon = option.icon;
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={option.label}
            title={option.label}
            className={active ? "theme-toggle-btn active" : "theme-toggle-btn"}
            onClick={() => onChange(option.value)}
          >
            <Icon size={15} strokeWidth={1.75} />
          </button>
        );
      })}
    </div>
  );
}
