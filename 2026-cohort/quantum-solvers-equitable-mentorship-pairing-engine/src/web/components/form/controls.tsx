"use client";

import { useId, useRef, useState } from "react";
import { CheckIcon, ChevronDownIcon } from "@/components/icon/icons";
import {
  FieldsetShell,
  controlClasses,
  labelType,
  type FieldOwnProps,
} from "@/components/ui/input";

/* ---------------------------------------------------------------
   Shared pieces
   --------------------------------------------------------------- */

export type Option = { id: string; label: string };

const BOX =
  "peer size-16 shrink-0 appearance-none border bg-surface " +
  "border-default checked:border-accent checked:bg-accent " +
  "outline-focus outline-offset-2 focus-visible:outline-2 " +
  "disabled:cursor-not-allowed disabled:border-subtle disabled:bg-sunken " +
  "transition-[background-color,border-color] duration-instant ease-out";

/**
 * The box and its mark. The mark is a sibling faded in by `peer-checked`
 * rather than an inset shadow: section 6 allows two shadows and this is not one
 * of them, and opacity is on the list of things we are allowed to animate.
 */
function Box({
  kind,
  ...input
}: { kind: "radio" | "checkbox" } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <span className="relative inline-flex shrink-0">
      <input
        {...input}
        type={kind}
        className={`${BOX} ${kind === "radio" ? "rounded-full" : "rounded-xs"}`}
      />
      {kind === "radio" ? (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute inset-4 rounded-full bg-surface opacity-0 transition-opacity duration-instant ease-out peer-checked:opacity-100"
        />
      ) : (
        <CheckIcon className="pointer-events-none absolute inset-0 size-16 text-on-accent opacity-0 transition-opacity duration-instant ease-out peer-checked:opacity-100" />
      )}
    </span>
  );
}

/**
 * One row in a radio or checkbox group. 44px minimum on a coarse pointer per
 * section 11, and the whole row is the target rather than the 16px box.
 */
function ChoiceRow({
  children,
  htmlFor,
}: {
  children: React.ReactNode;
  htmlFor: string;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className="flex cursor-pointer items-center gap-12 rounded-sm py-4 pointer-coarse:min-h-field type-body-m text-primary"
    >
      {children}
    </label>
  );
}

/* ---------------------------------------------------------------
   Single select
   --------------------------------------------------------------- */

/**
 * Radios up to six options, a native select above that. Neither doc specifies
 * the cut: radios show every choice at once, which is better until the list is
 * long enough that showing it all buries the rest of the form.
 */
export const RADIO_LIMIT = 6;

export function SingleSelectControl({
  options,
  value,
  onChange,
  onBlur,
  name,
  disabled,
  ...shell
}: FieldOwnProps & {
  options: Option[];
  value: string | undefined;
  onChange: (value: string | undefined) => void;
  onBlur: () => void;
  name: string;
  disabled?: boolean;
}) {
  const id = useId();
  const helperId = `${id}-helper`;
  const errorId = `${id}-error`;

  if (options.length > RADIO_LIMIT) {
    return (
      <NativeSelectControl
        {...shell}
        options={options}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        name={name}
        disabled={disabled}
      />
    );
  }

  return (
    <FieldsetShell {...shell} helperId={helperId} errorId={errorId}>
      <div className="flex flex-col gap-4">
        {options.map((option) => {
          const optionId = `${id}-${option.id}`;
          return (
            <ChoiceRow key={option.id} htmlFor={optionId}>
              <Box
                kind="radio"
                id={optionId}
                name={name}
                value={option.id}
                checked={value === option.id}
                disabled={disabled}
                onChange={() => onChange(option.id)}
                onBlur={onBlur}
              />
              <span className={disabled ? "text-muted" : undefined}>{option.label}</span>
            </ChoiceRow>
          );
        })}
      </div>
    </FieldsetShell>
  );
}

function NativeSelectControl({
  options,
  value,
  onChange,
  onBlur,
  name,
  disabled,
  label,
  helper,
  error,
  required,
  mark,
  emphasis,
}: FieldOwnProps & {
  options: Option[];
  value: string | undefined;
  onChange: (value: string | undefined) => void;
  onBlur: () => void;
  name: string;
  disabled?: boolean;
}) {
  const id = useId();
  const controlId = `${id}-control`;
  const helperId = `${id}-helper`;
  const errorId = `${id}-error`;

  return (
    <div className="flex flex-col gap-8">
      <label
        htmlFor={controlId}
        className={`flex flex-wrap items-center gap-8 text-primary ${labelType(emphasis)}`}
      >
        {label}
        {mark !== "optional" && required && <span className="text-muted">Required</span>}
        {mark === "optional" && !required && <span className="text-muted">Optional</span>}
      </label>

      <div className="relative">
        <select
          id={controlId}
          name={name}
          value={value ?? ""}
          disabled={disabled}
          required={required}
          aria-required={required || undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : helper ? helperId : undefined}
          onChange={(e) => onChange(e.target.value === "" ? undefined : e.target.value)}
          onBlur={onBlur}
          className={`h-field appearance-none pr-48 ${controlClasses(Boolean(error))}`}
        >
          <option value="">Choose one</option>
          {options.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDownIcon
          aria-hidden="true"
          className="pointer-events-none absolute top-1/2 right-16 size-16 -translate-y-1/2 text-muted"
        />
      </div>

      {helper && !error && (
        <p id={helperId} className="type-caption text-muted">
          {helper}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="type-caption text-danger">
          {error}
        </p>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------
   Multi select
   --------------------------------------------------------------- */

export function MultiSelectControl({
  options,
  value,
  onChange,
  onBlur,
  name,
  disabled,
  max,
  ...shell
}: FieldOwnProps & {
  options: Option[];
  value: string[] | undefined;
  onChange: (value: string[] | undefined) => void;
  onBlur: () => void;
  name: string;
  disabled?: boolean;
  max?: number | null;
}) {
  const id = useId();
  const helperId = `${id}-helper`;
  const errorId = `${id}-error`;
  const selected = value ?? [];
  const atLimit = max != null && selected.length >= max;

  const toggle = (optionId: string) => {
    const next = selected.includes(optionId)
      ? selected.filter((v) => v !== optionId)
      : [...selected, optionId];
    onChange(next.length === 0 ? undefined : next);
  };

  return (
    <FieldsetShell {...shell} helperId={helperId} errorId={errorId}>
      <div className="flex flex-col gap-4">
        {options.map((option) => {
          const optionId = `${id}-${option.id}`;
          const checked = selected.includes(option.id);
          return (
            <ChoiceRow key={option.id} htmlFor={optionId}>
              <Box
                kind="checkbox"
                id={optionId}
                name={name}
                value={option.id}
                checked={checked}
                // At the ceiling the unchosen boxes go disabled rather than
                // silently ignoring a click. Section 8.0: no hover, no press,
                // and the reason is already in the helper text.
                disabled={disabled || (atLimit && !checked)}
                onChange={() => toggle(option.id)}
                onBlur={onBlur}
              />
              <span className={disabled || (atLimit && !checked) ? "text-muted" : undefined}>
                {option.label}
              </span>
            </ChoiceRow>
          );
        })}
      </div>
    </FieldsetShell>
  );
}

/* ---------------------------------------------------------------
   Scale
   --------------------------------------------------------------- */

/**
 * A row of numbered radios. One tab stop for the group and arrow keys within
 * it, which is what a native radio group already does — so it is built from
 * real radios rather than from buttons with a roving tabindex.
 */
export function ScaleControl({
  min,
  max,
  minLabel,
  maxLabel,
  value,
  onChange,
  onBlur,
  name,
  disabled,
  ...shell
}: FieldOwnProps & {
  min: number;
  max: number;
  minLabel?: string | null;
  maxLabel?: string | null;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  onBlur: () => void;
  name: string;
  disabled?: boolean;
}) {
  const id = useId();
  const helperId = `${id}-helper`;
  const errorId = `${id}-error`;
  const points = Array.from({ length: max - min + 1 }, (_, i) => min + i);

  return (
    <FieldsetShell {...shell} helperId={helperId} errorId={errorId}>
      <div className="flex flex-wrap items-center gap-8">
        {points.map((point) => {
          const pointId = `${id}-${point}`;
          const checked = value === point;
          return (
            <label key={point} htmlFor={pointId} className="relative inline-flex">
              <input
                type="radio"
                id={pointId}
                name={name}
                value={point}
                checked={checked}
                disabled={disabled}
                onChange={() => onChange(point)}
                onBlur={onBlur}
                className="peer sr-only"
              />
              {/* The ring belongs on the visible box, not on the sr-only input. */}
              <span
                className={[
                  "flex h-control-lg w-48 cursor-pointer items-center justify-center",
                  "rounded-sm border type-data-m",
                  "transition-colors duration-instant ease-out",
                  "border-default text-primary hover:border-strong",
                  "peer-checked:border-accent peer-checked:bg-accent peer-checked:text-on-accent",
                  "peer-disabled:cursor-not-allowed peer-disabled:border-subtle peer-disabled:text-muted",
                  "peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus",
                ].join(" ")}
              >
                {point}
              </span>
            </label>
          );
        })}
      </div>

      {(minLabel || maxLabel) && (
        <div className="flex justify-between gap-16 type-caption text-muted">
          <span>{minLabel}</span>
          <span>{maxLabel}</span>
        </div>
      )}
    </FieldsetShell>
  );
}

/* ---------------------------------------------------------------
   Consent
   --------------------------------------------------------------- */

/**
 * One checkbox. The statement is the label, so it is read out with the control
 * rather than sitting near it, and `label` names the question for the
 * coordinator's list without appearing twice on screen.
 */
export function ConsentControl({
  statement,
  documentUrl,
  value,
  onChange,
  onBlur,
  name,
  disabled,
  error,
  required,
}: {
  statement: string;
  documentUrl?: string | null;
  value: boolean | undefined;
  onChange: (value: boolean) => void;
  onBlur: () => void;
  name: string;
  disabled?: boolean;
  error?: string;
  required?: boolean;
}) {
  const id = useId();
  const controlId = `${id}-control`;
  const errorId = `${id}-error`;

  return (
    <div className="flex flex-col gap-8">
      <label
        htmlFor={controlId}
        className="flex cursor-pointer items-start gap-12 py-4 pointer-coarse:min-h-field type-body-m text-primary"
      >
        <span className="mt-4 flex">
          <Box
            kind="checkbox"
            id={controlId}
            name={name}
            checked={value ?? false}
            disabled={disabled}
            required={required}
            aria-required={required || undefined}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? errorId : undefined}
            onChange={(e) => onChange(e.target.checked)}
            onBlur={onBlur}
          />
        </span>
        <span>
          {statement}{" "}
          {documentUrl && (
            <a href={documentUrl} className="text-link underline">
              Read it in full
            </a>
          )}
        </span>
      </label>

      {error && (
        <p
          id={errorId}
          role="alert"
          className="type-caption text-danger"
        >
          {error}
        </p>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------
   File
   --------------------------------------------------------------- */

const readableSize = (bytes: number) => `${Math.round(bytes / 1_048_576)} MB`;

/**
 * Holds the chosen file and reports its name. Nothing is uploaded: there is no
 * upload endpoint in the contract yet, so the serialiser drops file answers
 * rather than inventing an id for one. The accept list and the size ceiling are
 * enforced here, before a value exists at all, because a rejected file should
 * never become an answer that later fails validation.
 */
export function FileControl({
  accept,
  maxSizeBytes,
  value,
  onChange,
  onBlur,
  name,
  disabled,
  label,
  helper,
  error,
  required,
  mark,
  emphasis,
}: FieldOwnProps & {
  accept: string[];
  maxSizeBytes: number;
  value: string | undefined;
  onChange: (value: string | undefined) => void;
  onBlur: () => void;
  name: string;
  disabled?: boolean;
}) {
  const id = useId();
  const controlId = `${id}-control`;
  const helperId = `${id}-helper`;
  const errorId = `${id}-error`;
  const inputRef = useRef<HTMLInputElement>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const shown = localError ?? error;

  const onPick = (file: File | undefined) => {
    if (!file) {
      setLocalError(null);
      onChange(undefined);
      return;
    }
    if (file.size > maxSizeBytes) {
      setLocalError(
        `That file is larger than ${readableSize(maxSizeBytes)}. Choose a smaller one.`,
      );
      onChange(undefined);
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    setLocalError(null);
    onChange(file.name);
  };

  return (
    <div className="flex flex-col gap-8">
      <label
        htmlFor={controlId}
        className={`flex flex-wrap items-center gap-8 text-primary ${labelType(emphasis)}`}
      >
        {label}
        {mark !== "optional" && required && <span className="text-muted">Required</span>}
        {mark === "optional" && !required && <span className="text-muted">Optional</span>}
      </label>

      <input
        ref={inputRef}
        type="file"
        id={controlId}
        name={name}
        accept={accept.join(",")}
        disabled={disabled}
        required={required}
        aria-required={required || undefined}
        aria-invalid={shown ? true : undefined}
        aria-describedby={shown ? errorId : helper ? helperId : undefined}
        onChange={(e) => onPick(e.target.files?.[0])}
        onBlur={onBlur}
        className={[
          "w-full rounded-sm border bg-surface type-body-m text-primary",
          "file:mr-16 file:h-control-md file:cursor-pointer file:border-0",
          "file:bg-sunken file:px-16 file:type-body-m file:text-primary",
          "outline-focus outline-offset-2 focus-visible:outline-2",
          shown ? "border-danger" : "border-default",
          "disabled:cursor-not-allowed disabled:border-subtle disabled:bg-sunken",
        ].join(" ")}
      />

      {value && !shown && (
        <p className="type-caption text-muted">
          {value} is attached. It uploads when you send the form.
        </p>
      )}

      {helper && !shown && (
        <p id={helperId} className="type-caption text-muted">
          {helper}
        </p>
      )}

      {shown && (
        <p id={errorId} role="alert" className="type-caption text-danger">
          {shown}
        </p>
      )}
    </div>
  );
}
