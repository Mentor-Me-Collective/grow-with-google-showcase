import Link from "next/link";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireParticipation } from "@/lib/auth/guard";
import { buttonClasses } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { StrandCard, StrandCardError } from "@/components/strand/strand-card";

export const metadata = { title: "Strands" };

/**
 * Architecture 4.6 gives two filters, active and ended. They are links rather
 * than a client-side toggle: the filter is the address of the list, so it
 * survives a refresh and can be sent to someone.
 *
 * The other three strand states are deliberately unreachable here. A draft
 * belongs to a matching run nobody has published, and discarded is the state
 * that says it never happened; neither is a thing a participant has.
 */
const FILTERS = [
  { key: "active", label: "Active" },
  { key: "ended", label: "Ended" },
] as const;

type FilterKey = (typeof FILTERS)[number]["key"];

const isFilter = (value: unknown): value is FilterKey =>
  FILTERS.some((f) => f.key === value);

export default async function StrandsPage(
  props: PageProps<"/o/[org]/p/[program]/strands">,
) {
  const { org, program } = await props.params;
  const { state } = await props.searchParams;
  const result = await requireParticipation(org, program);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const filter: FilterKey = isFilter(state) ? state : "active";
  const base = `/o/${org}/p/${program}`;

  const { data: strands, error } = await serverApi.GET(
    "/programs/{programId}/strands",
    {
      params: {
        path: { programId: result.participation.programId },
        query: { state: filter },
      },
    },
  );

  return (
    <div className="flex flex-col gap-24">
      <h1 className="type-heading-l text-primary">Strands</h1>

      <nav aria-label="Filter strands" className="flex gap-8 border-b border-subtle">
        {FILTERS.map(({ key, label }) => {
          const current = key === filter;
          return (
            <Link
              key={key}
              href={key === "active" ? `${base}/strands` : `${base}/strands?state=${key}`}
              aria-current={current ? "page" : undefined}
              className={[
                // The bottom rule is the selected marker, so it cannot be the
                // only one: aria-current carries it for anyone not seeing the
                // border, and the label weight shifts with it.
                "-mb-px border-b-2 px-12 py-8 type-body-m",
                "pointer-coarse:min-h-field inline-flex items-center",
                "rounded-t-sm outline-focus outline-offset-2 focus-visible:outline-2",
                current
                  ? "border-accent text-primary"
                  : "border-transparent text-secondary hover:text-primary",
              ].join(" ")}
            >
              {label}
            </Link>
          );
        })}
      </nav>

      {error ? (
        <StrandCardError />
      ) : (
        <StrandList
          strands={strands ?? []}
          base={base}
          filter={filter}
          firstName={result.session.account.name.split(" ")[0]}
        />
      )}
    </div>
  );
}

function StrandList({
  strands,
  base,
  filter,
  firstName,
}: {
  strands: Schemas["StrandSummary"][];
  base: string;
  filter: FilterKey;
  firstName: string;
}) {
  if (strands.length === 0) {
    return (
      <div className="rounded-lg border border-subtle bg-surface">
        {filter === "active" ? (
          <EmptyState
            markId="strands-none-active"
            title="No strands yet."
            body={`${firstName}, matching has not paired you yet. When it does, whoever you are matched with turns up here and you will get an email the same day.`}
            action={
              <Link href={base} className={buttonClasses({ size: "lg" })}>
                Back to home
              </Link>
            }
          />
        ) : (
          <EmptyState
            markId="strands-none-ended"
            title="Nothing has ended."
            body="Strands that finish stay here, with their conversations, so you can read back over them."
          />
        )}
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-12">
      {strands.map((strand) => (
        <li key={strand.id}>
          <StrandCard strand={strand} href={`${base}/strands/${strand.id}`} />
        </li>
      ))}
    </ul>
  );
}
