"use client";

// `useId` is a hook, so these are client components. Form controls carry
// handlers in every real use anyway.
import { useId } from "react";
import type { InputHTMLAttributes, Ref, TextareaHTMLAttributes } from "react";
import { AlertIcon } from "@/components/icon/icons";

/**
 * 8.2: label above at 8px, 44px control, helper in caption, error in
 * status-danger with a 12px icon.
 *
 * `label` is required. Section 11 forbids a placeholder standing in for a
 * label, so the type signature makes that impossible rather than reviewable.
 *
 * "Required fields are marked. Optional fields are not. Whichever is rarer
 * gets the mark." Which is rarer is a per-form decision, so `mark` inverts it.
 */
export type FieldOwnProps = {
  label: string;
  helper?: string;
  /** Say what went wrong and how to fix it: "Enter a date after 14 September". */
  error?: string;
  required?: boolean;
  mark?: "required" | "optional" | "none";
  /**
   * `question` sets the label in heading-m instead of the label token, for the
   * one-question-per-view wizard on mobile where the question is the page.
   *
   * The element stays a real `<label>` bound to its control. Only the type
   * token changes, so there is no second code path and no way to end up with a
   * heading that is not a label.
   */
  emphasis?: "label" | "question";
};

export const labelType = (emphasis: FieldOwnProps["emphasis"]) =>
  emphasis === "question" ? "type-heading-m" : "type-label";

/**
 * `typography` is a parameter rather than something a caller appends via
 * className: two type utilities on one element resolve by stylesheet order, not
 * by the order they are written, so a `type-data-m` passed in from outside
 * would silently lose to the `type-body-m` in here.
 */
export const controlClasses = (invalid: boolean, typography = "type-body-m") =>
  [
    `w-full rounded-sm border bg-surface px-12 text-primary ${typography}`,
    "transition-[border-color,box-shadow] duration-instant ease-out",
    "placeholder:text-muted",
    "focus:outline-none focus:ring-3 focus:ring-focus-halo",
    invalid
      ? "border-danger focus:border-danger"
      : "border-default focus:border-accent",
    "disabled:cursor-not-allowed disabled:border-subtle disabled:bg-sunken disabled:text-muted",
  ].join(" ");

function Mark({ mark = "required", required }: Pick<FieldOwnProps, "mark" | "required">) {
  if (mark === "required" && required) return <span className="text-muted">Required</span>;
  if (mark === "optional" && !required) return <span className="text-muted">Optional</span>;
  return null;
}

function Support({
  helper,
  error,
  helperId,
  errorId,
}: Pick<FieldOwnProps, "helper" | "error"> & {
  helperId: string;
  errorId: string;
}) {
  return (
    <>
      {helper && !error && (
        <p id={helperId} className="type-caption text-muted">
          {helper}
        </p>
      )}

      {error && (
        <p
          id={errorId}
          role="alert"
          className="flex items-start gap-4 type-caption text-danger"
        >
          <AlertIcon className="mt-4 size-12 shrink-0" />
          {error}
        </p>
      )}
    </>
  );
}

function FieldShell({
  label,
  helper,
  error,
  required,
  mark,
  emphasis,
  controlId,
  helperId,
  errorId,
  children,
}: FieldOwnProps & {
  controlId: string;
  helperId: string;
  errorId: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-8">
      <label
        htmlFor={controlId}
        className={`flex flex-wrap items-center gap-8 text-primary ${labelType(emphasis)}`}
      >
        {label}
        <Mark mark={mark} required={required} />
      </label>

      {children}

      <Support helper={helper} error={error} helperId={helperId} errorId={errorId} />
    </div>
  );
}

/**
 * The same furniture for a group of controls. A radio group, a checkbox group
 * and a scale have no single element for a `<label>` to point at, so the group
 * gets a `<fieldset>` and a `<legend>`. Reusing FieldShell here would attach
 * the label to nothing.
 */
export function FieldsetShell({
  label,
  helper,
  error,
  required,
  mark,
  emphasis,
  helperId,
  errorId,
  children,
}: FieldOwnProps & {
  helperId: string;
  errorId: string;
  children: React.ReactNode;
}) {
  return (
    // A legend does not take part in its fieldset's flex layout, so the gap
    // comes from its own margin and the controls get their own flex container.
    <fieldset
      className="min-w-0"
      aria-required={required || undefined}
      aria-invalid={error ? true : undefined}
      aria-describedby={error ? errorId : helper ? helperId : undefined}
    >
      <legend
        className={`mb-8 flex flex-wrap items-center gap-8 text-primary ${labelType(emphasis)}`}
      >
        {label}
        <Mark mark={mark} required={required} />
      </legend>

      <div className="flex flex-col gap-8">
        {children}
        <Support helper={helper} error={error} helperId={helperId} errorId={errorId} />
      </div>
    </fieldset>
  );
}

export type FieldProps = FieldOwnProps &
  Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "required"> & {
    /** Numbers and dates set in the mono face, per section 5.3. */
    numeric?: boolean;
  };

export function Field({
  label,
  helper,
  error,
  required,
  mark,
  emphasis,
  numeric = false,
  className = "",
  ...rest
}: FieldProps) {
  const id = useId();
  const controlId = `${id}-control`;
  const helperId = `${id}-helper`;
  const errorId = `${id}-error`;

  return (
    <FieldShell
      label={label}
      helper={helper}
      error={error}
      required={required}
      mark={mark}
      emphasis={emphasis}
      controlId={controlId}
      helperId={helperId}
      errorId={errorId}
    >
      <input
        {...rest}
        id={controlId}
        required={required}
        aria-required={required || undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : helper ? helperId : undefined}
        className={`h-field ${controlClasses(Boolean(error), numeric ? "type-data-m" : "type-body-m")} ${className}`}
      />
    </FieldShell>
  );
}

export type TextareaFieldProps = FieldOwnProps &
  Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "id" | "required"> & {
    /**
     * For callers that need the node itself rather than its value — inserting
     * at the cursor is the case that cannot be done from state alone. React 19
     * passes `ref` as an ordinary prop, so no forwardRef is involved.
     */
    ref?: Ref<HTMLTextAreaElement>;
  };

export function TextareaField({
  label,
  helper,
  error,
  required,
  mark,
  emphasis,
  rows = 4,
  className = "",
  ...rest
}: TextareaFieldProps) {
  const id = useId();
  const controlId = `${id}-control`;
  const helperId = `${id}-helper`;
  const errorId = `${id}-error`;

  return (
    <FieldShell
      label={label}
      helper={helper}
      error={error}
      required={required}
      mark={mark}
      emphasis={emphasis}
      controlId={controlId}
      helperId={helperId}
      errorId={errorId}
    >
      <textarea
        {...rest}
        id={controlId}
        rows={rows}
        required={required}
        aria-required={required || undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : helper ? helperId : undefined}
        className={`py-8 ${controlClasses(Boolean(error))} ${className}`}
      />
    </FieldShell>
  );
}
