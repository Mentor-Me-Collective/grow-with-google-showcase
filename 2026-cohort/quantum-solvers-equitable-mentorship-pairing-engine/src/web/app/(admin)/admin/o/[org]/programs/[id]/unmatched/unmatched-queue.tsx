"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { pairManually } from "./actions";

type Entry = Schemas["UnmatchedEntry"];
type Mentor = Schemas["AvailableMentor"];

/**
 * Every reason has a different remedy, so each one says what it is and what
 * would fix it. A queue where every row reads "unmatched" tells a coordinator
 * nothing she can act on.
 */
const REASONS: Record<Schemas["UnmatchedReason"], { label: string; remedy: string }> = {
  no_mentor_capacity: {
    label: "No mentor had room",
    remedy: "Needs a mentor with capacity, or a mentor raising their cap.",
  },
  no_skill_overlap: {
    label: "No shared skills with anyone free",
    remedy: "Consider a group strand, or pair on the closest overlap by hand.",
  },
  joined_after_run: {
    label: "Joined after the run",
    remedy: "Will be picked up by the next run. Nothing needed now.",
  },
  incomplete_profile: {
    label: "Profile too incomplete to match",
    remedy: "Needs the participant, not you. A nudge is the action here.",
  },
  all_candidates_declined: {
    label: "Everyone suggested declined",
    remedy: "Pair by hand, or widen the criteria before the next run.",
  },
};

export function UnmatchedQueue({
  entries,
  availableMentors,
  programId,
}: {
  entries: Entry[];
  availableMentors: Mentor[];
  programId: string;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [pairing, setPairing] = useState<Entry | null>(null);
  const [mentorId, setMentorId] = useState<string>("");
  const [error, setError] = useState<string | undefined>();

  if (entries.length === 0) {
    return (
      <div className="rounded-lg border border-subtle bg-surface">
        <EmptyState
          markId="unmatched-empty"
          title="Everyone has a strand."
          body="Nobody in this programme is waiting. When a run leaves someone out, they appear here with the reason why."
        />
      </div>
    );
  }

  const confirm = () =>
    startTransition(async () => {
      if (!pairing || !mentorId) return;
      const result = await pairManually({
        programId,
        menteeParticipationId: pairing.participationId,
        mentorParticipationId: mentorId,
      });
      if (result.ok) {
        setPairing(null);
        setMentorId("");
        setError(undefined);
        router.refresh();
      } else {
        setError(result.message);
      }
    });

  const chosen = availableMentors.find((m) => m.participationId === mentorId);

  return (
    <div className="flex flex-col gap-16">
      {error && (
        <p role="alert" className="type-body-s text-danger">
          {error}
        </p>
      )}

      <ul className="flex flex-col gap-12">
        {entries.map((entry) => {
          const reason = REASONS[entry.reason];
          return (
            <li
              key={entry.participationId}
              className="flex flex-col gap-12 rounded-md border border-subtle bg-surface p-16"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-12">
                <h2 className="type-heading-s text-primary">{entry.name}</h2>
                <span className="type-body-s text-muted">
                  {capitalise(entry.role)}
                  {entry.timezone ? ` · ${entry.timezone}` : ""}
                  {` · profile ${Math.round(entry.profileCompleteness * 100)}%`}
                </span>
              </div>

              <div className="flex flex-col gap-4">
                <p className="type-body-m text-primary">{reason.label}</p>
                <p className="type-body-s text-secondary">{reason.remedy}</p>
              </div>

              {entry.skills && entry.skills.length > 0 && (
                <p className="type-body-s text-muted">
                  {entry.skills.join(", ")}
                </p>
              )}

              {/* Only a mentee can be paired into a mentor here. A mentor with
                  no mentee is waiting on intake, not on this button. */}
              {entry.role === "mentee" && availableMentors.length > 0 && (
                <div className="flex">
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setPairing(entry);
                      setMentorId(availableMentors[0].participationId);
                    }}
                  >
                    Pair by hand
                  </Button>
                </div>
              )}
            </li>
          );
        })}
      </ul>

      <ConfirmDialog
        open={pairing !== null}
        title={pairing ? `Pair ${pairing.name} with a mentor` : ""}
        confirmLabel="Create the strand"
        busy={pending}
        busyLabel="Creating"
        onCancel={() => {
          setPairing(null);
          setError(undefined);
        }}
        onConfirm={confirm}
        body={
          <div className="flex flex-col gap-16">
            <label className="flex flex-col gap-8">
              <span className="type-label text-primary">Mentor</span>
              <select
                value={mentorId}
                onChange={(e) => setMentorId(e.target.value)}
                className="h-field rounded-sm border border-default bg-surface px-12 type-body-m text-primary focus:border-accent focus:outline-none focus:ring-3 focus:ring-focus-halo"
              >
                {availableMentors.map((m) => (
                  <option key={m.participationId} value={m.participationId}>
                    {m.name} — {m.load} of {m.capacity} places used
                  </option>
                ))}
              </select>
            </label>

            <p>
              This creates an active strand immediately and both people are
              told. It is recorded as a manual pairing, so reports can tell it
              apart from the algorithm&apos;s.
            </p>

            {chosen && chosen.load + 1 >= chosen.capacity && (
              <p className="type-body-s text-secondary">
                This fills {chosen.name}&apos;s last place.
              </p>
            )}
          </div>
        }
      />
    </div>
  );
}

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
