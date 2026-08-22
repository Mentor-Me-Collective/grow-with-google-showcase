export type TextSizePreference = "small" | "default" | "large" | "x-large";

const STORAGE_KEY = "text-size";

export function getStoredTextSize(): TextSizePreference {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === "small" || stored === "large" || stored === "x-large" ? stored : "default";
}

export function applyTextSize(preference: TextSizePreference): void {
  if (preference === "default") {
    document.documentElement.removeAttribute("data-text-size");
    localStorage.removeItem(STORAGE_KEY);
  } else {
    document.documentElement.setAttribute("data-text-size", preference);
    localStorage.setItem(STORAGE_KEY, preference);
  }
}
