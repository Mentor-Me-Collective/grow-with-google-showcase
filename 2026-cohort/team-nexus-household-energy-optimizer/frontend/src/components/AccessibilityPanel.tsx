import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import type { ThemePreference } from "../lib/theme";
import type { TextSizePreference } from "../lib/textSize";
import { AccessibilityControls } from "./AccessibilityControls";

interface AccessibilityPanelProps {
  open: boolean;
  onClose: () => void;
  theme: ThemePreference;
  onThemeChange: (value: ThemePreference) => void;
  textSize: TextSizePreference;
  onTextSizeChange: (value: TextSizePreference) => void;
  isReading: boolean;
  onReadAloud: () => void;
  onStopReading: () => void;
}

const FOCUSABLE_SELECTOR =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

export function AccessibilityPanel({ open, onClose, ...controlsProps }: AccessibilityPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;

    closeButtonRef.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      const focusable = panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div className="a11y-backdrop" onClick={onClose} />
      <div
        className="a11y-panel"
        role="dialog"
        aria-modal="true"
        aria-label="Accessibility settings"
        ref={panelRef}
      >
        <div className="a11y-panel-header">
          <h2>Accessibility</h2>
          <button
            type="button"
            className="a11y-close"
            aria-label="Close accessibility panel"
            onClick={onClose}
            ref={closeButtonRef}
          >
            <X size={18} strokeWidth={1.75} />
          </button>
        </div>

        <AccessibilityControls {...controlsProps} />
      </div>
    </>
  );
}
