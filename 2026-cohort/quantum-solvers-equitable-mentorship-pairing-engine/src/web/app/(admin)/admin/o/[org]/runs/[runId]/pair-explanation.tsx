import type { Schemas } from "@/lib/api/client";

type Pair = Schemas["DraftPair"];
type Score = Schemas["ScoreContribution"];
type Priority = Schemas["PriorityContribution"];

const BAND_FLOOR: Record<string, string> = {
  high: "0.66 and above",
  medium: "0.33 to 0.66",
  low: "below 0.33",
};

/** Kept as a plain multiplication rather than a rounded total, so a coordinator
 *  can follow the arithmetic to the score she is being asked to publish. */
function weighted(rows: { weight: number; value: number }[]) {
  const total = rows.reduce((sum, r) => sum + r.value * r.weight, 0);
  const used = rows.reduce((sum, r) => sum + r.weight, 0);
  return { total, used, result: used ? total / used : 0 };
}

function asked(row: Score) {
  if (row.menteeAnswer && row.mentorAnswer) return "Asked of both";
  if (row.menteeAnswer) return "Asked of the mentee";
  if (row.mentorAnswer) return "Asked of the mentor";
  return "Neither answered";
}

/**
 * Design direction 9 puts distribution before names; this is the layer below
 * that, for the moment a coordinator has picked one row and wants to know why.
 *
 * Every number here is the run's own record rather than a recomputation, and
 * the panel says out loud that it is partial: in a whole-cohort assignment the
 * real reason a mentee got this mentor is often about a third person.
 */
export function PairExplanation({ pair }: { pair: Pair }) {
  const scored = pair.scoreBreakdown ?? [];
  const unscored = pair.unscored ?? [];
  const priority = pair.priorityBreakdown ?? [];

  if (scored.length === 0 && priority.length === 0) {
    return (
      <p className="type-body-s text-secondary">
        This run was made before the pairing detail was kept, so there is
        nothing recorded about how it reached this pair.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-32">
      {scored.length > 0 && (
        <section className="flex flex-col gap-12">
          <h4 className="type-label text-secondary">What was compared</h4>

          <ul className="flex flex-col gap-8">
            {scored.map((row) => (
              <Contribution key={row.fieldId} row={row} />
            ))}
          </ul>

          <Arithmetic
            rows={scored.map((r) => ({
              weight: r.weight,
              value: r.contribution,
            }))}
            result={pair.score}
            caption="Each answer scored 0 to 1, weighted, then divided by the weight of the questions that could be compared — not the weight of every question, so a pair is never penalised for something neither person was asked."
          />
        </section>
      )}

      {unscored.length > 0 && (
        <section className="flex flex-col gap-8">
          <h4 className="type-label text-secondary">
            Not compared ({unscored.length})
          </h4>
          <p className="type-body-s text-primary">{unscored.join(" · ")}</p>
          <p className="type-body-s text-secondary">
            Free text, with no taxonomy behind it yet. It contributes nothing
            rather than a similarity invented from string overlap, which would
            reward writing style rather than suitability.
          </p>
        </section>
      )}

      {priority.length > 0 && (
        <section className="flex flex-col gap-12">
          <h4 className="type-label text-secondary">
            Why this mentee is {pair.priorityBand} priority
          </h4>

          <ul className="flex flex-col gap-8">
            {priority.map((row) => (
              <PriorityRow key={row.fieldId} row={row} />
            ))}
          </ul>

          <Arithmetic
            rows={priority.map((r) => ({ weight: r.weight, value: r.value }))}
            result={pair.priorityScore ?? 0}
            suffix={` — ${pair.priorityBand} is ${BAND_FLOOR[pair.priorityBand] ?? "a band"}`}
            caption="Scales are inverted before they are weighted, so less experience and lower confidence raise the score. Priority tilts a close call; it never lets a weaker pairing beat a stronger one."
          />
        </section>
      )}

      <p className="type-body-s text-secondary">
        This names the strongest signals. It is not the whole reason — in a
        whole-cohort assignment a mentee often gets her second choice because
        somebody else had no other option, and that cannot be shown on one row.
      </p>
    </div>
  );
}

function Contribution({ row }: { row: Score }) {
  return (
    <li className="flex flex-col gap-4 rounded-md border border-subtle bg-page p-12">
      <div className="flex flex-wrap items-baseline justify-between gap-8">
        <span className="type-body-s text-primary">{row.label}</span>
        <span className="type-data-m text-secondary">
          {row.contribution.toFixed(2)} × {row.weight}
        </span>
      </div>

      <span className="type-label text-secondary">
        {asked(row)} · {row.direction}
      </span>

      {row.menteeAnswer && (
        <span className="type-body-s text-secondary">
          Mentee: {row.menteeAnswer}
        </span>
      )}
      {row.mentorAnswer && (
        <span className="type-body-s text-secondary">
          Mentor: {row.mentorAnswer}
        </span>
      )}
    </li>
  );
}

function PriorityRow({ row }: { row: Priority }) {
  return (
    <li className="flex flex-col gap-4 rounded-md border border-subtle bg-page p-12">
      <div className="flex flex-wrap items-baseline justify-between gap-8">
        <span className="type-body-s text-primary">{row.label}</span>
        <span className="type-data-m text-secondary">
          {row.value.toFixed(2)} × {row.weight}
        </span>
      </div>
      {row.answer && (
        <span className="type-body-s text-secondary">Answer: {row.answer}</span>
      )}
    </li>
  );
}

function Arithmetic({
  rows,
  result,
  caption,
  suffix,
}: {
  rows: { weight: number; value: number }[];
  result: number;
  caption: string;
  suffix?: string;
}) {
  const { total, used } = weighted(rows);
  return (
    <div className="flex flex-col gap-4">
      <p className="type-data-m text-primary">
        {total.toFixed(1)} ÷ {used} = {result.toFixed(2)}
        {suffix}
      </p>
      <p className="type-body-s text-secondary">{caption}</p>
    </div>
  );
}
