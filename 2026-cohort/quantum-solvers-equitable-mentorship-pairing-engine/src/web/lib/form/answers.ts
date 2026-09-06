import type { components } from "@/lib/api/types";
import type { FormValues, FormVersion } from "./conditions";
import { allFields } from "./conditions";

type S = components["schemas"];

/**
 * Local form state to the wire shape.
 *
 * Two things happen here and nowhere else.
 *
 * Fields hidden by a condition are dropped. A question nobody was shown has no
 * answer, and storing one would put words in someone's mouth. The stripping is
 * at serialisation on purpose: local state keeps the value, so toggling an
 * answer back does not lose what was typed.
 *
 * File fields are dropped too. There is no upload endpoint yet, so the value in
 * local state is a filename, which is not an answer to anything.
 */
export function toAnswerInput(
  version: FormVersion,
  values: FormValues,
  visibleIds: Set<string>,
  provenance: S["Provenance"],
): Record<string, S["AnswerInput"]> {
  const answers: Record<string, S["AnswerInput"]> = {};

  for (const field of allFields(version)) {
    if (!visibleIds.has(field.id)) continue;
    if (field.type === "file") continue;

    const value = values[field.id];
    if (value === undefined || value === "") continue;
    if (Array.isArray(value) && value.length === 0) continue;

    answers[field.id] = { value, provenance };
  }

  return answers;
}

/** Stored answers back to form state, for profile edit and for resuming. */
export function toFormValues(
  answers: Record<string, S["AnswerRecord"]> | undefined,
): FormValues {
  const values: FormValues = {};
  for (const [fieldId, record] of Object.entries(answers ?? {})) {
    values[fieldId] = record.value;
  }
  return values;
}
