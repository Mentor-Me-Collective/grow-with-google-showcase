"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { Field } from "@/components/ui/input";
import { leaveProgram, saveSettings, setMuted } from "./actions";

type Preferences = Schemas["NotificationPreferences"];

const KINDS: Array<{ key: keyof Omit<Preferences, "digest">; label: string; help: string }> = [
  {
    key: "newMessage",
    label: "When someone writes to me",
    help: "A message in one of your strands.",
  },
  {
    key: "matchPublished",
    label: "When I am matched",
    help: "Sent once, when a run is published.",
  },
  {
    key: "milestoneReminders",
    label: "Milestone reminders",
    help: "A nudge before each point in the programme's arc.",
  },
  {
    key: "broadcasts",
    label: "Programme announcements",
    help: "Messages the coordinator sends to everyone at once.",
  },
];

const DIGESTS: Array<{ value: Schemas["DigestFrequency"]; label: string }> = [
  { value: "off", label: "No summary" },
  { value: "daily", label: "Once a day" },
  { value: "weekly", label: "Once a week" },
];

export function SettingsForm({
  settings,
}: {
  settings: Schemas["AccountSettings"];
}) {
  const router = useRouter();
  const [name, setName] = useState(settings.account.name);
  const [prefs, setPrefs] = useState<Preferences>(settings.notifications);
  const [pending, startTransition] = useTransition();
  const [notice, setNotice] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();
  const [leaving, setLeaving] = useState<Schemas["AccountProgram"] | null>(null);

  const dirty =
    name !== settings.account.name ||
    JSON.stringify(prefs) !== JSON.stringify(settings.notifications);

  const run = (action: () => Promise<{ ok: boolean; message?: string }>) =>
    startTransition(async () => {
      const result = await action();
      setLeaving(null);
      if (result.ok) {
        setError(undefined);
        setNotice(result.message);
        router.refresh();
      } else {
        setError(result.message);
        setNotice(undefined);
      }
    });

  return (
    <div className="flex flex-col gap-48">
      <section className="flex flex-col gap-16">
        <h2 className="type-heading-m text-primary">You</h2>

        <Field
          label="Name"
          value={name}
          mark="none"
          onChange={(e) => setName(e.target.value)}
          helper="What everyone in your programmes sees."
        />

        <Field
          label="Email address"
          value={settings.account.email}
          mark="none"
          disabled
          helper="Your sign-in link goes here. Changing it needs a new link, so ask your coordinator for now."
        />

        {/* 4.16 lists a password. There is no password: sign-in is an emailed
            link, and offering to change one would describe a mechanism that
            does not exist. */}
        <p className="rounded-md border border-subtle bg-sunken p-16 type-body-s text-secondary">
          There is no password on this account. You sign in with a link we email
          you, which expires after fifteen minutes and works once.
        </p>
      </section>

      <section className="flex flex-col gap-16">
        <h2 className="type-heading-m text-primary">What we email you</h2>

        <fieldset className="flex flex-col gap-12">
          <legend className="mb-8 type-label text-primary">Send me email</legend>
          {KINDS.map((kind) => (
            <label key={kind.key} className="flex items-start gap-12">
              <input
                type="checkbox"
                checked={prefs[kind.key]}
                onChange={(e) =>
                  setPrefs((p) => ({ ...p, [kind.key]: e.target.checked }))
                }
                className="mt-4 size-16 shrink-0 rounded-xs border border-default accent-[var(--action-primary-bg)] outline-focus outline-offset-2 focus-visible:outline-2"
              />
              <span className="flex flex-col gap-4">
                <span className="type-body-m text-primary">{kind.label}</span>
                <span className="type-caption text-muted">{kind.help}</span>
              </span>
            </label>
          ))}
        </fieldset>

        <fieldset className="flex flex-col gap-12">
          <legend className="mb-8 type-label text-primary">
            Summary of everything else
          </legend>
          {DIGESTS.map((option) => (
            <label key={option.value} className="flex items-center gap-12">
              <input
                type="radio"
                name="digest"
                checked={prefs.digest === option.value}
                onChange={() => setPrefs((p) => ({ ...p, digest: option.value }))}
                className="size-16 accent-[var(--action-primary-bg)] outline-focus outline-offset-2 focus-visible:outline-2"
              />
              <span className="type-body-m text-primary">{option.label}</span>
            </label>
          ))}
        </fieldset>

        <div className="flex flex-wrap items-center gap-16">
          <Button
            onClick={() => run(() => saveSettings({ name, notifications: prefs }))}
            disabled={!dirty}
            loading={pending}
            loadingLabel="Saving"
          >
            Save
          </Button>
          <p className="type-body-s text-muted" role="status">
            {dirty ? "Unsaved changes." : (notice ?? "No unsaved changes.")}
          </p>
        </div>
      </section>

      <section className="flex flex-col gap-16">
        <h2 className="type-heading-m text-primary">Your programmes</h2>

        {settings.programs.length === 0 ? (
          <p className="type-body-m text-secondary">
            You are not in a programme yet.
          </p>
        ) : (
          <ul className="flex flex-col gap-12">
            {settings.programs.map((programme) => (
              <li
                key={programme.participationId}
                className="flex flex-wrap items-center justify-between gap-12 rounded-md border border-subtle bg-surface p-16"
              >
                <div className="flex min-w-0 flex-col gap-4">
                  <p className="type-body-m text-primary">
                    {programme.programName}
                  </p>
                  <p className="type-body-s text-muted">
                    {programme.organisationName} ·{" "}
                    {programme.isCoordinator
                      ? "you coordinate this"
                      : `you are a ${programme.role}`}
                    {programme.muted ? " · email muted" : ""}
                  </p>
                </div>

                <div className="flex flex-wrap gap-8">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={pending}
                    onClick={() =>
                      run(() =>
                        setMuted({
                          participationId: programme.participationId,
                          muted: !programme.muted,
                        }),
                      )
                    }
                  >
                    {programme.muted ? "Unmute" : "Mute email"}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={pending}
                    onClick={() => setLeaving(programme)}
                  >
                    Leave
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {error && (
        <p role="alert" className="type-body-m text-danger">
          {error}
        </p>
      )}

      <ConfirmDialog
        open={leaving !== null}
        title={`Leave ${leaving?.programName ?? "this programme"}?`}
        confirmLabel="Leave it"
        confirmVariant="danger"
        busy={pending}
        busyLabel="Leaving"
        onCancel={() => setLeaving(null)}
        onConfirm={() =>
          leaving && run(() => leaveProgram(leaving.participationId))
        }
        body={
          <div className="flex flex-col gap-12">
            <p>
              Any strand you hold here ends, and the other person is told. The
              conversation is kept and stays readable to both of you.
            </p>
            <p>
              If you only want the email to stop, mute it instead — that leaves
              everything else as it is.
            </p>
          </div>
        }
      />
    </div>
  );
}
