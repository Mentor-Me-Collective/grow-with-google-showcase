import type { Schemas } from "@/lib/api/client";

type Summary = Schemas["FairnessSummary"];

const percent = (n: number) => `${Math.round(n * 100)}%`;

/**
 * Design direction 9: this sits above the pair list, full width, always.
 *
 * "A coordinator must see coverage, load spread, and the quality gap between
 * priority bands before she sees a single name. Putting the pairs first would
 * train her to optimise pair by pair, which is precisely the behaviour the
 * product exists to prevent. This is a design decision with an ethical payload
 * and it should not be reordered for convenience."
 */
export function FairnessSummary({ summary }: { summary: Summary }) {
  return (
    <section className="flex flex-col gap-24 rounded-lg border border-subtle bg-surface p-24">
      <h2 className="type-heading-m text-primary">Before you look at names</h2>

      <div className="flex flex-wrap gap-32">
        <Figure
          label="Coverage"
          value={percent(summary.coverageRate)}
          note={`${summary.matchedCount} of ${summary.totalMentees} mentees matched`}
        />
        <Figure
          label="Unmatched"
          value={String(summary.unmatchedCount)}
          note={
            summary.unmatchedCount === 0
              ? "Everyone has a mentor"
              : "Each one needs a reason and a next step"
          }
        />
      </div>

      <BandGap bands={summary.priorityBands} />
      <MentorLoad load={summary.mentorLoad} />
      <ScoreDistribution buckets={summary.scoreDistribution} />
    </section>
  );
}

/** Numbers at display size in the mono face, per 5.3. */
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

/**
 * The comparison that makes a run defensible. The gap is stated in words as
 * well as drawn, because it is the number a coordinator has to be able to
 * defend to the mentees who came out worst.
 */
function BandGap({ bands }: { bands: Summary["priorityBands"] }) {
  const present = bands.filter((b) => b.menteeCount > 0);
  const means = present.map((b) => b.meanScore);
  const gap = means.length > 1 ? Math.max(...means) - Math.min(...means) : 0;

  return (
    <div className="flex flex-col gap-12">
      <h3 className="type-label text-muted">Match quality by priority band</h3>

      <table className="w-full border-collapse">
        <caption className="sr-only">
          Mean and median match score for each priority band
        </caption>
        <thead>
          <tr className="border-b border-subtle">
            <th scope="col" className="py-8 text-left type-label text-secondary">
              Band
            </th>
            <th scope="col" className="py-8 text-right type-label text-secondary">
              Mentees
            </th>
            <th scope="col" className="py-8 text-right type-label text-secondary">
              Mean
            </th>
            <th scope="col" className="py-8 text-right type-label text-secondary">
              Median
            </th>
          </tr>
        </thead>
        <tbody>
          {present.map((band) => (
            <tr key={band.band} className="border-b border-subtle">
              <th scope="row" className="py-8 text-left type-body-s text-primary">
                {capitalise(band.band)} priority
              </th>
              <td className="py-8 text-right type-data-m text-primary">
                {band.menteeCount}
              </td>
              <td className="py-8 text-right type-data-m text-primary">
                {band.meanScore.toFixed(2)}
              </td>
              <td className="py-8 text-right type-data-m text-primary">
                {band.medianScore.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="type-body-s text-secondary">
        {means.length < 2
          ? "Only one band has mentees in it, so there is no gap to compare."
          : gap < 0.05
            ? `The gap between the best and worst band average is ${gap.toFixed(2)}. High-priority mentees came out about as well as everyone else.`
            : `The gap between the best and worst band average is ${gap.toFixed(2)}. That is wide enough to need an explanation before you publish.`}
      </p>
    </div>
  );
}

/**
 * Over capacity is the thing worth seeing, so it is named in words rather than
 * left to the reader to spot by comparing two numbers on every row.
 */
function MentorLoad({ load }: { load: Summary["mentorLoad"] }) {
  const over = load.filter((m) => m.load > m.capacity);
  const idle = load.filter((m) => m.load === 0);

  return (
    <div className="flex flex-col gap-12">
      <h3 className="type-label text-muted">Mentor load</h3>

      <ul className="flex flex-col gap-8">
        {load.map((m) => {
          const ceiling = Math.max(m.capacity, m.load, 1);
          return (
            <li
              key={m.mentor.participationId}
              className="flex items-center gap-12"
            >
              <span className="min-w-0 flex-1 truncate type-body-s text-primary">
                {m.mentor.name}
              </span>
              <span
                aria-hidden="true"
                className="flex h-8 w-96 items-center gap-4 overflow-hidden rounded-sm bg-sunken"
              >
                <span
                  className={`h-8 rounded-sm ${m.load > m.capacity ? "bg-danger" : "bg-accent"}`}
                  style={{ inlineSize: `${(m.load / ceiling) * 100}%` }}
                />
              </span>
              <span className="w-64 shrink-0 text-right type-data-m text-primary">
                {m.load}/{m.capacity}
              </span>
            </li>
          );
        })}
      </ul>

      <p className="type-body-s text-secondary">
        {over.length > 0
          ? `${listNames(over.map((m) => m.mentor.name))} ${over.length === 1 ? "is" : "are"} over the capacity they set. Publishing this run holds them to it.`
          : "Nobody is over the capacity they set."}
        {idle.length > 0 &&
          ` ${listNames(idle.map((m) => m.mentor.name))} ${idle.length === 1 ? "has" : "have"} no mentee at all.`}
      </p>
    </div>
  );
}

function ScoreDistribution({
  buckets,
}: {
  buckets: Summary["scoreDistribution"];
}) {
  const tallest = Math.max(...buckets.map((b) => b.count), 1);

  return (
    <div className="flex flex-col gap-12">
      <h3 className="type-label text-muted">Score distribution</h3>

      {/* The bars are the shape of the table below them, not a substitute for
          it: a screen reader gets the counts as a list, not as decoration. */}
      <ul className="flex items-end gap-8" aria-hidden="true">
        {buckets.map((bucket) => (
          <li
            key={`${bucket.rangeStart}`}
            className="flex min-w-0 flex-1 flex-col items-center gap-4"
          >
            <span
              className="w-full rounded-xs bg-accent"
              style={{ blockSize: `${Math.max((bucket.count / tallest) * 64, 2)}px` }}
            />
            <span className="type-caption text-muted">
              {bucket.rangeStart.toFixed(1)}
            </span>
          </li>
        ))}
      </ul>

      <p className="type-body-s text-secondary">
        {buckets
          .filter((b) => b.count > 0)
          .map(
            (b) =>
              `${b.count} between ${b.rangeStart.toFixed(1)} and ${b.rangeEnd.toFixed(1)}`,
          )
          .join(", ")}
        .
      </p>
    </div>
  );
}

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

function listNames(names: string[]) {
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}
