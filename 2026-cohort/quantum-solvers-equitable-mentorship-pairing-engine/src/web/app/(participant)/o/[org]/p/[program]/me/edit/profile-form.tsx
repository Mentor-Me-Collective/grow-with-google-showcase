"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button, buttonClasses } from "@/components/ui/button";
import { FormRenderer } from "@/components/form/form-renderer";
import { useAnswerForm } from "@/components/form/use-answer-form";
import { toFormValues } from "@/lib/form/answers";
import { saveProfileSection } from "./actions";

/**
 * Architecture 4.3: the same questions as the application form, after
 * submission, grouped by section with a save per section. Rendered by the same
 * FormRenderer, so a question added in the builder reaches this screen with no
 * work at all.
 */
export function ProfileForm({
  profile,
  programId,
  backHref,
}: {
  profile: Schemas["ProfileView"];
  programId: string;
  backHref: string;
}) {
  const version = profile.formVersion;
  const form = useAnswerForm({
    version,
    defaultValues: toFormValues(profile.answers),
  });
  const router = useRouter();
  const [savedSection, setSavedSection] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | undefined>();
  const [pending, startTransition] = useTransition();

  const save = (sectionId: string) => {
    const section = version.sections.find((s) => s.id === sectionId);
    const fieldIds = section?.fields.map((f) => f.id) ?? [];

    setSaving(sectionId);
    startTransition(async () => {
      if (!(await form.validateFields(fieldIds))) {
        setError("Some answers need another look before this can save.");
        setSaving(null);
        return;
      }

      // Only this section's answers go up. The endpoint merges, so the
      // sections not on screen are left exactly as they were.
      const answers = Object.fromEntries(
        Object.entries(form.answersNow()).filter(([fieldId]) =>
          fieldIds.includes(fieldId),
        ),
      );

      const result = await saveProfileSection({ programId, answers });
      setSaving(null);
      if (result.ok) {
        setError(undefined);
        setSavedSection(sectionId);
        router.refresh();
      } else {
        setError(result.message);
      }
    });
  };

  return (
    <div className="flex flex-col gap-48">
      {version.sections.map((section) => {
        const matchingFields = section.fields.filter((f) => f.matching);
        return (
          <section key={section.id} className="flex flex-col gap-24">
            <div className="flex flex-col gap-8">
              <h2 className="type-heading-m text-primary">{section.title}</h2>
              {section.description && (
                <p className="type-body-m text-secondary">{section.description}</p>
              )}
            </div>

            <FormRenderer form={form} sectionIds={[section.id]} showHeadings={false} />

            {/* 4.3: changing an answer that feeds matching does not re-run it.
                Said before saving rather than after, because afterwards it is
                an explanation of a disappointment. */}
            {matchingFields.length > 0 && (
              <p className="rounded-md border border-subtle bg-sunken p-16 type-body-s text-secondary">
                Some of these answers feed matching. Changing them now will not
                re-run a match you already have — they count towards the next
                run.
              </p>
            )}

            <div className="flex flex-wrap items-center gap-16">
              <Button
                onClick={() => save(section.id)}
                loading={pending && saving === section.id}
                loadingLabel="Saving this section"
              >
                Save this section
              </Button>
              {savedSection === section.id && !pending && (
                <p role="status" className="type-body-s text-secondary">
                  Saved.
                </p>
              )}
            </div>
          </section>
        );
      })}

      {error && (
        <p role="alert" className="type-body-m text-danger">
          {error}
        </p>
      )}

      <div className="flex border-t border-subtle pt-24">
        <Link href={backHref} className={buttonClasses({ variant: "secondary" })}>
          Back to my profile
        </Link>
      </div>
    </div>
  );
}
