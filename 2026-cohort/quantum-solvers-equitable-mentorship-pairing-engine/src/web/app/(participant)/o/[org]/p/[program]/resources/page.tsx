import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireParticipation } from "@/lib/auth/guard";
import { EmptyState } from "@/components/ui/empty-state";

export const metadata = { title: "Resources" };

const KIND_WORD: Record<Schemas["ResourceKind"], string> = {
  handbook: "Handbook",
  expectations: "What is expected",
  conversation_starters: "Conversation starters",
  code_of_conduct: "Code of conduct",
  other: "Reading",
};

const longDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(iso));

/** Architecture 4.15: static content the coordinator publishes. */
export default async function ResourcesPage(
  props: PageProps<"/o/[org]/p/[program]/resources">,
) {
  const { org, program } = await props.params;
  const result = await requireParticipation(org, program);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const { data: resources, error } = await serverApi.GET(
    "/programs/{programId}/resources",
    { params: { path: { programId: result.participation.programId } } },
  );

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Resources</h1>
        <p className="type-body-m text-secondary">
          What the programme has written down, so you are not guessing at what
          is expected.
        </p>
      </div>

      {error || !resources ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          These did not load. Reload to try again.
        </div>
      ) : resources.length === 0 ? (
        <div className="rounded-lg border border-subtle bg-surface">
          <EmptyState
            markId="resources-empty"
            title="Nothing published yet."
            body="Your coordinator puts the handbook, the code of conduct and anything else worth reading here. Until then, your strand is the place to ask."
          />
        </div>
      ) : (
        <ul className="flex flex-col gap-12">
          {resources.map((resource) => (
            <li key={resource.id}>
              <a
                href={resource.url}
                // Downloads rather than navigating: these are documents, and a
                // PDF opening over the app loses the person's place in it.
                download
                className="flex flex-col gap-8 rounded-md border border-subtle bg-surface p-16 transition-colors duration-instant ease-out outline-focus outline-offset-2 hover:border-default focus-visible:outline-2"
              >
                <span className="flex flex-wrap items-baseline justify-between gap-8">
                  <span className="type-heading-s text-primary">
                    {resource.title}
                  </span>
                  <span className="type-caption text-muted">
                    {KIND_WORD[resource.kind]}
                  </span>
                </span>

                {resource.description && (
                  <span className="type-body-m text-secondary">
                    {resource.description}
                  </span>
                )}

                <span className="type-caption text-muted">
                  {[
                    resource.sizeBytes ? readableSize(resource.sizeBytes) : null,
                    resource.updatedAt
                      ? `Updated ${longDate(resource.updatedAt)}`
                      : null,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Size is stated because most of these are opened on a phone on mobile data. */
function readableSize(bytes: number) {
  if (bytes < 1000) return `${bytes} bytes`;
  if (bytes < 1_000_000) return `${Math.round(bytes / 1000)} KB`;
  return `${(bytes / 1_000_000).toFixed(1)} MB`;
}
