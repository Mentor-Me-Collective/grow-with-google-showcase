import { EarOff, Square, Volume2 } from "lucide-react";
import type { ThemePreference } from "../lib/theme";
import type { TextSizePreference } from "../lib/textSize";
import { isReadAloudSupported } from "../lib/readAloud";
import { ThemeToggle } from "./ThemeToggle";

interface AccessibilityControlsProps {
  theme: ThemePreference;
  onThemeChange: (value: ThemePreference) => void;
  textSize: TextSizePreference;
  onTextSizeChange: (value: TextSizePreference) => void;
  isReading: boolean;
  onReadAloud: () => void;
  onStopReading: () => void;
}

const TEXT_SIZE_OPTIONS: { value: TextSizePreference; label: string; fullLabel: string }[] = [
  { value: "small", label: "S", fullLabel: "Small text" },
  { value: "default", label: "M", fullLabel: "Default text size" },
  { value: "large", label: "L", fullLabel: "Large text" },
  { value: "x-large", label: "XL", fullLabel: "Extra large text" },
];

/** The actual accessibility controls, shared by the desktop slide-in panel and the mobile menu (inlined, no extra popup). */
export function AccessibilityControls({
  theme,
  onThemeChange,
  textSize,
  onTextSizeChange,
  isReading,
  onReadAloud,
  onStopReading,
}: AccessibilityControlsProps) {
  return (
    <>
      <div className="a11y-section">
        <div className="a11y-section-label">Text size</div>
        <div className="text-size-toggle" role="radiogroup" aria-label="Text size">
          {TEXT_SIZE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={option.value === textSize}
              aria-label={option.fullLabel}
              title={option.fullLabel}
              className={option.value === textSize ? "text-size-btn active" : "text-size-btn"}
              onClick={() => onTextSizeChange(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="a11y-section">
        <div className="a11y-section-label">Theme</div>
        <ThemeToggle value={theme} onChange={onThemeChange} includeSepia />
      </div>

      <div className="a11y-section">
        <div className="a11y-section-label">Read aloud</div>
        {isReadAloudSupported() ? (
          <button
            type="button"
            className="btn btn-secondary a11y-read-btn"
            onClick={isReading ? onStopReading : onReadAloud}
          >
            {isReading ? (
              <>
                <Square size={15} strokeWidth={2} />
                Stop reading
              </>
            ) : (
              <>
                <Volume2 size={15} strokeWidth={2} />
                Read this page aloud
              </>
            )}
          </button>
        ) : (
          <p className="muted-note">
            <EarOff size={15} strokeWidth={1.75} />
            Read-aloud isn't supported in this browser.
          </p>
        )}
      </div>
    </>
  );
}
