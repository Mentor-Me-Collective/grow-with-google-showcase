"use client";

import { useCallback, useMemo } from "react";
import { useForm, useWatch, type Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { components } from "@/lib/api/types";
import {
  visibleFieldIds,
  type FormValues,
  type FormVersion,
} from "@/lib/form/conditions";
import { buildAnswerSchema } from "@/lib/form/zod-schema";
import { toAnswerInput } from "@/lib/form/answers";

type S = components["schemas"];
export type AnswerInputMap = Record<string, S["AnswerInput"]>;

/**
 * The answer state for one form version, shared by everything that renders it.
 *
 * Separated from the renderer because a wizard needs to validate one step
 * without submitting, autosave without validating, and decide for itself what
 * a step is — none of which a component that only draws fields can offer.
 */
export function useAnswerForm({
  version,
  defaultValues,
  provenance = "self",
}: {
  version: FormVersion;
  defaultValues?: FormValues;
  provenance?: S["Provenance"];
}) {
  /**
   * Rebuilt from the answers on every run rather than held in state. A field
   * hidden by a condition has not been asked, so its rules must not fire, and
   * deriving that at validation time from the values being validated is the
   * only version that cannot go stale.
   */
  const resolver = useMemo<Resolver<FormValues>>(
    () => (values, context, options) => {
      const schema = buildAnswerSchema(version, visibleFieldIds(version, values));
      // The shape is built at runtime from the form version, so zod infers
      // Record<string, unknown> and cannot know it matches FormValues. The
      // cast is at this one boundary and nowhere else.
      const validate = zodResolver(schema) as unknown as Resolver<FormValues>;
      return validate(values, context, options);
    },
    [version],
  );

  const {
    register,
    control,
    handleSubmit,
    getValues,
    trigger,
    reset,
    formState: { errors, isSubmitting, isSubmitted },
  } = useForm<FormValues>({
    defaultValues: defaultValues ?? {},
    resolver,
    mode: "onBlur",
    reValidateMode: "onChange",
  });

  // useWatch rather than watch(): it subscribes without handing back a function
  // the compiler has to bail out on.
  const values = useWatch({ control }) as FormValues;
  const visible = visibleFieldIds(version, values);

  /** Wire-shaped answers as they stand. Hidden fields already stripped. */
  const answersNow = useCallback((): AnswerInputMap => {
    const current = getValues();
    return toAnswerInput(
      version,
      current,
      visibleFieldIds(version, current),
      provenance,
    );
  }, [getValues, provenance, version]);

  /** Wrap a handler so it receives wire-shaped answers, after validation. */
  const submit = useCallback(
    (handler: (answers: AnswerInputMap) => Promise<void> | void) =>
      handleSubmit(async () => {
        await handler(answersNow());
      }),
    [answersNow, handleSubmit],
  );

  /** Validate a subset. A wizard step gates on this, not on the whole form. */
  const validateFields = useCallback(
    (ids: string[]) => trigger(ids.length > 0 ? ids : undefined),
    [trigger],
  );

  return {
    version,
    register,
    control,
    errors,
    values,
    visible,
    getValues,
    /** Replace every answer at once, for resuming a draft or a saved profile. */
    reset,
    answersNow,
    submit,
    validateFields,
    isSubmitting,
    isSubmitted,
  };
}

export type AnswerForm = ReturnType<typeof useAnswerForm>;
