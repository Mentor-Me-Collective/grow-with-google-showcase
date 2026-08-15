"use client";

import { useRef, useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { Field, TextareaField } from "@/components/ui/input";
import {
  insertAtCursor,
  resolveMergeCodes,
  unknownMergeCodes,
} from "@/lib/comms/merge-codes";
import { resetTemplate, saveTemplate } from "./actions";

type Template = Schemas["MessageTemplate"];
type Kind = Schemas["TemplateKind"];

const KIND_LABEL: Record<Kind, string> = {
  welcome: "Welcome",
  match_notification: "Match notification",
  nudge: "Nudge",
  mid_point_check_in: "Mid-point check-in",
  closing: "Closing",
};

const KIND_WHEN: Record<Kind, string> = {
  welcome: "Sent when someone is approved onto the roster.",
  match_notification: "Sent to both sides when a run is published.",
  nudge: "Sent to a strand that has gone quiet for fourteen days.",
  mid_point_check_in: "Sent at the halfway milestone.",
  closing: "Sent when the programme ends.",
};

export function TemplatesEditor({
  templates,
  mergeCodes,
  programId,
}: {
  templates: Template[];
  mergeCodes: Schemas["MergeCode"][];
  programId: string;
}) {
  const [selected, setSelected] = useState<Kind>(templates[0]?.kind ?? "welcome");
  const [drafts, setDrafts] = useState<Record<string, { subject: string; body: string }>>(
    () =>
      Object.fromEntries(
        templates.map((t) => [t.kind, { subject: t.subject, body: t.body }]),
      ),
  );
  const [saved, setSaved] = useState<Record<string, Template>>(() =>
    Object.fromEntries(templates.map((t) => [t.kind, t])),
  );
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | undefined>();
  const [resetting, setResetting] = useState<Kind | null>(null);
  const bodyRef = useRef<HTMLTextAreaElement>(null);

  const template = saved[selected];
  const draft = drafts[selected] ?? { subject: "", body: "" };
  const dirty =
    draft.subject !== template?.subject || draft.body !== template?.body;

  const update = (patch: Partial<{ subject: string; body: string }>) =>
    setDrafts((current) => ({
      ...current,
      [selected]: { ...current[selected], ...patch },
    }));

  /**
   * Inserted at the cursor rather than appended: a coordinator reaches for a
   * code mid-sentence, and appending would put it at the end of the message.
   */
  const insert = (code: string) => {
    const { text, caret } = insertAtCursor(bodyRef.current, draft.body, code);
    update({ body: text });
    requestAnimationFrame(() => {
      bodyRef.current?.focus();
      bodyRef.current?.setSelectionRange(caret, caret);
    });
  };

  const save = () =>
    startTransition(async () => {
      const result = await saveTemplate({
        programId,
        kind: selected,
        subject: draft.subject,
        body: draft.body,
      });
      if (result.ok) {
        setSaved((c) => ({ ...c, [selected]: result.template }));
        setError(undefined);
      } else {
        setError(result.message);
      }
    });

  const doReset = (kind: Kind) =>
    startTransition(async () => {
      const result = await resetTemplate({ programId, kind });
      setResetting(null);
      if (result.ok) {
        setSaved((c) => ({ ...c, [kind]: result.template }));
        setDrafts((c) => ({
          ...c,
          [kind]: {
            subject: result.template.subject,
            body: result.template.body,
          },
        }));
        setError(undefined);
      } else {
        setError(result.message);
      }
    });

  return (
    <div className="flex flex-col gap-24 lg:flex-row lg:items-start">
      <nav aria-label="Templates" className="flex flex-col gap-8 lg:w-sidebar lg:shrink-0">
        {templates.map((t) => {
          const active = t.kind === selected;
          const edited = !saved[t.kind]?.isDefault;
          return (
            <button
              key={t.kind}
              type="button"
              onClick={() => setSelected(t.kind)}
              aria-current={active ? "true" : undefined}
              className={[
                "pointer-coarse:min-h-field flex flex-col items-start gap-4 rounded-md px-16 py-12 text-left",
                "outline-focus outline-offset-2 focus-visible:outline-2",
                active
                  ? "bg-accent text-on-accent"
                  : "border border-subtle text-primary hover:border-default",
              ].join(" ")}
            >
              <span className="type-body-m">{KIND_LABEL[t.kind]}</span>
              <span
                className={`type-caption ${active ? "text-on-accent" : "text-muted"}`}
              >
                {edited ? "Edited" : "Default wording"}
              </span>
            </button>
          );
        })}
      </nav>

      <div className="flex min-w-0 flex-1 flex-col gap-24">
        <p className="type-body-s text-muted">{KIND_WHEN[selected]}</p>

        <Field
          label="Subject"
          value={draft.subject}
          onChange={(e) => update({ subject: e.target.value })}
          mark="none"
        />

        <TextareaField
          ref={bodyRef}
          label="Message"
          value={draft.body}
          onChange={(e) => update({ body: e.target.value })}
          rows={12}
          mark="none"
          helper="Codes in braces are replaced when the message is sent."
        />

        <div className="flex flex-col gap-8">
          <h2 className="type-label text-muted">Insert a code</h2>
          <div className="flex flex-wrap gap-8">
            {mergeCodes.map((code) => (
              <Button
                key={code.code}
                size="sm"
                variant="secondary"
                onClick={() => insert(code.code)}
                title={code.description}
              >
                {code.code}
              </Button>
            ))}
          </div>
        </div>

        <Preview
          subject={draft.subject}
          body={draft.body}
          mergeCodes={mergeCodes}
        />

        {error && (
          <p role="alert" className="type-body-m text-danger">
            {error}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-16 border-t border-subtle pt-24">
          <Button
            size="lg"
            onClick={save}
            disabled={!dirty || !draft.subject.trim() || !draft.body.trim()}
            loading={pending}
            loadingLabel="Saving the template"
          >
            Save
          </Button>

          {!template?.isDefault && (
            <Button variant="ghost" onClick={() => setResetting(selected)}>
              Reset to default
            </Button>
          )}

          <p className="type-body-s text-muted" role="status">
            {dirty
              ? "Unsaved changes."
              : template?.updatedBy
                ? `Last edited by ${template.updatedBy}.`
                : "This is the default wording."}
          </p>
        </div>
      </div>

      <ConfirmDialog
        open={resetting !== null}
        title={`Reset the ${resetting ? KIND_LABEL[resetting].toLowerCase() : ""} template?`}
        confirmLabel="Reset it"
        confirmVariant="danger"
        busy={pending}
        busyLabel="Resetting"
        onCancel={() => setResetting(null)}
        onConfirm={() => resetting && doReset(resetting)}
        body={
          <p>
            Your wording is replaced with Braid&apos;s default. What you wrote is
            not kept.
          </p>
        }
      />
    </div>
  );
}

/** Substitution and validation live in lib/comms, so this and the broadcast
 *  composer cannot disagree about what a valid code is. */
function Preview({
  subject,
  body,
  mergeCodes,
}: {
  subject: string;
  body: string;
  mergeCodes: Schemas["MergeCode"][];
}) {
  const resolve = (text: string) => resolveMergeCodes(text, mergeCodes);
  const unknown = unknownMergeCodes(body, mergeCodes);

  return (
    <section className="flex flex-col gap-12 rounded-lg border border-subtle bg-sunken p-24">
      <h2 className="type-label text-muted">Preview</h2>
      <p className="type-heading-s text-primary">{resolve(subject)}</p>
      <p className="whitespace-pre-wrap type-body-m text-secondary">
        {resolve(body)}
      </p>
      {unknown.length > 0 && (
        <p role="alert" className="type-body-s text-danger">
          There is no code called {`{${unknown[0]}}`}. It would be sent as
          written.
        </p>
      )}
    </section>
  );
}
