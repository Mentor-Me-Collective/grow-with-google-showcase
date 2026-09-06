"use client";

import { AlertIcon } from "@/components/icon/icons";
import {
  visibleFieldsInSection,
  type FormField,
} from "@/lib/form/conditions";
import { FieldControl } from "./field-control";
import type { AnswerForm } from "./use-answer-form";

export const anchorFor = (fieldId: string) => `field-${fieldId}`;

export type FormRendererProps = {
  form: AnswerForm;
  /**
   * Which sections to render, and within them which fields. Omit both for the
   * whole form.
   *
   * This is the whole of what the renderer knows about being a wizard step, a
   * profile-edit panel or a builder preview. A section subset is desktop's step
   * and a single field id is mobile's, per design direction 9.
   */
  sectionIds?: string[];
  fieldIds?: string[];
  /** Off when the step is one question and the question is already the page. */
  showHeadings?: boolean;
  emphasis?: "label" | "question";
  disabled?: boolean;
};

export function FormRenderer({
  form,
  sectionIds,
  fieldIds,
  showHeadings = true,
  emphasis = "label",
  disabled,
}: FormRendererProps) {
  const { version, visible, errors, register, control } = form;

  const sections = sectionIds
    ? version.sections.filter((s) => sectionIds.includes(s.id))
    : version.sections;

  const inScope = (field: FormField) =>
    !fieldIds || fieldIds.includes(field.id);

  const onScreen = sections.flatMap((s) =>
    visibleFieldsInSection(s, visible).filter(inScope),
  );

  // 8.2: "Required fields are marked. Optional fields are not. Whichever is
  // rarer gets the mark." Which is rarer depends on the form, so it is counted
  // rather than assumed — and recounted as conditional questions come and go.
  const requiredCount = onScreen.filter((f) => f.required).length;
  const mark = requiredCount <= onScreen.length / 2 ? "required" : "optional";

  return (
    <div className="flex flex-col gap-48">
      {sections.map((section) => {
        const fields = visibleFieldsInSection(section, visible).filter(inScope);
        if (fields.length === 0) return null;

        return (
          <section key={section.id} className="flex flex-col gap-24">
            {showHeadings && (
              <div className="flex flex-col gap-4">
                <h2 className="type-heading-m text-primary">{section.title}</h2>
                {section.description && (
                  <p className="type-body-m text-secondary">{section.description}</p>
                )}
              </div>
            )}

            <div className="flex flex-col gap-32">
              {fields.map((field) => (
                <div key={field.id} id={anchorFor(field.id)} className="scroll-mt-32">
                  <FieldControl
                    field={field}
                    control={control}
                    register={register}
                    errors={errors}
                    mark={mark}
                    emphasis={emphasis}
                    disabled={disabled}
                  />
                </div>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

/**
 * Listed and linked, not just outlined in red. Someone who submits a long form
 * and lands back at the top with two failures twelve questions apart needs to
 * be told which two, in words.
 */
export function ErrorSummary({
  form,
  fields,
}: {
  form: AnswerForm;
  /** Restrict to the current step. A wizard must not report a later step. */
  fields?: FormField[];
}) {
  const { errors, version, visible } = form;
  const candidates =
    fields ??
    version.sections.flatMap((s) => visibleFieldsInSection(s, visible));
  const failures = candidates.filter((f) => errors[f.id]);

  if (failures.length === 0) return null;

  return (
    <div
      role="alert"
      className="flex flex-col gap-8 rounded-md border border-danger bg-surface p-16"
    >
      <p className="flex items-center gap-8 type-heading-s text-primary">
        <AlertIcon className="size-16 shrink-0 text-danger" />
        {failures.length === 1
          ? "One question needs another look"
          : `${failures.length} questions need another look`}
      </p>
      <ul className="flex flex-col gap-4">
        {failures.map((f) => (
          <li key={f.id}>
            <a href={`#${anchorFor(f.id)}`} className="type-body-s text-link underline">
              {f.label}
            </a>{" "}
            <span className="type-body-s text-secondary">
              {errors[f.id]?.message as string}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
