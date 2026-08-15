"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import type { components } from "@/lib/api/types";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/input";
import { PublicHeader, PublicMain } from "@/components/shell/public-shell";
import { ErrorSummary, FormRenderer } from "@/components/form/form-renderer";
import { useAnswerForm } from "@/components/form/use-answer-form";
import { visibleFieldsInSection, type FormVersion } from "@/lib/form/conditions";
import { toFormValues } from "@/lib/form/answers";
import { submitApplication } from "./actions";

type S = components["schemas"];

/**
 * Design direction 9: one section per view on desktop, one question per view on
 * mobile. Two step models over one answer set, decided by the viewport.
 *
 * The server snapshot is the desktop model, so the first paint is a whole
 * section and a narrow browser collapses to one question on hydration rather
 * than the other way round. Going section-to-question loses nothing on screen;
 * the reverse would flash four questions and take three away.
 */
const DESKTOP = "(min-width: 48rem)";

function useIsDesktop() {
  return useSyncExternalStore(
    (onChange) => {
      const query = window.matchMedia(DESKTOP);
      query.addEventListener("change", onChange);
      return () => query.removeEventListener("change", onChange);
    },
    () => window.matchMedia(DESKTOP).matches,
    () => true,
  );
}

type Step =
  | { kind: "section"; sectionId: string; fieldIds: string[] }
  | { kind: "field"; sectionId: string; fieldIds: string[] }
  | { kind: "contact"; sectionId: null; fieldIds: [] };

const AUTOSAVE_MS = 800;

export function ApplyWizard({
  version,
  role,
  programName,
  orgSlug,
  programSlug,
}: {
  version: FormVersion;
  role: S["Role"];
  programName: string;
  orgSlug: string;
  programSlug: string;
}) {
  const router = useRouter();
  const desktop = useIsDesktop();
  const form = useAnswerForm({ version });
  const [index, setIndex] = useState(0);
  // Stays true through the navigation to /applied, so the submit button does
  // not flip back to idle while the confirmation route is still loading.
  const [leaving, setLeaving] = useState(false);
  const [submitError, setSubmitError] = useState<string | undefined>();
  const [contact, setContact] = useState({ name: "", email: "" });
  const [contactErrors, setContactErrors] = useState<{ name?: string; email?: string }>({});
  // The wizard gates steps with `validateFields`, which never runs
  // `handleSubmit`, so `isSubmitted` stays false and cannot drive the summary.
  const [attempted, setAttempted] = useState(false);

  const draft = useDraft({ orgSlug, programSlug, role, version, form });

  // Recomputed every render, because a conditional answer adds or removes a
  // step in place. Mobile's steps are the visible fields; desktop's are the
  // sections that still have one.
  const steps = useMemo<Step[]>(() => {
    const out: Step[] = [];
    for (const section of version.sections) {
      const fields = visibleFieldsInSection(section, form.visible);
      if (fields.length === 0) continue;
      if (desktop) {
        out.push({
          kind: "section",
          sectionId: section.id,
          fieldIds: fields.map((f) => f.id),
        });
      } else {
        for (const field of fields) {
          out.push({ kind: "field", sectionId: section.id, fieldIds: [field.id] });
        }
      }
    }
    out.push({ kind: "contact", sectionId: null, fieldIds: [] });
    return out;
  }, [desktop, form.visible, version.sections]);

  const at = Math.min(index, steps.length - 1);
  const step = steps[at];
  const last = at === steps.length - 1;
  const headingRef = useRef<HTMLDivElement>(null);

  const sectionsBefore = useMemo(() => {
    if (!step.sectionId) return version.sections.length;
    const order = version.sections.map((s) => s.id);
    return order.indexOf(step.sectionId);
  }, [step.sectionId, version.sections]);

  // "The form must feel finishable, which means never showing the applicant how
  // many questions remain until they are within the last section." (Section 9.)
  const inLastSection =
    step.sectionId === version.sections[version.sections.length - 1]?.id;
  const questionsLeft = inLastSection
    ? steps.slice(at, steps.length - 1).length
    : null;

  const goto = useCallback((next: number) => {
    setIndex(next);
    setAttempted(false);
    // Move focus to the top of the new step, or a keyboard user is left where
    // the old Continue button used to be.
    requestAnimationFrame(() => headingRef.current?.focus());
  }, []);

  const onContinue = async () => {
    if (step.kind === "contact") return;
    setAttempted(true);
    const ok = await form.validateFields(step.fieldIds);
    if (ok) {
      setAttempted(false);
      goto(at + 1);
    }
  };

  const onSubmit = async () => {
    const errors: typeof contactErrors = {};
    if (contact.name.trim().length < 2) errors.name = "Tell us what to call you.";
    if (!contact.email.includes("@")) errors.email = "Enter an email address we can reach you at.";
    setContactErrors(errors);
    if (Object.keys(errors).length > 0) return;

    // Everything before the contact step has already been validated on the way
    // through, but a conditional revealed late could still be empty.
    const everything = steps.flatMap((s) => s.fieldIds);
    if (!(await form.validateFields(everything))) {
      setSubmitError("Some answers need another look. Step back to fix them.");
      return;
    }

    setSubmitError(undefined);
    const result = await submitApplication({
      orgSlug,
      programSlug,
      body: {
        role,
        name: contact.name.trim(),
        email: contact.email.trim(),
        formVersionId: version.id,
        answers: form.answersNow(),
      },
    });

    if (!result.ok) {
      setSubmitError(result.message);
      return;
    }
    draft.clear();
    // replace, not push: back from the confirmation must not re-enter a form
    // that has already been submitted.
    setLeaving(true);
    router.replace(
      `/p/${orgSlug}/${programSlug}/applied?id=${result.application.id}`,
    );
  };

  return (
    <>
      <PublicHeader right={<SaveState draft={draft} />} />

      <PublicMain className="flex flex-col gap-32">
        <Progress
          total={version.sections.length}
          done={sectionsBefore}
          questionsLeft={questionsLeft}
        />

        <RoleBanner
          role={role}
          programName={programName}
          switchTo={`/p/${orgSlug}/${programSlug}/apply?role=${role === "mentee" ? "mentor" : "mentee"}`}
        />

        <div ref={headingRef} tabIndex={-1} className="flex flex-col gap-32 outline-none">
          {attempted && step.kind !== "contact" && (
            <ErrorSummary
              form={form}
              fields={version.sections
                .flatMap((s) => s.fields)
                .filter((f) => step.fieldIds.includes(f.id))}
            />
          )}

          {step.kind === "contact" ? (
            <ContactStep
              contact={contact}
              errors={contactErrors}
              onChange={setContact}
            />
          ) : (
            <FormRenderer
              form={form}
              sectionIds={[step.sectionId]}
              fieldIds={step.kind === "field" ? step.fieldIds : undefined}
              // On mobile the question is the page, so it takes the heading and
              // the section title would only repeat what the progress bar says.
              showHeadings={step.kind === "section"}
              emphasis={step.kind === "field" ? "question" : "label"}
            />
          )}
        </div>

        {submitError && (
          <p role="alert" className="type-body-s text-danger">
            {submitError}
          </p>
        )}

        <div className="flex items-center gap-16 border-t border-subtle pt-24">
          {at > 0 && (
            <Button variant="ghost" onClick={() => goto(at - 1)}>
              Back
            </Button>
          )}
          {last ? (
            <Button
              size="lg"
              onClick={onSubmit}
              loading={form.isSubmitting || leaving}
              loadingLabel="Sending your application"
            >
              Send my application
            </Button>
          ) : (
            <Button size="lg" onClick={onContinue}>
              Continue
            </Button>
          )}
        </div>

        <p className="type-caption text-muted">
          Your answers are kept on this device as you go. There is no resume link
          yet, so finishing on another phone means starting again.
        </p>
      </PublicMain>
    </>
  );
}

/**
 * Sections completed, never a percentage. A percentage on a form the
 * coordinator built is a lie, because nobody knows what the questions weigh.
 */
function Progress({
  total,
  done,
  questionsLeft,
}: {
  total: number;
  done: number;
  questionsLeft: number | null;
}) {
  const sections = `${countWord(done)} ${done === 1 ? "section" : "sections"} done`;
  const label =
    questionsLeft !== null
      ? `${sections} · ${questionsLeft} ${questionsLeft === 1 ? "question" : "questions"} left`
      : sections;

  return (
    <div className="flex flex-col gap-16">
      <p className="type-label text-muted">{label}</p>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={done}
        aria-label="Sections completed"
        className="flex gap-8"
      >
        {Array.from({ length: total }, (_, i) => (
          <span
            key={i}
            className={`h-4 flex-1 rounded-sm ${
              i < done ? "bg-inverse" : i === done ? "bg-default" : "bg-subtle"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

const COUNTS = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight"];
const countWord = (n: number) => COUNTS[n] ?? String(n);

/**
 * Architecture 3.2: the role is fixed from the query and shown. Someone who
 * clicked the wrong link has no other way to notice before the end.
 */
function RoleBanner({
  role,
  programName,
  switchTo,
}: {
  role: S["Role"];
  programName: string;
  switchTo: string;
}) {
  return (
    <p className="flex flex-wrap items-center gap-8 rounded-md border border-subtle bg-surface p-16 type-body-s text-secondary">
      <span>
        Applying to {programName} as a{" "}
        <strong className="font-semibold text-primary">{role}</strong>.
      </span>
      <Link href={switchTo} className="text-link underline">
        Apply as a {role === "mentee" ? "mentor" : "mentee"} instead
      </Link>
    </p>
  );
}

/**
 * The form schema has no email question and `ApplicationCreate` requires one,
 * so the wizard adds a step rather than mining an answer that might not be
 * there. Coordinators build the questions; this is the envelope.
 */
function ContactStep({
  contact,
  errors,
  onChange,
}: {
  contact: { name: string; email: string };
  errors: { name?: string; email?: string };
  onChange: (next: { name: string; email: string }) => void;
}) {
  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h2 className="type-heading-m text-primary">How we reach you</h2>
        <p className="type-body-m text-secondary">
          The last two. Your address is used for the outcome of this
          application and nothing else.
        </p>
      </div>

      <Field
        label="Your name"
        autoComplete="name"
        required
        value={contact.name}
        error={errors.name}
        onChange={(e) => onChange({ ...contact, name: e.target.value })}
      />
      <Field
        label="Email address"
        type="email"
        autoComplete="email"
        required
        value={contact.email}
        error={errors.email}
        onChange={(e) => onChange({ ...contact, email: e.target.value })}
      />
    </div>
  );
}

function SaveState({ draft }: { draft: ReturnType<typeof useDraft> }) {
  // A timestamp, not a spinner. A spinner says wait, and there is nothing to
  // wait for.
  return (
    <span aria-live="polite" className="type-caption text-muted">
      {draft.savedAt
        ? `Saved ${new Intl.DateTimeFormat("en-GB", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }).format(new Date(draft.savedAt))}`
        : draft.failed
          ? "Not saved"
          : ""}
    </span>
  );
}

/**
 * Autosave. Debounced, and only after something has actually been answered, so
 * opening the form and leaving does not mint an empty draft.
 *
 * The id lives in this browser only. Architecture 3.2 also asks for an emailed
 * resume link, which needs an endpoint that does not exist yet; the screen says
 * so rather than implying the draft can be picked up elsewhere.
 */
function useDraft({
  orgSlug,
  programSlug,
  role,
  version,
  form,
}: {
  orgSlug: string;
  programSlug: string;
  role: S["Role"];
  version: FormVersion;
  form: ReturnType<typeof useAnswerForm>;
}) {
  const key = `braid:draft:${orgSlug}/${programSlug}:${role}`;
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const draftId = useRef<string | undefined>(undefined);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const { answersNow, reset } = form;

  // Resume whatever this browser started.
  useEffect(() => {
    const existing = window.localStorage.getItem(key);
    if (!existing) return;
    let live = true;
    void (async () => {
      const { data } = await api.GET(
        "/orgs/{orgSlug}/programs/{programSlug}/application-draft",
        {
          params: { path: { orgSlug, programSlug }, query: { draftId: existing } },
        },
      );
      if (!live || !data || data.formVersionId !== version.id) return;
      draftId.current = data.draftId;
      setSavedAt(data.savedAt);
      // Reset rather than per-field writes: nothing has been typed yet, and a
      // whole-form replace keeps the dirty state honest.
      reset(toFormValues(data.answers));
    })();
    return () => {
      live = false;
    };
    // Runs once for this form version. Re-running would fight the typist.
  }, [key, orgSlug, programSlug, reset, version.id]);

  const save = useCallback(() => {
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      const answers = answersNow();
      if (Object.keys(answers).length === 0) return;
      const { data, error } = await api.PUT(
        "/orgs/{orgSlug}/programs/{programSlug}/application-draft",
        {
          params: { path: { orgSlug, programSlug } },
          body: {
            draftId: draftId.current,
            role,
            formVersionId: version.id,
            answers,
          },
        },
      );
      if (error || !data) {
        setFailed(true);
        return;
      }
      draftId.current = data.draftId;
      window.localStorage.setItem(key, data.draftId);
      setFailed(false);
      setSavedAt(data.savedAt);
    }, AUTOSAVE_MS);
  }, [answersNow, key, orgSlug, programSlug, role, version.id]);

  // Architecture 3.2 says autosave on blur. Watching the values instead catches
  // a radio, which never blurs before the answer changes.
  useEffect(() => {
    save();
    return () => clearTimeout(timer.current);
  }, [form.values, save]);

  const clear = useCallback(() => {
    clearTimeout(timer.current);
    window.localStorage.removeItem(key);
  }, [key]);

  return { savedAt, failed, clear };
}
