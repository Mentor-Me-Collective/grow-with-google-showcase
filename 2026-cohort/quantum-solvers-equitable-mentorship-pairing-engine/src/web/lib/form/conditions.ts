import type { components } from "@/lib/api/types";

type S = components["schemas"];
export type FormVersion = S["FormVersion"];
export type FormField = S["FormField"];
export type FormClause = S["FormClause"];
export type AnswerValue = S["AnswerValue"];

/**
 * What the renderer holds while someone is typing: a value per field id, with
 * `undefined` for anything not yet answered. Distinct from the wire shape,
 * which carries provenance and drops everything invisible.
 */
export type FormValues = Record<string, AnswerValue | undefined>;

export function allFields(version: FormVersion): FormField[] {
  return version.sections.flatMap((s) => s.fields);
}

function isEmpty(value: AnswerValue | undefined) {
  if (value === undefined || value === null || value === "") return true;
  if (Array.isArray(value)) return value.length === 0;
  return false;
}

function asNumber(value: AnswerValue | undefined) {
  const n = typeof value === "string" ? Number(value) : value;
  return typeof n === "number" && Number.isFinite(n) ? n : null;
}

function clauseHolds(clause: FormClause, values: FormValues): boolean {
  const actual = values[clause.fieldId];

  switch (clause.operator) {
    case "is_answered":
      return !isEmpty(actual);

    case "equals":
      return Array.isArray(actual)
        ? actual.length === 1 && actual[0] === clause.value
        : actual === clause.value;

    case "not_equals":
      return !(Array.isArray(actual)
        ? actual.length === 1 && actual[0] === clause.value
        : actual === clause.value);

    // The one operator that reads the other way round: does the answer, which
    // is a set, contain the value the clause names.
    case "includes":
      return Array.isArray(actual)
        ? actual.includes(String(clause.value))
        : actual === clause.value;

    case "gt": {
      const a = asNumber(actual);
      const b = asNumber(clause.value);
      return a !== null && b !== null && a > b;
    }

    case "lt": {
      const a = asNumber(actual);
      const b = asNumber(clause.value);
      return a !== null && b !== null && a < b;
    }
  }
}

/**
 * Which fields are on screen for the answers given.
 *
 * Resolved to a fixed point rather than in one pass, because a field can be
 * conditioned on a field that is itself conditional. A question the person
 * cannot see has not been asked, so an answer left behind in local state must
 * not keep a downstream question alive. Every clause has to hold *and* every
 * field it reads has to be visible.
 *
 * Starts from everything visible and removes, which terminates: the set only
 * ever shrinks, so it settles in at most one round per field.
 */
export function visibleFieldIds(
  version: FormVersion,
  values: FormValues,
): Set<string> {
  const fields = allFields(version);
  const visible = new Set(fields.map((field) => field.id));

  let settled = false;
  while (!settled) {
    settled = true;
    for (const field of fields) {
      if (!visible.has(field.id) || !field.visibleWhen) continue;

      const holds = field.visibleWhen.all.every(
        (clause) => visible.has(clause.fieldId) && clauseHolds(clause, values),
      );
      if (!holds) {
        visible.delete(field.id);
        settled = false;
      }
    }
  }

  return visible;
}

/** The fields of one section that are currently on screen, in order. */
export function visibleFieldsInSection(
  section: S["FormSection"],
  visible: Set<string>,
): FormField[] {
  return section.fields.filter((field) => visible.has(field.id));
}
