"use client";

import { Controller, type Control, type FieldErrors } from "react-hook-form";
import type { UseFormRegister } from "react-hook-form";
import { Field, TextareaField } from "@/components/ui/input";
import type { FormField, FormValues } from "@/lib/form/conditions";
import {
  ConsentControl,
  FileControl,
  MultiSelectControl,
  ScaleControl,
  SingleSelectControl,
} from "./controls";

export type ControlProps = {
  field: FormField;
  control: Control<FormValues>;
  register: UseFormRegister<FormValues>;
  errors: FieldErrors<FormValues>;
  mark: "required" | "optional";
  emphasis?: "label" | "question";
  disabled?: boolean;
};

/**
 * One question, whichever of the nine types it is.
 *
 * Text, number and date go through `register` because a native input is already
 * the right control. The rest go through `Controller`, because a group of
 * radios or checkboxes has no single DOM value for RHF to read.
 *
 * Empty is normalised to `undefined` at the boundary rather than in the
 * validator, so the generated schema stays a plain description of the answers
 * and never has to know that a browser reports a cleared text box as "".
 */
export function FieldControl({
  field,
  control,
  register,
  errors,
  mark,
  emphasis,
  disabled,
}: ControlProps) {
  const error = errors[field.id]?.message as string | undefined;
  const shared = {
    label: field.label,
    helper: field.help ?? undefined,
    error,
    required: field.required,
    mark,
    emphasis,
    disabled,
  };
  const blank = (v: unknown) => (v === "" || v === undefined ? undefined : v);

  switch (field.type) {
    case "short_text":
      return (
        <Field
          {...shared}
          type="text"
          maxLength={field.text?.maxLength ?? undefined}
          placeholder={field.text?.placeholder ?? undefined}
          {...register(field.id, { setValueAs: blank })}
        />
      );

    case "long_text":
      return (
        <TextareaField
          {...shared}
          rows={5}
          maxLength={field.text?.maxLength ?? undefined}
          {...register(field.id, { setValueAs: blank })}
        />
      );

    case "number":
      return (
        <Field
          {...shared}
          type="number"
          inputMode="numeric"
          min={field.number?.min ?? undefined}
          max={field.number?.max ?? undefined}
          step={field.number?.step ?? undefined}
          numeric
          {...register(field.id, {
            setValueAs: (v) => (v === "" || v === undefined ? undefined : Number(v)),
          })}
        />
      );

    case "date":
      return (
        <Field
          {...shared}
          type="date"
          min={field.date?.min ?? undefined}
          max={field.date?.max ?? undefined}
          numeric
          {...register(field.id, { setValueAs: blank })}
        />
      );

    case "single_select":
      return (
        <Controller
          control={control}
          name={field.id}
          render={({ field: rhf }) => (
            <SingleSelectControl
              {...shared}
              name={rhf.name}
              options={field.options ?? []}
              value={rhf.value as string | undefined}
              onChange={rhf.onChange}
              onBlur={rhf.onBlur}
            />
          )}
        />
      );

    case "multi_select":
      return (
        <Controller
          control={control}
          name={field.id}
          render={({ field: rhf }) => (
            <MultiSelectControl
              {...shared}
              name={rhf.name}
              options={field.options ?? []}
              max={field.selection?.max ?? null}
              value={rhf.value as string[] | undefined}
              onChange={rhf.onChange}
              onBlur={rhf.onBlur}
            />
          )}
        />
      );

    case "scale":
      return (
        <Controller
          control={control}
          name={field.id}
          render={({ field: rhf }) => (
            <ScaleControl
              {...shared}
              name={rhf.name}
              min={field.scale?.min ?? 1}
              max={field.scale?.max ?? 5}
              minLabel={field.scale?.minLabel}
              maxLabel={field.scale?.maxLabel}
              value={rhf.value as number | undefined}
              onChange={rhf.onChange}
              onBlur={rhf.onBlur}
            />
          )}
        />
      );

    case "file":
      return (
        <Controller
          control={control}
          name={field.id}
          render={({ field: rhf }) => (
            <FileControl
              {...shared}
              name={rhf.name}
              accept={field.file?.accept ?? []}
              maxSizeBytes={field.file?.maxSizeBytes ?? 0}
              value={rhf.value as string | undefined}
              onChange={rhf.onChange}
              onBlur={rhf.onBlur}
            />
          )}
        />
      );

    case "consent":
      return (
        <Controller
          control={control}
          name={field.id}
          render={({ field: rhf }) => (
            <ConsentControl
              name={rhf.name}
              statement={field.consent?.statement ?? field.label}
              documentUrl={field.consent?.documentUrl}
              required={field.required}
              disabled={disabled}
              error={error}
              value={rhf.value as boolean | undefined}
              onChange={rhf.onChange}
              onBlur={rhf.onBlur}
            />
          )}
        />
      );
  }
}
