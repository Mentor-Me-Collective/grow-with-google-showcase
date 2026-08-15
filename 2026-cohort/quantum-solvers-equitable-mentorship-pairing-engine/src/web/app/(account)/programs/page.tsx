import Link from "next/link";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireSession } from "@/lib/auth/guard";
import { EmptyState } from "@/components/ui/empty-state";

export const metadata = { title: "My programmes" };

/**
 * Architecture 4.17: the switcher as a whole page, not only a header dropdown.
 * This is also where somebody lands after signing in with more than one
 * programme, so it has to answer "which one" without them opening each.
 */
export default async function ProgramsPage() {
  await requireSession();

  const { data: programs, error } = await serverApi.GET("/account/programs");

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">My programmes</h1>
        <p className="type-body-m text-secondary">
          Every programme you belong to. Your role is set per programme, so it
          can differ between them.
        </p>
      </div>

      {error || !programs ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          These did not load. Reload to try again.
        </div>
      ) : programs.length === 0 ? (
        <div className="rounded-lg border border-subtle bg-surface">
          <EmptyState
            markId="programs-empty"
            title="You are not in a programme yet."
            body="When an organisation accepts your application or invites you, it appears here. An invitation arrives by email and takes one click."
          />
        </div>
      ) : (
        <ul className="flex flex-col gap-12">
          {programs.map((programme) => (
            <li key={programme.participationId}>
              <ProgramCard programme={programme} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ProgramCard({ programme }: { programme: Schemas["AccountProgram"] }) {
  const href = programme.isCoordinator
    ? `/admin/o/${programme.orgSlug}`
    : `/o/${programme.orgSlug}/p/${programme.programSlug}`;

  return (
    <Link
      href={href}
      className="block rounded-md border border-subtle bg-surface p-16 transition-colors duration-instant ease-out outline-focus outline-offset-2 hover:border-default focus-visible:outline-2"
    >
      <span className="flex flex-col gap-8">
        <span className="flex flex-wrap items-baseline justify-between gap-8">
          <span className="type-heading-s text-primary">
            {programme.programName}
          </span>
          {/* A count, not a dot: colour never carries meaning on its own. */}
          {programme.unreadCount > 0 && (
            <span className="type-body-s text-primary">
              {programme.unreadCount} unread
            </span>
          )}
        </span>

        <span className="type-body-s text-secondary">
          {programme.organisationName}
        </span>

        <span className="type-body-s text-muted">
          {[
            programme.isCoordinator
              ? "You coordinate this"
              : `You are a ${programme.role} here`,
            readableStatus(programme.status),
            programme.readOnly ? "Finished — open to read" : null,
            programme.muted ? "Email muted" : null,
          ]
            .filter(Boolean)
            .join(" · ")}
        </span>
      </span>
    </Link>
  );
}

function readableStatus(status: Schemas["ParticipationStatus"]) {
  switch (status) {
    case "approved":
      return "Active";
    case "invited":
      return "Invited, not yet accepted";
    case "applied":
      return "Application being read";
    case "waitlisted":
      return "On the waitlist";
    case "removed":
      return "No longer a member";
  }
}
