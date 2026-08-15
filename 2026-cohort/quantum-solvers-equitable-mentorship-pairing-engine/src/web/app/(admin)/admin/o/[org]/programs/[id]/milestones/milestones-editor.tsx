"use client";

import { useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Field, TextareaField } from "@/components/ui/input";
import { saveMilestones } from "./actions";

type Milestone = Schemas["ProgramMilestone"];

/** Local rows carry a key of their own: a new milestone has no id yet, and
 *  React still needs something stable to track it across reorders. */
type Row = {
  key: string;
  id: string | null;
  title: string;
  description: string;
  weekOffset: number;
  strandPrompt: string;
  reminderDaysBefore: number | null;
};

const toRow = (m: Milestone): Row => ({
  key: m.id,
  id: m.id,
  title: m.title,
  description: m.description ?? "",
  weekOffset: m.weekOffset,
  strandPrompt: m.strandPrompt ?? "",
  reminderDaysBefore: m.reminderDaysBefore ?? null,
});

let newRowCount = 0;

export function MilestonesEditor({
  milestones,
  programId,
  cohortStart,
}: {
  milestones: Milestone[];
  programId: string;
  cohortStart: string | null;
}) {
  const [rows, setRows] = useState<Row[]>(milestones.map(toRow));
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | undefined>();
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [removing, setRemoving] = useState<Row | null>(null);

  // Dirty is compared against what the server last gave us, so re-saving an
  // untouched arc is not offered as if it were work.
  const dirty =
    JSON.stringify(sortRows(rows).map(stripKey)) !==
    JSON.stringify(sortRows(milestones.map(toRow)).map(stripKey));

  const update = (key: string, patch: Partial<Row>) =>
    setRows((current) =>
      current.map((r) => (r.key === key ? { ...r, ...patch } : r)),
    );

  /**
   * The arc is ordered by week, so moving a milestone earlier means giving it
   * an earlier week — swapping array positions alone would be undone by the
   * server's own ordering the moment it saved.
   *
   * Two milestones sharing a week are the exception: there the order really is
   * just position, so the rows swap instead.
   */
  const move = (index: number, direction: -1 | 1) =>
    setRows((current) => {
      const ordered = sortRows(current);
      const target = index + direction;
      if (target < 0 || target >= ordered.length) return current;

      const a = ordered[index];
      const b = ordered[target];
      if (a.weekOffset === b.weekOffset) {
        const next = [...ordered];
        [next[index], next[target]] = [next[target], next[index]];
        return next;
      }
      return ordered.map((row) =>
        row.key === a.key
          ? { ...row, weekOffset: b.weekOffset }
          : row.key === b.key
            ? { ...row, weekOffset: a.weekOffset }
            : row,
      );
    });

  const add = () =>
    setRows((current) => [
      ...current,
      {
        key: `new-${++newRowCount}`,
        id: null,
        title: "",
        description: "",
        // Four weeks after the arc currently ends, so a new milestone lands at
        // the bottom rather than colliding with whatever week is last edited.
        weekOffset:
          current.length > 0 ? last(sortRows(current)).weekOffset + 4 : 2,
        strandPrompt: "",
        reminderDaysBefore: 7,
      },
    ]);

  const save = () =>
    startTransition(async () => {
      const result = await saveMilestones({
        programId,
        items: sortRows(rows).map((r, i) => ({
          id: r.id,
          title: r.title.trim(),
          description: r.description.trim() || null,
          weekOffset: r.weekOffset,
          strandPrompt: r.strandPrompt.trim() || null,
          reminderDaysBefore: r.reminderDaysBefore,
          position: i + 1,
        })),
      });

      if (result.ok) {
        setRows(result.milestones.map(toRow));
        setError(undefined);
        setSavedAt(new Date().toISOString());
      } else {
        setError(result.message);
      }
    });

  const untitled = rows.some((r) => !r.title.trim());

  return (
    <div className="flex flex-col gap-24">
      {rows.length === 0 ? (
        <div className="rounded-lg border border-subtle bg-surface">
          <EmptyState
            markId="milestones-empty"
            title="The programme has no arc yet."
            body="Milestones are what turn a match into six months of something. Each one can carry a prompt that appears inside every strand when it lands."
            action={<Button onClick={add}>Add the first milestone</Button>}
          />
        </div>
      ) : (
        <ol className="flex flex-col gap-16">
          {sortRows(rows).map((row, index) => (
            <li
              key={row.key}
              className="flex flex-col gap-16 rounded-lg border border-subtle bg-surface p-24"
            >
              <div className="flex flex-wrap items-center justify-between gap-12">
                <h2 className="type-label text-muted">
                  {cohortStart
                    ? `Week ${row.weekOffset} — ${weekDate(cohortStart, row.weekOffset)}`
                    : `Week ${row.weekOffset}`}
                </h2>

                {/* Reorder is buttons, not drag: section 11 requires every
                    control to be keyboard reachable, and drag alone is not. */}
                <div className="flex items-center gap-8">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => move(index, -1)}
                    disabled={index === 0}
                    aria-label={`Move ${row.title || "this milestone"} earlier`}
                  >
                    Move up
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => move(index, 1)}
                    disabled={index === rows.length - 1}
                    aria-label={`Move ${row.title || "this milestone"} later`}
                  >
                    Move down
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setRemoving(row)}
                    aria-label={`Remove ${row.title || "this milestone"}`}
                  >
                    Remove
                  </Button>
                </div>
              </div>

              <Field
                label="Title"
                value={row.title}
                onChange={(e) => update(row.key, { title: e.target.value })}
                required
                mark="none"
                error={!row.title.trim() ? "Give this milestone a title." : undefined}
              />

              <Field
                label="What should have happened"
                value={row.description}
                onChange={(e) => update(row.key, { description: e.target.value })}
                helper="For you and your team. Participants do not see this."
                mark="none"
              />

              <div className="flex flex-col gap-16 md:flex-row">
                <div className="md:w-participant md:max-w-full">
                  <Field
                    label="Week"
                    type="number"
                    min={0}
                    numeric
                    value={row.weekOffset}
                    onChange={(e) =>
                      update(row.key, { weekOffset: Number(e.target.value) })
                    }
                    helper="Weeks after the cohort starts."
                    mark="none"
                  />
                </div>
                <div className="md:w-participant md:max-w-full">
                  <Field
                    label="Remind this many days before"
                    type="number"
                    min={0}
                    numeric
                    value={row.reminderDaysBefore ?? ""}
                    onChange={(e) =>
                      update(row.key, {
                        reminderDaysBefore:
                          e.target.value === "" ? null : Number(e.target.value),
                      })
                    }
                    helper="Leave empty to send no reminder."
                    mark="none"
                  />
                </div>
              </div>

              <TextareaField
                label="Prompt shown inside strands"
                value={row.strandPrompt}
                onChange={(e) => update(row.key, { strandPrompt: e.target.value })}
                helper="Appears in every strand when this week arrives. Without one, the milestone only exists for you."
                mark="none"
                rows={3}
              />
            </li>
          ))}
        </ol>
      )}

      {rows.length > 0 && (
        <div className="flex">
          <Button variant="secondary" onClick={add}>
            Add a milestone
          </Button>
        </div>
      )}

      {error && (
        <p role="alert" className="type-body-m text-danger">
          {error}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-16 border-t border-subtle pt-24">
        <Button
          size="lg"
          onClick={save}
          disabled={!dirty || untitled}
          loading={pending}
          loadingLabel="Saving the arc"
        >
          Save
        </Button>
        <p className="type-body-s text-muted" role="status">
          {untitled
            ? "Every milestone needs a title before this can save."
            : dirty
              ? "Unsaved changes."
              : savedAt
                ? `Saved ${new Intl.DateTimeFormat("en-GB", {
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                  }).format(new Date(savedAt))}.`
                : "No changes."}
        </p>
      </div>

      <ConfirmDialog
        open={removing !== null}
        title={`Remove ${removing?.title || "this milestone"}?`}
        confirmLabel="Remove"
        confirmVariant="danger"
        onCancel={() => setRemoving(null)}
        onConfirm={() => {
          setRows((current) => current.filter((r) => r.key !== removing?.key));
          setRemoving(null);
        }}
        body={
          <p>
            It leaves the arc when you save. Any prompt written on it goes with
            it.
          </p>
        }
      />
    </div>
  );
}

/**
 * The same ordering the server applies, so what is on screen is what will be
 * stored. Week first, then position for milestones sharing a week.
 */
const sortRows = (rows: Row[]) =>
  [...rows].sort((a, b) => a.weekOffset - b.weekOffset);

/** The local-only tracking key must not count towards whether the arc changed. */
const stripKey = (row: Row) => {
  const copy: Partial<Row> = { ...row };
  delete copy.key;
  return copy;
};
const last = <T,>(items: T[]) => items[items.length - 1];

/** The real date a week offset lands on, so an arc is checkable against a calendar. */
function weekDate(cohortStart: string, weekOffset: number) {
  const date = new Date(`${cohortStart}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + weekOffset * 7);
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(date);
}
