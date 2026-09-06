"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { nudgeStrand, setStrandState } from "./actions";

type Entry = Schemas["StrandMonitorEntry"];
type Health = Schemas["StrandHealth"];

/**
 * Health is a word, never a colour alone: section 11 forbids colour carrying
 * meaning by itself, and a coordinator should not have to learn a legend to
 * read her own programme.
 */
const HEALTH: Record<Health, { label: string; note: string }> = {
  on_track: { label: "On track", note: "Talking, and moving through the arc." },
  slow: {
    label: "Slow",
    note: "Talking, but no milestone reached yet.",
  },
  quiet: {
    label: "Quiet",
    note: "No message for a fortnight or more.",
  },
  not_started: {
    label: "Never started",
    note: "Matched, but nobody has written anything.",
  },
  ended: { label: "Ended", note: "Finished. The conversation stays readable." },
};

const FILTERS: Array<{ key: Health | "all"; label: string }> = [
  { key: "all", label: "All" },
  { key: "not_started", label: "Never started" },
  { key: "quiet", label: "Quiet" },
  { key: "slow", label: "Slow" },
  { key: "on_track", label: "On track" },
  { key: "ended", label: "Ended" },
];

export function StrandMonitor({
  entries,
  healthCounts,
  basePath,
  current,
}: {
  entries: Entry[];
  healthCounts: Schemas["StrandHealthCounts"];
  basePath: string;
  current: Health | "all";
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [notice, setNotice] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();
  const [ending, setEnding] = useState<Entry | null>(null);

  const act = (run: () => Promise<{ ok: boolean; message: string }>) =>
    startTransition(async () => {
      const result = await run();
      setEnding(null);
      if (result.ok) {
        setNotice(result.message);
        setError(undefined);
        router.refresh();
      } else {
        setError(result.message);
        setNotice(undefined);
      }
    });

  const countFor = (key: Health | "all") =>
    key === "all"
      ? Object.values(healthCounts).reduce((a, b) => a + b, 0)
      : healthCounts[key];

  return (
    <div className="flex flex-col gap-16">
      <nav aria-label="Filter by health" className="flex flex-wrap gap-8">
        {FILTERS.map(({ key, label }) => {
          const active = key === current;
          return (
            <Link
              key={key}
              href={key === "all" ? basePath : `${basePath}?health=${key}`}
              aria-current={active ? "page" : undefined}
              className={[
                "pointer-coarse:min-h-field inline-flex items-center gap-8 rounded-sm px-12 py-8 type-body-s",
                "outline-focus outline-offset-2 focus-visible:outline-2",
                active
                  ? "bg-accent text-on-accent"
                  : "border border-default text-secondary hover:text-primary",
              ].join(" ")}
            >
              {label}
              <span className="type-data-m">{countFor(key)}</span>
            </Link>
          );
        })}
      </nav>

      {notice && (
        <p role="status" className="type-body-s text-secondary">
          {notice}
        </p>
      )}
      {error && (
        <p role="alert" className="type-body-s text-danger">
          {error}
        </p>
      )}

      {entries.length === 0 ? (
        <div className="rounded-lg border border-subtle bg-surface">
          <EmptyState
            markId="monitor-empty"
            title={
              current === "all"
                ? "No strands yet."
                : "Nothing in this state."
            }
            body={
              current === "all"
                ? "Strands appear here once a matching run is published. Until then this page has nothing to watch."
                : "Try another filter to see the rest of the programme."
            }
          />
        </div>
      ) : (
        <ul className="flex flex-col gap-12">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className="flex flex-col gap-12 rounded-md border border-subtle bg-surface p-16"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-12">
                <h2 className="type-heading-s text-primary">
                  {names(entry.members)}
                </h2>
                <span className="type-body-s text-muted">
                  {entry.originMode === "manual"
                    ? "Paired by hand"
                    : entry.originMode === "self"
                      ? "Self-matched"
                      : "From a run"}
                </span>
              </div>

              <div className="flex flex-col gap-4">
                <p className="type-body-m text-primary">
                  {HEALTH[entry.health].label}
                </p>
                <p className="type-body-s text-secondary">
                  {HEALTH[entry.health].note}
                </p>
              </div>

              <dl className="flex flex-wrap gap-24">
                <Stat
                  label="Last activity"
                  value={
                    entry.daysSinceActivity === null
                      ? "Never"
                      : entry.daysSinceActivity === 0
                        ? "Today"
                        : `${entry.daysSinceActivity} days ago`
                  }
                />
                <Stat label="Sessions logged" value={String(entry.sessionsLogged)} />
                <Stat
                  label="Milestones"
                  value={`${entry.milestonesCompleted} of ${entry.milestonesTotal}`}
                />
              </dl>

              {entry.state !== "ended" && (
                <div className="flex flex-wrap gap-12">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={pending}
                    onClick={() => act(() => nudgeStrand(entry.id))}
                  >
                    Send a nudge
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={pending}
                    onClick={() =>
                      act(() =>
                        setStrandState({
                          strandId: entry.id,
                          state: entry.state === "paused" ? "active" : "paused",
                        }),
                      )
                    }
                  >
                    {entry.state === "paused" ? "Resume" : "Pause"}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={pending}
                    onClick={() => setEnding(entry)}
                  >
                    End
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={ending !== null}
        title="End this strand?"
        confirmLabel="End it"
        confirmVariant="danger"
        busy={pending}
        busyLabel="Ending"
        onCancel={() => setEnding(null)}
        onConfirm={() =>
          ending &&
          act(() => setStrandState({ strandId: ending.id, state: "ended" }))
        }
        body={
          <div className="flex flex-col gap-12">
            <p>
              {names(ending?.members ?? [])}{" "}
              {(ending?.members.length ?? 0) === 1 ? "is" : "are"} told the
              strand has finished, and it cannot be reopened.
            </p>
            <p>
              The conversation is kept and stays readable to both of them. The
              record of what was said is what people come back for.
            </p>
          </div>
        }
      />
    </div>
  );
}

/** "A and B" for a pair, "A, B and C" for a group. */
function names(members: Array<{ name: string }>) {
  const list = members.map((m) => m.name);
  if (list.length <= 1) return list[0] ?? "This strand";
  if (list.length === 2) return `${list[0]} and ${list[1]}`;
  return `${list.slice(0, -1).join(", ")} and ${list[list.length - 1]}`;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-4">
      <dt className="type-label text-muted">{label}</dt>
      <dd className="type-data-m text-primary">{value}</dd>
    </div>
  );
}
