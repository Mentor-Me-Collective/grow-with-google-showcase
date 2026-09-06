"use client";

import type { Schemas } from "@/lib/api/client";
import { FormRenderer } from "@/components/form/form-renderer";
import { useAnswerForm } from "@/components/form/use-answer-form";

/**
 * The applicant's view, rendered by the same component the apply screen uses.
 * That reuse is the point of the renderer existing: a preview built from a
 * second rendering path would drift, and the drift would only be discovered by
 * an applicant.
 *
 * Answering here is real — conditions resolve, validation fires — because a
 * preview that cannot be typed into cannot show a coordinator whether her
 * conditional question ever appears.
 */
export function PreviewPane({ version }: { version: Schemas["FormVersion"] }) {
  const form = useAnswerForm({ version });
  const fieldCount = version.sections.flatMap((s) => s.fields).length;

  return (
    <div className="flex flex-col gap-16">
      <div className="flex flex-col gap-4">
        <h2 className="type-label text-muted">What the applicant sees</h2>
        <p className="type-caption text-muted">
          Live. Answer it to check your conditions.
        </p>
      </div>

      <div className="rounded-lg border border-subtle bg-surface p-24">
        {fieldCount === 0 ? (
          <p className="type-body-m text-secondary">
            Nothing to show yet. Add a question and it appears here as an
            applicant would see it.
          </p>
        ) : (
          <FormRenderer form={form} />
        )}
      </div>
    </div>
  );
}
