import { z } from "zod";
import type { FormVersion } from "./conditions";
import { allFields } from "./conditions";
import { buildAnswerSchema } from "./zod-schema";

/**
 * The JSON Schema document for a form version: the portable artifact the
 * backend validates against and the form builder can show.
 *
 * Derived from the same generator the browser validates with, so the two cannot
 * drift. Nothing about a form is written twice.
 *
 * Two rules do not survive the trip, because JSON Schema draft 2020-12 has no
 * keyword for either:
 *
 *   - a date range, which stays a refinement in the validator and prose here
 *   - a file's accept list and size ceiling, which the browser enforces before
 *     a value exists at all
 *
 * They are carried as `description` rather than silently dropped.
 */
export function toJsonSchema(version: FormVersion, visibleIds: Set<string>) {
  const schema = z.toJSONSchema(buildAnswerSchema(version, visibleIds), {
    unrepresentable: "any",
    io: "input",
  });

  const properties = (schema.properties ?? {}) as Record<
    string,
    Record<string, unknown>
  >;

  for (const field of allFields(version)) {
    const node = properties[field.id];
    if (!node) continue;

    const notes: string[] = [];
    if (field.date?.min) notes.push(`On or after ${field.date.min}.`);
    if (field.date?.max) notes.push(`On or before ${field.date.max}.`);
    if (field.file) {
      notes.push(`Accepts ${field.file.accept.join(", ")}.`);
      notes.push(`Up to ${field.file.maxSizeBytes} bytes.`);
    }
    if (notes.length === 0) continue;

    node.description = [node.description, ...notes].filter(Boolean).join(" ");
  }

  return {
    $id: `braid:form/${version.programId}/${version.role}/v${version.version}`,
    ...schema,
  };
}
