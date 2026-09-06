"use client";

import { useState } from "react";
import type { Schemas } from "@/lib/api/client";

type RunDetail = Schemas["RunDetail"];

/**
 * The engine, narrated with this run's own figures.
 *
 * Written because "0.85" and "high" are not explanations, and a coordinator who
 * cannot say why a cohort came out this way cannot defend it to the people in
 * it. Every number below is read off the run rather than illustrated, so the
 * section cannot drift from what actually happened.
 */
export function HowScored({ run }: { run: RunDetail }) {
  const [open, setOpen] = useState(false);
  const summary = run.fairnessSummary;
  if (!summary) return null;

  const mentors = summary.mentorLoad?.length ?? 0;
  const mentees = summary.totalMentees ?? 0;
  const possible = mentees * mentors;

  // Any pair's breakdown names the same questions: the recipe is one per run.
  const sample = run.pairs.find((p) => (p.scoreBreakdown?.length ?? 0) > 0);
  const scored = sample?.scoreBreakdown ?? [];
  const unscored = sample?.unscored ?? [];
  const equity = sample?.priorityBreakdown ?? [];

  const capacity = summary.mentorLoad?.reduce((n, m) => n + m.capacity, 0) ?? 0;

  return (
    <section className="flex flex-col gap-16 rounded-lg border border-subtle bg-surface p-24">
      <div className="flex flex-wrap items-baseline justify-between gap-12">
        <h2 className="type-heading-m text-primary">How this run was scored</h2>
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-controls="how-scored-body"
          className="pointer-coarse:min-h-field px-8 type-body-s text-link underline underline-offset-4 outline-focus outline-offset-2 focus-visible:outline-2"
        >
          {open ? "Hide the working" : "Show the working"}
        </button>
      </div>

      <p className="type-body-m text-secondary">
        Four stages, kept apart so each one can be checked on its own.
      </p>

      {open && (
        <ol id="how-scored-body" className="flex flex-col gap-16">
          <Stage
            n={1}
            title="Who could work with whom"
            figure={possible > 0 ? `up to ${possible.toLocaleString()} pairings` : undefined}
          >
            {mentees} mentees and {mentors} mentors, so at most{" "}
            {possible.toLocaleString()} combinations before any rule is applied.
            Hard constraints — a shared skill, a workable time zone, no conflict
            of interest — then remove pairs outright rather than scoring them
            low, because a heavy weight can be argued down by a strong score
            elsewhere and a rule cannot.
          </Stage>

          <Stage
            n={2}
            title="How good each surviving pair would be"
            figure={`${scored.length} of ${scored.length + unscored.length} questions`}
          >
            Each pair is scored 0 to 1 on the questions the programme weights.
            {scored.length > 0 && (
              <>
                {" "}
                This run compared{" "}
                <strong className="text-primary">
                  {scored.map((s) => s.label).join(", ")}
                </strong>
                .
              </>
            )}
            {unscored.length > 0 && (
              <>
                {" "}
                {unscored.length}{" "}
                {unscored.length === 1 ? "question" : "questions"} contributed
                nothing, being free text with no taxonomy behind it — counting
                them would reward writing style rather than suitability.
              </>
            )}
          </Stage>

          <Stage
            n={3}
            title="Who most needs the structured route"
            figure={
              equity.length > 0 ? `${equity.length} equity questions` : undefined
            }
          >
            Priority is computed per mentee, separately from fit, and never
            mixed into it — a single number combining &ldquo;how good is this
            pairing&rdquo; with &ldquo;who most needs one&rdquo; cannot be
            explained afterwards. Scales are
            inverted, so less experience and lower confidence raise it.
            {summary.priorityBands && summary.priorityBands.length > 0 && (
              <>
                {" "}
                This cohort came out{" "}
                {summary.priorityBands
                  .filter((b) => b.menteeCount > 0)
                  .map((b) => `${b.menteeCount} ${b.band}`)
                  .join(", ")}
                .
              </>
            )}
          </Stage>

          <Stage
            n={4}
            title="Solving the whole cohort at once"
            figure={`${summary.matchedCount} matched, ${summary.unmatchedCount} not`}
          >
            Not one mentee at a time. Taking each mentee&apos;s best available mentor
            in turn looks reasonable and is not: an early pick consumes a mentor
            a later mentee needed more, and every individual choice can be
            sensible while the cohort comes out worse. So every eligible pair
            goes into one cost matrix, solved in a single step, subject to
            mentor capacity{capacity > 0 ? ` (${capacity} places across ${mentors} mentors)` : ""}
            , a coverage floor, and bounded priority weighting.
            {summary.unmatchedCount > 0 && (
              <>
                {" "}
                The {summary.unmatchedCount} unmatched carry a reason code
                rather than being forced onto whoever was left.
              </>
            )}
          </Stage>
        </ol>
      )}
    </section>
  );
}

function Stage({
  n,
  title,
  figure,
  children,
}: {
  n: number;
  title: string;
  figure?: string;
  children: React.ReactNode;
}) {
  return (
    <li className="flex flex-col gap-4 border-l border-subtle pl-16">
      <div className="flex flex-wrap items-baseline gap-8">
        <span className="type-label text-muted">Stage {n}</span>
        <h3 className="type-heading-s text-primary">{title}</h3>
      </div>
      {figure && <p className="type-data-m text-secondary">{figure}</p>}
      <p className="type-body-s text-secondary">{children}</p>
    </li>
  );
}
