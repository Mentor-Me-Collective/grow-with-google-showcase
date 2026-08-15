import { z } from "zod";
import type { FormField, FormVersion } from "./conditions";
import { allFields } from "./conditions";

/**
 * Builds the validator for a form version from the version itself. Nothing here
 * is written per form: a coordinator publishes questions, and the rules follow.
 *
 * `visibleIds` is required rather than optional. A field hidden by a condition
 * has not been asked, so its required rule must not fire, and making the caller
 * pass the visible set means that cannot be forgotten.
 */
export function buildAnswerSchema(
  version: FormVersion,
  visibleIds: Set<string>,
) {
  const shape: Record<string, z.ZodType> = {};

  for (const field of allFields(version)) {
    if (!visibleIds.has(field.id)) continue;
    shape[field.id] = fieldSchema(field);
  }

  return z.object(shape);
}

const optionIds = (field: FormField) => (field.options ?? []).map((o) => o.id);

/** Zod needs a non-empty tuple to build an enum. A select with no options is a
 *  half-finished question, so it validates as a plain string rather than
 *  throwing while a coordinator is still building it in the form builder. */
function enumOf(field: FormField, error: string) {
  const ids = optionIds(field);
  return ids.length > 0
    ? z.enum(ids as [string, ...string[]], { error })
    : z.string({ error });
}

const plural = (n: number, one: string, many: string) =>
  n === 1 ? `1 ${one}` : `${n} ${many}`;

function fieldSchema(field: FormField): z.ZodType {
  const base = baseSchema(field);
  const described = base.meta({
    title: field.label,
    ...(field.help ? { description: field.help } : {}),
  });
  return field.required ? described : described.optional();
}

function baseSchema(field: FormField): z.ZodType {
  switch (field.type) {
    case "short_text":
    case "long_text": {
      const min = field.text?.minLength ?? null;
      const max = field.text?.maxLength ?? null;
      let s = z.string({ error: "Answer this question to continue." });
      if (min && min > 0) {
        s = s.min(min, {
          error: `Write at least ${plural(min, "character", "characters")}.`,
        });
      } else if (field.required) {
        s = s.min(1, { error: "Answer this question to continue." });
      }
      if (max) {
        s = s.max(max, {
          error: `Keep this under ${plural(max, "character", "characters")}.`,
        });
      }
      return s;
    }

    case "single_select":
      return enumOf(field, "Choose one to continue.");

    case "multi_select": {
      const min = field.selection?.min ?? null;
      const max = field.selection?.max ?? null;
      let s = z.array(enumOf(field, "Choose at least one."), {
        error: "Choose at least one.",
      });
      if (min && min > 0) {
        s = s.min(min, {
          error:
            min === 1
              ? "Choose at least one."
              : `Choose at least ${min}.`,
        });
      } else if (field.required) {
        s = s.min(1, { error: "Choose at least one." });
      }
      if (max) s = s.max(max, { error: `Choose up to ${max}.` });
      return s;
    }

    case "scale": {
      const min = field.scale?.min ?? 1;
      const max = field.scale?.max ?? 5;
      return z
        .number({ error: "Pick a point on the scale." })
        .int()
        .min(min, { error: "Pick a point on the scale." })
        .max(max, { error: "Pick a point on the scale." });
    }

    case "number": {
      const min = field.number?.min ?? null;
      const max = field.number?.max ?? null;
      const unit = field.number?.unit ? ` ${field.number.unit}` : "";
      let s = z.number({ error: "Enter a number." });
      if (field.number?.step === 1) s = s.int({ error: "Enter a whole number." });
      if (min !== null) {
        s = s.min(min, { error: `Enter ${min}${unit} or more.` });
      }
      if (max !== null) {
        s = s.max(max, { error: `Enter ${max}${unit} or less.` });
      }
      return s;
    }

    case "date": {
      const min = field.date?.min ?? null;
      const max = field.date?.max ?? null;
      let s: z.ZodType = z.iso.date({ error: "Enter a date." });
      // JSON Schema has no portable keyword for a date range, so these two
      // survive as refinements in the validator and as prose in the generated
      // document. The control also sets the native min and max.
      if (min) {
        s = s.refine((v) => String(v) >= min, {
          error: `Choose a date on or after ${readableDate(min)}.`,
        });
      }
      if (max) {
        s = s.refine((v) => String(v) <= max, {
          error: `Choose a date on or before ${readableDate(max)}.`,
        });
      }
      return s;
    }

    // The value here is the chosen file's name. Nothing is uploaded yet: there
    // is no upload endpoint, so the serialiser drops file fields entirely.
    // Required still means a file has to be chosen before the form will submit.
    case "file":
      return z.string({ error: "Choose a file." }).min(1, {
        error: "Choose a file.",
      });

    case "consent":
      return field.required
        ? z.literal(true, { error: "Tick this to continue." })
        : z.boolean();
  }
}

function readableDate(iso: string) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${iso}T00:00:00Z`));
}
