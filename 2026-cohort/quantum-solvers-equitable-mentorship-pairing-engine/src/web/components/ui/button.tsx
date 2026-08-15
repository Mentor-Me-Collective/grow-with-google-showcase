import type { ButtonHTMLAttributes } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const VARIANT: Record<ButtonVariant, string> = {
  primary: "bg-accent text-on-accent hover:bg-accent-hover",
  secondary: "border border-default text-primary hover:border-strong",
  ghost: "text-primary hover:bg-sunken",
  // 8.1 gives danger no hover colour and there is no darker danger token, so
  // the press and the focus ring carry the feedback.
  danger: "bg-danger text-on-accent",
};

const VARIANT_DISABLED: Record<ButtonVariant, string> = {
  primary: "bg-sunken text-muted",
  secondary: "border border-subtle text-muted",
  ghost: "text-muted",
  danger: "bg-sunken text-muted",
};

// 8.1: heights 40 / 32 / 48 with horizontal padding 16 / 12 / 20, bound
// together as utilities in tokens.css.
const SIZE: Record<ButtonSize, string> = {
  sm: "control-sm",
  md: "control-md",
  lg: "control-lg",
};

/**
 * The button's look, without the button. A link that acts as a primary action
 * is an `<a>` — it navigates — so it takes these classes rather than being
 * wrapped in a button element that lies about what it does.
 *
 * Loading and the disabled variants stay inside `Button`: a link cannot be
 * either.
 */
export function buttonClasses({
  variant = "primary",
  size = "md",
  className = "",
}: {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
} = {}) {
  return [
    "pointer-coarse:min-h-field",
    "relative inline-flex items-center justify-center gap-8",
    "rounded-md type-body-m whitespace-nowrap",
    "transition-[background-color,border-color,color,transform] duration-instant ease-out",
    "outline-focus outline-offset-2 focus-visible:outline-2",
    "active:scale-98",
    SIZE[size],
    VARIANT[variant],
    className,
  ].join(" ");
}

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  /** Announced while loading. Say what is happening, not "Loading". */
  loadingLabel?: string;
};

/**
 * The verb on the button is the verb in the resulting toast (8.1).
 * "Publish" produces "Published."
 *
 * `danger` is only legitimate for an irreversible destructive action inside a
 * confirmation dialog. Nothing enforces that; 8.1 states it as a rule.
 */
export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  loadingLabel = "Working",
  disabled = false,
  children,
  className = "",
  type = "button",
  ...rest
}: ButtonProps) {
  // Loading blocks input like disabled does, but must not *look* disabled —
  // so the styling keys off the prop, not off the DOM attribute.
  const inert = disabled || loading;

  return (
    <button
      {...rest}
      type={type}
      disabled={inert}
      aria-busy={loading || undefined}
      className={[
        // 8.1 draws 40 and 32; section 11 sets a 44px floor. Both hold: the
        // drawn heights on a fine pointer, never below 44 on a coarse one.
        "pointer-coarse:min-h-field",
        "relative inline-flex items-center justify-center gap-8",
        "rounded-md type-body-m whitespace-nowrap",
        "transition-[background-color,border-color,color,transform] duration-instant ease-out",
        "outline-focus outline-offset-2 focus-visible:outline-2",
        inert ? "cursor-not-allowed" : "active:scale-98",
        SIZE[size],
        disabled ? VARIANT_DISABLED[variant] : VARIANT[variant],
        className,
      ].join(" ")}
    >
      {/* The label stays in the DOM so the button cannot change width when it
          starts loading. 8.1: preserve the width so nothing reflows. */}
      <span className={loading ? "invisible" : undefined}>{children}</span>

      {loading && (
        <>
          <span
            aria-hidden="true"
            className="absolute size-16 animate-spin rounded-full border-2 border-current border-t-transparent"
          />
          <span className="sr-only">{loadingLabel}</span>
        </>
      )}
    </button>
  );
}
