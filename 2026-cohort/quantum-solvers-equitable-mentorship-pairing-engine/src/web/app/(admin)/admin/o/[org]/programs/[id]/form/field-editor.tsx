"use client";

import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Field, TextareaField } from "@/components/ui/input";

type FormField = Schemas["FormField"];
type FormOption = Schemas["FormOption"];
type FieldType = Schemas["FormFieldType"];

const TYPES: Array<{ value: FieldType; label: string }> = [
  { value: "short_text", label: "Short text" },
  { value: "long_text", label: "Long text" },
  { value: "single_select", label: "Choose one" },
  { value: "multi_select", label: "Choose several" },
  { value: "scale", label: "Scale" },
  { value: "number", label: "Number" },
  { value: "date", label: "Date" },
  { value: "file", label: "File upload" },
  { value: "consent", label: "Consent checkbox" },
];

const SELECT_TYPES = new Set<FieldType>(["single_select", "multi_select"]);

/**
 * The three flags from architecture 5.4. They decide what happens to an answer
 * downstream, so they are described by their consequence rather than named and
 * left for the coordinator to guess at.
 */
const FLAGS: Array<{
  key: "matching" | "equity" | "admin";
  label: string;
  help: string;
}> = [
  {
    key: "matching",
    label: "Use for matching",
    help: "Feeds the similarity score. Only useful on questions two people can be compared on.",
  },
  {
    key: "equity",
    label: "Use for priority",
    help: "Feeds the priority score, which decides who gets matched first when mentors are scarce.",
  },
  {
    key: "admin",
    label: "For you only",
    help: "Collected and never scored. Visible to coordinators, invisible to matching.",
  },
];

const newId = () => crypto.randomUUID();

export function FieldEditor({
  field,
  earlierFields,
  onChange,
  onClose,
}: {
  field: FormField;
  /** Only questions asked before this one can drive a visibleWhen on it. */
  earlierFields: FormField[];
  onChange: (patch: Partial<FormField>) => void;
  onClose: () => void;
}) {
  const clause = field.visibleWhen?.all?.[0];
  const conditionSource = earlierFields.find((f) => f.id === clause?.fieldId);

  return (
    <div className="flex flex-col gap-24 rounded-md border border-default bg-surface p-24">
      <div className="flex items-center justify-between gap-16">
        <h3 className="type-label text-muted">Editing this question</h3>
        <Button size="sm" variant="ghost" onClick={onClose}>
          Done
        </Button>
      </div>

      <Field
        label="Question"
        value={field.label}
        onChange={(e) => onChange({ label: e.target.value })}
        mark="none"
        error={!field.label.trim() ? "A question needs wording." : undefined}
      />

      <Field
        label="Help text"
        value={field.help ?? ""}
        onChange={(e) => onChange({ help: e.target.value || null })}
        helper="Shown under the question. Use it to say why you are asking."
        mark="none"
      />

      <label className="flex flex-col gap-8">
        <span className="type-label text-primary">Answer type</span>
        <select
          value={field.type}
          onChange={(e) => onChange(retypeTo(field, e.target.value as FieldType))}
          className="h-field rounded-sm border border-default bg-surface px-12 type-body-m text-primary focus:border-accent focus:outline-none focus:ring-3 focus:ring-focus-halo"
        >
          {TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </label>

      <Toggle
        label="Required"
        help="An applicant cannot move past this question without answering."
        checked={field.required}
        onChange={(required) => onChange({ required })}
      />

      {SELECT_TYPES.has(field.type) && (
        <Options
          options={field.options ?? []}
          onChange={(options) => onChange({ options })}
        />
      )}

      {field.type === "scale" && (
        <div className="flex flex-wrap gap-16">
          <Field
            label="Lowest"
            type="number"
            numeric
            mark="none"
            value={field.scale?.min ?? 1}
            onChange={(e) =>
              onChange({
                scale: { ...scaleOf(field), min: Number(e.target.value) },
              })
            }
          />
          <Field
            label="Highest"
            type="number"
            numeric
            mark="none"
            value={field.scale?.max ?? 5}
            onChange={(e) =>
              onChange({
                scale: { ...scaleOf(field), max: Number(e.target.value) },
              })
            }
          />
          <Field
            label="Label for the low end"
            mark="none"
            value={field.scale?.minLabel ?? ""}
            onChange={(e) =>
              onChange({
                scale: { ...scaleOf(field), minLabel: e.target.value || null },
              })
            }
          />
          <Field
            label="Label for the high end"
            mark="none"
            value={field.scale?.maxLabel ?? ""}
            onChange={(e) =>
              onChange({
                scale: { ...scaleOf(field), maxLabel: e.target.value || null },
              })
            }
          />
        </div>
      )}

      {(field.type === "short_text" || field.type === "long_text") && (
        <div className="flex flex-wrap gap-16">
          <Field
            label="Fewest characters"
            type="number"
            numeric
            mark="none"
            value={field.text?.minLength ?? ""}
            onChange={(e) =>
              onChange({
                text: {
                  ...(field.text ?? {}),
                  minLength: e.target.value === "" ? null : Number(e.target.value),
                },
              })
            }
          />
          <Field
            label="Most characters"
            type="number"
            numeric
            mark="none"
            value={field.text?.maxLength ?? ""}
            onChange={(e) =>
              onChange({
                text: {
                  ...(field.text ?? {}),
                  maxLength: e.target.value === "" ? null : Number(e.target.value),
                },
              })
            }
          />
        </div>
      )}

      {field.type === "consent" && (
        <TextareaField
          label="What they are agreeing to"
          value={field.consent?.statement ?? ""}
          onChange={(e) => onChange({ consent: { statement: e.target.value } })}
          rows={3}
          mark="none"
          helper="The sentence beside the checkbox. Separate from the question itself."
        />
      )}

      <fieldset className="flex flex-col gap-12">
        <legend className="mb-8 type-label text-primary">
          What this answer is for
        </legend>
        {FLAGS.map((flag) => (
          <Toggle
            key={flag.key}
            label={flag.label}
            help={flag.help}
            checked={Boolean(field[flag.key])}
            onChange={(next) => onChange({ [flag.key]: next })}
          />
        ))}
      </fieldset>

      <div className="flex flex-col gap-12 border-t border-subtle pt-16">
        <h4 className="type-label text-primary">Only ask this question when</h4>

        {earlierFields.length === 0 ? (
          <p className="type-body-s text-muted">
            Nothing comes before this question, so there is no answer to depend
            on. Move it below another question to make it conditional.
          </p>
        ) : (
          <div className="flex flex-wrap items-end gap-12">
            <label className="flex flex-col gap-8">
              <span className="type-label text-primary">Question</span>
              <select
                value={clause?.fieldId ?? ""}
                onChange={(e) =>
                  onChange({
                    visibleWhen: e.target.value
                      ? {
                          all: [
                            {
                              fieldId: e.target.value,
                              operator: clause?.operator ?? "is_answered",
                              ...(clause?.value !== undefined
                                ? { value: clause.value }
                                : {}),
                            },
                          ],
                        }
                      : null,
                  })
                }
                className="h-field rounded-sm border border-default bg-surface px-12 type-body-s text-primary focus:border-accent focus:outline-none focus:ring-3 focus:ring-focus-halo"
              >
                <option value="">Always ask it</option>
                {earlierFields.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.label || "Untitled question"}
                  </option>
                ))}
              </select>
            </label>

            {clause && (
              <>
                <label className="flex flex-col gap-8">
                  <span className="type-label text-primary">Test</span>
                  <select
                    value={clause.operator}
                    onChange={(e) =>
                      onChange({
                        visibleWhen: {
                          all: [
                            {
                              ...clause,
                              operator: e.target
                                .value as Schemas["FormClause"]["operator"],
                            },
                          ],
                        },
                      })
                    }
                    className="h-field rounded-sm border border-default bg-surface px-12 type-body-s text-primary focus:border-accent focus:outline-none focus:ring-3 focus:ring-focus-halo"
                  >
                    <option value="is_answered">has any answer</option>
                    <option value="equals">is</option>
                    <option value="not_equals">is not</option>
                    <option value="includes">includes</option>
                    <option value="gt">is more than</option>
                    <option value="lt">is less than</option>
                  </select>
                </label>

                {clause.operator !== "is_answered" && (
                  <ClauseValue
                    clause={clause}
                    source={conditionSource}
                    onChange={(value) =>
                      onChange({ visibleWhen: { all: [{ ...clause, value }] } })
                    }
                  />
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * A visibleWhen on a select compares option ids, never labels — the label is
 * editable copy and using it as the key would break the rule the moment
 * somebody fixed a typo.
 */
function ClauseValue({
  clause,
  source,
  onChange,
}: {
  clause: Schemas["FormClause"];
  source: FormField | undefined;
  onChange: (value: Schemas["AnswerValue"]) => void;
}) {
  if (source && SELECT_TYPES.has(source.type)) {
    return (
      <label className="flex flex-col gap-8">
        <span className="type-label text-primary">Answer</span>
        <select
          value={typeof clause.value === "string" ? clause.value : ""}
          onChange={(e) => onChange(e.target.value)}
          className="h-field rounded-sm border border-default bg-surface px-12 type-body-s text-primary focus:border-accent focus:outline-none focus:ring-3 focus:ring-focus-halo"
        >
          <option value="">Choose one</option>
          {(source.options ?? []).map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
    );
  }

  const numeric = clause.operator === "gt" || clause.operator === "lt";
  return (
    <Field
      label="Answer"
      mark="none"
      type={numeric ? "number" : "text"}
      numeric={numeric}
      value={
        typeof clause.value === "string" || typeof clause.value === "number"
          ? clause.value
          : ""
      }
      onChange={(e) =>
        onChange(numeric ? Number(e.target.value) : e.target.value)
      }
    />
  );
}

function Options({
  options,
  onChange,
}: {
  options: FormOption[];
  onChange: (options: FormOption[]) => void;
}) {
  return (
    <div className="flex flex-col gap-12">
      <h4 className="type-label text-primary">Choices</h4>

      {options.length === 0 && (
        <p className="type-body-s text-muted">
          A choice question with no choices cannot be published.
        </p>
      )}

      <ul className="flex flex-col gap-8">
        {options.map((option, i) => (
          <li key={option.id} className="flex items-end gap-8">
            <div className="min-w-0 flex-1">
              <Field
                label={`Choice ${i + 1}`}
                value={option.label}
                mark="none"
                onChange={(e) =>
                  onChange(
                    options.map((o) =>
                      o.id === option.id ? { ...o, label: e.target.value } : o,
                    ),
                  )
                }
              />
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onChange(options.filter((o) => o.id !== option.id))}
              aria-label={`Remove choice ${option.label || i + 1}`}
            >
              Remove
            </Button>
          </li>
        ))}
      </ul>

      <div className="flex">
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onChange([...options, { id: newId(), label: "" }])}
        >
          Add a choice
        </Button>
      </div>
    </div>
  );
}

function Toggle({
  label,
  help,
  checked,
  onChange,
}: {
  label: string;
  help: string;
  checked: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <label className="flex items-start gap-12">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-4 size-16 shrink-0 rounded-xs border border-default accent-[var(--action-primary-bg)] outline-focus outline-offset-2 focus-visible:outline-2"
      />
      <span className="flex flex-col gap-4">
        <span className="type-body-m text-primary">{label}</span>
        <span className="type-caption text-muted">{help}</span>
      </span>
    </label>
  );
}

const scaleOf = (field: FormField) =>
  field.scale ?? { min: 1, max: 5, minLabel: null, maxLabel: null };

/**
 * Changing type carries across only what the new type can use, and seeds what
 * it needs. A select that becomes a number should not keep options nothing can
 * render, and a field that becomes a select with no options cannot publish.
 */
function retypeTo(field: FormField, type: FieldType): Partial<FormField> {
  const patch: Partial<FormField> = { type };

  patch.options = SELECT_TYPES.has(type)
    ? (field.options ?? []).length > 0
      ? field.options
      : [
          { id: newId(), label: "" },
          { id: newId(), label: "" },
        ]
    : null;

  patch.scale =
    type === "scale"
      ? (field.scale ?? { min: 1, max: 5, minLabel: null, maxLabel: null })
      : null;
  patch.text =
    type === "short_text" || type === "long_text" ? (field.text ?? {}) : null;
  patch.consent =
    type === "consent" ? (field.consent ?? { statement: "" }) : null;

  return patch;
}
