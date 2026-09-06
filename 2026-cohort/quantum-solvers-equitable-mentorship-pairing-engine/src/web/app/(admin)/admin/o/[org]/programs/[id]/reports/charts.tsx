import type { Schemas } from "@/lib/api/client";

/**
 * Charts are hand-drawn SVG on the token palette rather than a charting
 * dependency. They are simple shapes and the palette is the point: a library
 * would arrive with its own colours and its own type.
 *
 * Every chart is `aria-hidden` and carries the same numbers in text beside it.
 * The drawing is a summary of the figures, never the only copy of them —
 * section 11, and also what makes the printed report readable in grey.
 */

const CHART_HEIGHT = 120;

export function LineChart({
  points,
  caption,
}: {
  points: Schemas["TimePoint"][];
  caption: string;
}) {
  if (points.length < 2) {
    return (
      <p className="type-body-s text-secondary">
        Not enough points in this range to draw a line. {caption}
      </p>
    );
  }

  const max = Math.max(...points.map((p) => p.value), 1);
  const step = 100 / (points.length - 1);
  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${i * step} ${CHART_HEIGHT - (p.value / max) * CHART_HEIGHT}`)
    .join(" ");

  return (
    <div className="flex flex-col gap-8">
      <svg
        viewBox={`0 0 100 ${CHART_HEIGHT}`}
        preserveAspectRatio="none"
        role="presentation"
        aria-hidden="true"
        className="h-96 w-full"
      >
        <path
          d={path}
          fill="none"
          stroke="var(--action-primary-bg)"
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
          strokeLinejoin="round"
        />
      </svg>
      <p className="type-body-s text-secondary">{caption}</p>
    </div>
  );
}

export function BarChart({
  points,
  caption,
  empty,
  format = (n: number) => String(n),
}: {
  points: Schemas["CountPoint"][];
  caption: string;
  /** Why there is nothing here. A section that renders an axis and no bars
      reads as a fault; saying what is missing is the state, not a fallback. */
  empty: string;
  format?: (n: number) => string;
}) {
  if (points.length === 0) {
    return <p className="type-body-s text-secondary">{empty}</p>;
  }

  const max = Math.max(...points.map((p) => p.count), 1);

  return (
    <div className="flex flex-col gap-12">
      <ul aria-hidden="true" className="flex items-end gap-8">
        {points.map((point) => (
          <li key={point.label} className="flex min-w-0 flex-1 flex-col items-center gap-4">
            <span
              className="w-full rounded-xs bg-accent"
              style={{
                blockSize: `${Math.max((point.count / max) * 96, 2)}px`,
              }}
            />
            <span className="truncate type-caption text-muted">{point.label}</span>
          </li>
        ))}
      </ul>

      {/* The same figures as a list, which is what a screen reader and a
          black-and-white printer both get. */}
      <dl className="flex flex-wrap gap-x-24 gap-y-4">
        {points.map((point) => (
          <div key={point.label} className="flex items-baseline gap-8">
            <dt className="type-caption text-muted">{point.label}</dt>
            <dd className="type-data-m text-primary">{format(point.count)}</dd>
          </div>
        ))}
      </dl>

      <p className="type-body-s text-secondary">{caption}</p>
    </div>
  );
}

/** A count at each stage, drawn as narrowing bars so the losses are visible. */
export function Funnel({ stages }: { stages: Schemas["DropOffStage"][] }) {
  const STAGE_WORD: Record<string, string> = {
    applied: "Applied",
    approved: "Approved onto the roster",
    matched: "Matched into a strand",
    first_message: "Sent a first message",
    first_session: "Logged a first session",
    still_active: "Still meeting",
  };

  const top = stages[0]?.count ?? 1;

  return (
    <ol className="flex flex-col gap-8">
      {stages.map((stage, i) => {
        const previous = stages[i - 1]?.count;
        const lost = previous === undefined ? 0 : previous - stage.count;
        return (
          <li key={stage.stage} className="flex flex-col gap-4">
            <div className="flex items-center gap-12">
              <span className="min-w-0 flex-1 truncate type-body-s text-primary">
                {STAGE_WORD[stage.stage] ?? stage.stage}
              </span>
              <span
                aria-hidden="true"
                className="hidden h-8 rounded-sm bg-accent md:block"
                style={{ inlineSize: `${(stage.count / top) * 200}px` }}
              />
              <span className="w-48 shrink-0 text-right type-data-m text-primary">
                {stage.count}
              </span>
            </div>
            {lost > 0 && (
              <p className="type-caption text-muted">
                {lost} {lost === 1 ? "person" : "people"} did not get this far.
              </p>
            )}
          </li>
        );
      })}
    </ol>
  );
}

export function MilestoneProgress({
  items,
}: {
  items: Schemas["MilestoneCompletion"][];
}) {
  if (items.length === 0) {
    return (
      <p className="type-body-s text-secondary">
        This programme has no milestones set, so there is nothing to measure
        progress against.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-12">
      {items.map((item) => {
        const percent = item.total === 0 ? 0 : Math.round((item.completed / item.total) * 100);
        return (
          <li key={item.title} className="flex flex-col gap-4">
            <div className="flex items-center gap-12">
              <span className="min-w-0 flex-1 type-body-s text-primary">
                {item.title}
              </span>
              <div
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={percent}
                aria-label={`${item.title} completion`}
                className="hidden h-8 w-96 overflow-hidden rounded-sm bg-sunken md:block"
              >
                <div
                  className="h-8 rounded-sm bg-accent"
                  style={{ inlineSize: `${percent}%` }}
                />
              </div>
              <span className="w-96 shrink-0 text-right type-data-m text-primary">
                {item.completed} of {item.total}
              </span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
