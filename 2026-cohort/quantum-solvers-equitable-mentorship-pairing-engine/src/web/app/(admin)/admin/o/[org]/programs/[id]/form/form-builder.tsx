"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Field } from "@/components/ui/input";
import { FieldEditor } from "./field-editor";
import { PreviewPane } from "./preview-pane";
import { publishDraft, saveDraft } from "./actions";

type FormVersion = Schemas["FormVersion"];
type FormSection = Schemas["FormSection"];
type FormField = Schemas["FormField"];
type Role = Schemas["Role"];

const newId = () => crypto.randomUUID();

const blankField = (): FormField => ({
  id: newId(),
  type: "short_text",
  label: "",
  help: null,
  required: false,
  matching: false,
  equity: false,
  admin: false,
  visibleWhen: null,
  options: null,
});

const TYPE_WORD: Record<Schemas["FormFieldType"], string> = {
  short_text: "Short text",
  long_text: "Long text",
  single_select: "Choose one",
  multi_select: "Choose several",
  scale: "Scale",
  number: "Number",
  date: "Date",
  file: "File",
  consent: "Consent",
};

export function FormBuilder({
  state,
  programId,
  role,
  basePath,
}: {
  state: Schemas["FormEditorState"];
  programId: string;
  role: Role;
  basePath: string;
}) {
  const router = useRouter();

  // The working copy is the draft when one exists, otherwise a copy of what is
  // live. Editing never touches the published document — that is what
  // applicants are answering right now.
  const source = state.draft ?? state.published;
  const [sections, setSections] = useState<FormSection[]>(
    () => structuredClone(source?.sections ?? []),
  );
  const [editing, setEditing] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | undefined>();
  const [notice, setNotice] = useState<string | undefined>();
  const [confirmingPublish, setConfirmingPublish] = useState(false);

  const dirty =
    JSON.stringify(sections) !== JSON.stringify(source?.sections ?? []);

  const allFields = sections.flatMap((s) => s.fields);
  const previewVersion: FormVersion = {
    id: source?.id ?? "preview",
    programId,
    role,
    version: source?.version ?? 1,
    publishedAt: null,
    sections,
  };

  const patchField = (fieldId: string, patch: Partial<FormField>) =>
    setSections((current) =>
      current.map((section) => ({
        ...section,
        fields: section.fields.map((f) =>
          f.id === fieldId ? { ...f, ...patch } : f,
        ),
      })),
    );

  const addSection = () =>
    setSections((current) => [
      ...current,
      { id: newId(), title: "", description: null, fields: [] },
    ]);

  const addField = (sectionId: string) => {
    const field = blankField();
    setSections((current) =>
      current.map((s) =>
        s.id === sectionId ? { ...s, fields: [...s.fields, field] } : s,
      ),
    );
    setEditing(field.id);
  };

  const duplicateField = (sectionId: string, fieldId: string) =>
    setSections((current) =>
      current.map((s) => {
        if (s.id !== sectionId) return s;
        const index = s.fields.findIndex((f) => f.id === fieldId);
        const original = s.fields[index];
        // A duplicate is a new question, so it takes new ids throughout —
        // answers are keyed by field id, and sharing one would merge two
        // questions' answers into a single column.
        const copy: FormField = {
          ...structuredClone(original),
          id: newId(),
          label: `${original.label} (copy)`,
          options: original.options?.map((o) => ({ ...o, id: newId() })) ?? null,
        };
        const fields = [...s.fields];
        fields.splice(index + 1, 0, copy);
        return { ...s, fields };
      }),
    );

  const removeField = (fieldId: string) =>
    setSections((current) =>
      current.map((s) => ({
        ...s,
        fields: s.fields.filter((f) => f.id !== fieldId),
      })),
    );

  const moveField = (sectionId: string, index: number, direction: -1 | 1) =>
    setSections((current) =>
      current.map((s) => {
        if (s.id !== sectionId) return s;
        const target = index + direction;
        if (target < 0 || target >= s.fields.length) return s;
        const fields = [...s.fields];
        [fields[index], fields[target]] = [fields[target], fields[index]];
        return { ...s, fields };
      }),
    );

  const moveSection = (index: number, direction: -1 | 1) =>
    setSections((current) => {
      const target = index + direction;
      if (target < 0 || target >= current.length) return current;
      const next = [...current];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });

  const save = () =>
    startTransition(async () => {
      const result = await saveDraft({ programId, role, sections });
      if (result.ok) {
        setError(undefined);
        setNotice("Draft saved. Applicants still see the published version.");
        router.refresh();
      } else {
        setError(result.message);
        setNotice(undefined);
      }
    });

  const publish = () =>
    startTransition(async () => {
      // Save first: publishing what is on screen, not what was last saved, is
      // what a coordinator means by the button.
      const saved = await saveDraft({ programId, role, sections });
      if (!saved.ok) {
        setConfirmingPublish(false);
        setError(saved.message);
        return;
      }
      const result = await publishDraft({ programId, role });
      setConfirmingPublish(false);
      if (result.ok) {
        setError(undefined);
        setNotice(`Version ${result.draft.version} is live.`);
        router.refresh();
      } else {
        setError(result.message);
        setNotice(undefined);
      }
    });

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-wrap items-center justify-between gap-16">
        <RoleTabs basePath={basePath} role={role} />
        <p className="type-body-s text-muted">
          {state.published
            ? `Version ${state.published.version} is live${state.draft ? ", with unpublished changes" : ""}.`
            : "Nothing published yet. Applicants cannot apply for this role until you publish."}
        </p>
      </div>

      {notice && (
        <p role="status" className="type-body-s text-secondary">
          {notice}
        </p>
      )}
      {error && (
        <p role="alert" className="type-body-m text-danger">
          {error}
        </p>
      )}

      <div className="flex flex-col gap-32 xl:flex-row xl:items-start">
        {/* Left: the question list. */}
        <div className="flex min-w-0 flex-1 flex-col gap-16">
          <h2 className="type-label text-muted">Questions</h2>

          {sections.length === 0 ? (
            <div className="rounded-lg border border-subtle bg-surface">
              <EmptyState
                markId="form-empty"
                title="This form has no questions."
                body="Applicants answer what you build here. Start with a section — About you is the usual first one — and add questions to it."
                action={<Button onClick={addSection}>Add a section</Button>}
              />
            </div>
          ) : (
            <ol className="flex flex-col gap-24">
              {sections.map((section, sectionIndex) => (
                <li
                  key={section.id}
                  className="flex flex-col gap-16 rounded-lg border border-subtle bg-surface p-16"
                >
                  <div className="flex flex-wrap items-end justify-between gap-12">
                    <div className="min-w-0 flex-1">
                      <Field
                        label={`Section ${sectionIndex + 1}`}
                        value={section.title}
                        mark="none"
                        placeholder="About you"
                        onChange={(e) =>
                          setSections((current) =>
                            current.map((s) =>
                              s.id === section.id
                                ? { ...s, title: e.target.value }
                                : s,
                            ),
                          )
                        }
                        error={
                          !section.title.trim()
                            ? "A section needs a title."
                            : undefined
                        }
                      />
                    </div>
                    <div className="flex gap-8">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => moveSection(sectionIndex, -1)}
                        disabled={sectionIndex === 0}
                        aria-label={`Move section ${section.title || sectionIndex + 1} up`}
                      >
                        Up
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => moveSection(sectionIndex, 1)}
                        disabled={sectionIndex === sections.length - 1}
                        aria-label={`Move section ${section.title || sectionIndex + 1} down`}
                      >
                        Down
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          setSections((current) =>
                            current.filter((s) => s.id !== section.id),
                          )
                        }
                        aria-label={`Remove section ${section.title || sectionIndex + 1}`}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>

                  <ol className="flex flex-col gap-12">
                    {section.fields.map((field, fieldIndex) => (
                      <li key={field.id} className="flex flex-col gap-12">
                        <div className="flex flex-wrap items-center justify-between gap-12 rounded-md border border-subtle p-12">
                          <div className="flex min-w-0 flex-col gap-4">
                            <p className="type-body-m text-primary">
                              {field.label || "Untitled question"}
                            </p>
                            <p className="type-caption text-muted">
                              {TYPE_WORD[field.type]}
                              {field.required ? " · required" : ""}
                              {field.visibleWhen ? " · conditional" : ""}
                              {field.matching ? " · matching" : ""}
                              {field.equity ? " · priority" : ""}
                              {field.admin ? " · yours only" : ""}
                            </p>
                          </div>

                          <div className="flex flex-wrap gap-8">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() =>
                                moveField(section.id, fieldIndex, -1)
                              }
                              disabled={fieldIndex === 0}
                              aria-label={`Move ${field.label || "question"} up`}
                            >
                              Up
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => moveField(section.id, fieldIndex, 1)}
                              disabled={fieldIndex === section.fields.length - 1}
                              aria-label={`Move ${field.label || "question"} down`}
                            >
                              Down
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => duplicateField(section.id, field.id)}
                              aria-label={`Duplicate ${field.label || "question"}`}
                            >
                              Duplicate
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removeField(field.id)}
                              aria-label={`Delete ${field.label || "question"}`}
                            >
                              Delete
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() =>
                                setEditing(editing === field.id ? null : field.id)
                              }
                            >
                              {editing === field.id ? "Close" : "Edit"}
                            </Button>
                          </div>
                        </div>

                        {editing === field.id && (
                          <FieldEditor
                            field={field}
                            earlierFields={allFields.slice(
                              0,
                              allFields.findIndex((f) => f.id === field.id),
                            )}
                            onChange={(patch) => patchField(field.id, patch)}
                            onClose={() => setEditing(null)}
                          />
                        )}
                      </li>
                    ))}
                  </ol>

                  <div className="flex">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => addField(section.id)}
                    >
                      Add a question
                    </Button>
                  </div>
                </li>
              ))}
            </ol>
          )}

          {sections.length > 0 && (
            <div className="flex">
              <Button variant="secondary" onClick={addSection}>
                Add a section
              </Button>
            </div>
          )}
        </div>

        {/* Right: the applicant's view. */}
        <div className="min-w-0 flex-1 xl:sticky xl:top-32">
          <PreviewPane version={previewVersion} />
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-16 border-t border-subtle pt-24">
        <Button
          size="lg"
          variant="secondary"
          onClick={save}
          disabled={!dirty}
          loading={pending}
          loadingLabel="Saving the draft"
        >
          Save draft
        </Button>
        <Button
          size="lg"
          onClick={() => setConfirmingPublish(true)}
          disabled={allFields.length === 0}
        >
          Publish
        </Button>
        <p className="type-body-s text-muted" role="status">
          {dirty ? "Unsaved changes." : "No unsaved changes."}
        </p>
      </div>

      <ConfirmDialog
        open={confirmingPublish}
        title="Publish this form?"
        confirmLabel="Publish it"
        busy={pending}
        busyLabel="Publishing"
        onCancel={() => setConfirmingPublish(false)}
        onConfirm={publish}
        body={
          <div className="flex flex-col gap-12">
            <p>
              Version {(state.published?.version ?? 0) + 1} becomes what every
              new applicant answers, with {allFields.length}{" "}
              {allFields.length === 1 ? "question" : "questions"} in{" "}
              {sections.length} {sections.length === 1 ? "section" : "sections"}.
            </p>
            <p>
              Applications already submitted keep the version they were answered
              against. Nothing anyone has already written changes.
            </p>
          </div>
        }
      />
    </div>
  );
}

/** Separate schemas per role, per 5.4: mentors and mentees answer different questions. */
function RoleTabs({ basePath, role }: { basePath: string; role: Role }) {
  return (
    <nav aria-label="Which form" className="flex gap-8">
      {(["mentee", "mentor"] as const).map((r) => {
        const active = r === role;
        return (
          <Link
            key={r}
            href={`${basePath}?role=${r}`}
            aria-current={active ? "page" : undefined}
            className={[
              "pointer-coarse:min-h-field inline-flex items-center rounded-sm px-12 py-8 type-body-s",
              "outline-focus outline-offset-2 focus-visible:outline-2",
              active
                ? "bg-accent text-on-accent"
                : "border border-default text-secondary hover:text-primary",
            ].join(" ")}
          >
            {r === "mentee" ? "Mentee form" : "Mentor form"}
          </Link>
        );
      })}
    </nav>
  );
}
