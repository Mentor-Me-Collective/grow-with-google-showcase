import Link from "next/link";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireParticipation } from "@/lib/auth/guard";
import { Avatar } from "@/components/ui/avatar";
import { EmptyState } from "@/components/ui/empty-state";

export const metadata = { title: "Directory" };

const one = (value: string | string[] | undefined) =>
  typeof value === "string" ? value : undefined;

/**
 * Architecture 4.9. Search and filters live in the URL, so a filtered view is
 * a link rather than a state somebody has to recreate.
 */
export default async function DirectoryPage(
  props: PageProps<"/o/[org]/p/[program]/directory">,
) {
  const { org, program } = await props.params;
  const search = await props.searchParams;
  const result = await requireParticipation(org, program);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const q = one(search.q);
  const skill = one(search.skill);
  const base = `/o/${org}/p/${program}`;

  const { data, error } = await serverApi.GET(
    "/programs/{programId}/directory",
    {
      params: {
        path: { programId: result.participation.programId },
        query: { ...(q ? { q } : {}), ...(skill ? { skill } : {}), pageSize: 100 },
      },
    },
  );

  if (error || !data) {
    return (
      <div className="flex flex-col gap-16">
        <h1 className="type-heading-l text-primary">Directory</h1>
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The directory did not load. Reload to try again.
        </div>
      </div>
    );
  }

  // Not an error: a programme where the coordinator matches everyone has no
  // directory, and saying so is better than an empty list.
  if (!data.selfMatchingEnabled) {
    return (
      <div className="flex flex-col gap-24">
        <h1 className="type-heading-l text-primary">Directory</h1>
        <div className="rounded-lg border border-subtle bg-surface">
          <EmptyState
            markId="directory-off"
            title="This programme matches people itself."
            body="Browsing and choosing your own mentor is switched off here, so the coordinator makes the matches. Your home screen tells you when that happens."
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Directory</h1>
        <p className="type-body-m text-secondary">
          Everyone open to being matched. People already at capacity are shown
          too, so you can see how much room there really is.
        </p>
      </div>

      <Filters basePath={`${base}/directory`} skills={data.skills} q={q} skill={skill} />

      {data.items.length === 0 ? (
        <div className="rounded-lg border border-subtle bg-surface">
          <EmptyState
            markId="directory-empty"
            title="Nobody matches that."
            body="Try a different skill, or clear the search to see everyone."
          />
        </div>
      ) : (
        <ul className="flex flex-col gap-12">
          {data.items.map((entry) => (
            <li key={entry.participationId}>
              <Card entry={entry} href={`${base}/directory/${entry.participationId}`} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Filters({
  basePath,
  skills,
  q,
  skill,
}: {
  basePath: string;
  skills: string[];
  q: string | undefined;
  skill: string | undefined;
}) {
  const href = (patch: { q?: string; skill?: string }) => {
    const params = new URLSearchParams();
    const merged = { q, skill, ...patch };
    if (merged.q) params.set("q", merged.q);
    if (merged.skill) params.set("skill", merged.skill);
    const query = params.toString();
    return query ? `${basePath}?${query}` : basePath;
  };

  return (
    <div className="flex flex-col gap-12">
      {/* A plain GET form: search works with no JavaScript and the result is
          an address. */}
      <form action={basePath} className="flex flex-wrap items-end gap-12">
        <label className="flex flex-col gap-8">
          <span className="type-label text-primary">Search</span>
          <input
            type="search"
            name="q"
            defaultValue={q ?? ""}
            placeholder="Name or skill"
            className="h-field rounded-sm border border-default bg-surface px-12 type-body-m text-primary placeholder:text-muted focus:border-accent focus:outline-none focus:ring-3 focus:ring-focus-halo"
          />
        </label>
        {skill && <input type="hidden" name="skill" value={skill} />}
        <button
          type="submit"
          className="pointer-coarse:min-h-field inline-flex h-field items-center rounded-md border border-default px-16 type-body-m text-primary outline-focus outline-offset-2 focus-visible:outline-2"
        >
          Search
        </button>
      </form>

      <div className="flex flex-wrap items-center gap-8">
        <span className="type-label text-muted">Skill</span>
        <Link
          href={href({ skill: undefined })}
          aria-current={skill ? undefined : "page"}
          className={chipClass(!skill)}
        >
          Any
        </Link>
        {skills.map((s) => (
          <Link
            key={s}
            href={href({ skill: s })}
            aria-current={skill === s ? "page" : undefined}
            className={chipClass(skill === s)}
          >
            {s}
          </Link>
        ))}
      </div>
    </div>
  );
}

function Card({
  entry,
  href,
}: {
  entry: Schemas["DirectoryEntry"];
  href: string;
}) {
  return (
    <Link
      href={href}
      className="block rounded-md border border-subtle bg-surface p-16 transition-colors duration-instant ease-out outline-focus outline-offset-2 hover:border-default focus-visible:outline-2"
    >
      <span className="flex items-start gap-12">
        <Avatar
          name={entry.name}
          participationId={entry.participationId}
          size={40}
          neutral={!entry.available}
        />

        <span className="flex min-w-0 flex-1 flex-col gap-4">
          <span className="flex flex-wrap items-baseline gap-8">
            <span className="type-heading-s text-primary">{entry.name}</span>
            {entry.timezone && (
              <span className="type-caption text-muted">{entry.timezone}</span>
            )}
          </span>

          {entry.headline && (
            <span className="type-body-s text-secondary">{entry.headline}</span>
          )}

          {entry.skills.length > 0 && (
            <span className="type-body-s text-muted">
              {entry.skills.join(", ")}
            </span>
          )}

          {/* Stated in words. Greying the card alone would make availability a
              colour, and colour never carries meaning by itself. */}
          {!entry.available && (
            <span className="type-caption text-secondary">
              {entry.unavailableReason ?? "Not taking anyone new"}
            </span>
          )}
        </span>
      </span>
    </Link>
  );
}

const chipClass = (active: boolean) =>
  [
    "pointer-coarse:min-h-field inline-flex items-center rounded-sm px-8 py-4 type-body-s",
    "outline-focus outline-offset-2 focus-visible:outline-2",
    active
      ? "bg-accent text-on-accent"
      : "border border-default text-secondary hover:text-primary",
  ].join(" ");
