export type ThemePreference = "system" | "light" | "dark" | "sepia";

const STORAGE_KEY = "theme";

export function getStoredTheme(): ThemePreference {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === "light" || stored === "dark" || stored === "sepia" ? stored : "system";
}

export function applyTheme(preference: ThemePreference): void {
  if (preference === "system") {
    document.documentElement.removeAttribute("data-theme");
    localStorage.removeItem(STORAGE_KEY);
  } else {
    document.documentElement.setAttribute("data-theme", preference);
    localStorage.setItem(STORAGE_KEY, preference);
  }
}
