import Link from "next/link";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { buttonClasses } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export const metadata = { title: "Dashboard" };

const longDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(new Date(iso));

/**
 * Architecture 5.1. Opened daily during a live cohort, so it answers one
 * question — is anything waiting on me — before it answers any other.
 *
 * `architecture.md` gives this route twice: 5.1 calls it the dashboard and 5.22
 * calls it organisation settings. The sidebar points Dashboard here, so that is
 * what it is; org settings needs a route of its own.
 */
export default async function DashboardPage(
  props: PageProps<"/admin/o/[org]">,
) {
  const { org } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  // The sidebar's selected programme. An organisation with several would put a
  // switcher above this; the shell already owns that decision.
  const programme = result.programmes[0];
  const base = `/admin/o/${org}/programs/${programme.programId}`;

  const { data, error } = await serverApi.GET("/programs/{programId}/dashboard", {
    params: { path: { programId: programme.programId } },
  });

  if (error || !data) {
    return (
      <div className="flex flex-col gap-16">
        <h1 className="type-heading-l text-primary">{programme.programName}</h1>
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The dashboard did not load. Nothing is wrong with the programme; this
          is a connection problem. Reload to try again.
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-48">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">{programme.programName}</h1>
        <p className="type-body-m text-secondary">
          Where the cohort stands today.
        </p>
      </div>

      {/* The attention list comes first. Counts say how things are; this says
          what to do about them, and that is the reason to open the page. */}
      <Attention items={data.attention} base={base} />

      <section className="flex flex-col gap-16">
        <h2 className="type-label text-muted">The cohort</h2>
        <div className="flex flex-wrap gap-32">
          <Figure
            label="Mentees"
            value={String(data.menteeCount)}
            note={
              data.recruitmentGoal
                ? `${Math.round((data.menteeCount / data.recruitmentGoal) * 100)}% of the ${data.recruitmentGoal} you set out to recruit`
                : "No recruitment goal set"
            }
          />
          <Figure
            label="Mentors"
            value={String(data.mentorCount)}
            note={ratioNote(data.menteeCount, data.mentorCount)}
          />
          <Figure
            label="Matched"
            value={`${data.matchedCount}`}
            note={
              data.unmatchedCount === 0
                ? "Everyone has a strand"
                : `${data.unmatchedCount} still without one`
            }
          />
          <Figure
            label="Active strands"
            value={String(data.activeStrands)}
            note={
              data.quietStrands === 0
                ? "None have gone quiet"
                : `${data.quietStrands} quiet for a fortnight or more`
            }
          />
          <Figure
            label="Sessions this week"
            value={String(data.sessionsLoggedThisWeek)}
            note="Logged, not scheduled. Logging is the signal that matters."
          />
        </div>
      </section>

      {data.upcomingMilestone && (
        <section className="flex flex-col gap-8">
          <h2 className="type-label text-muted">Next milestone</h2>
          <p className="type-body-m text-primary">
            {data.upcomingMilestone.title}
          </p>
          <p className="type-body-s text-muted">
            Due {longDate(data.upcomingMilestone.dueAt)}.{" "}
            <Link href={`${base}/milestones`} className="text-link underline">
              Edit the arc
            </Link>
          </p>
        </section>
      )}
    </div>
  );
}

/**
 * Every item links to the page that resolves it, per 5.1. An item with nowhere
 * to go would be a worry rather than a task.
 */
function Attention({
  items,
  base,
}: {
  items: Schemas["AttentionItem"][];
  base: string;
}) {
  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-subtle bg-surface">
        <EmptyState
          markId="dashboard-clear"
          title="Nothing needs you today."
          body="No applications waiting, nobody unmatched, and every strand has been written in this fortnight. This is what a healthy cohort looks like."
        />
      </div>
    );
  }

  return (
    <section className="flex flex-col gap-16">
      <h2 className="type-label text-muted">Needs a human</h2>
      <ul className="flex flex-col gap-12">
        {items.map((item) => (
          <li
            key={item.kind}
            className="flex flex-wrap items-center justify-between gap-16 rounded-md border border-subtle bg-surface p-16"
          >
            <div className="flex min-w-0 flex-col gap-4">
              <p className="type-heading-s text-primary">{item.title}</p>
              {item.body && (
                <p className="type-body-s text-secondary">{item.body}</p>
              )}
            </div>
            <Link
              href={`${base}${item.href}`}
              className={buttonClasses({ variant: "secondary" })}
            >
              {item.actionLabel}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Figure({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-4">
      <h3 className="type-label text-muted">{label}</h3>
      <p className="type-data-l text-primary">{value}</p>
      <p className="type-body-s text-secondary">{note}</p>
    </div>
  );
}

/** Stated as a ratio because that is how a coordinator thinks about recruiting. */
function ratioNote(mentees: number, mentors: number) {
  if (mentors === 0) return "No mentors yet";
  const ratio = mentees / mentors;
  return `${ratio.toFixed(1)} mentees per mentor`;
}
