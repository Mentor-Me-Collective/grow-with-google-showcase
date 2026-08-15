import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import type { Schemas } from "@/lib/api/client";
import { ApplicationsTable } from "./applications-table";

export const metadata = { title: "Applications" };

const STATUSES = new Set([
  "submitted",
  "under_review",
  "approved",
  "waitlisted",
  "rejected",
]);

export default async function ApplicationsPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/applications">,
) {
  const { org, id } = await props.params;
  const { status } = await props.searchParams;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  // Unread first: the queue opens on the work, not on the archive.
  const current =
    typeof status === "string" && STATUSES.has(status) ? status : "submitted";

  const { data, error } = await serverApi.GET(
    "/programs/{programId}/applications",
    {
      params: {
        path: { programId: id },
        query: {
          status: current as Schemas["ApplicationStatus"],
          pageSize: 100,
        },
      },
    },
  );

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-wrap items-baseline justify-between gap-16">
        <h1 className="type-heading-l text-primary">Applications</h1>
        {data && (
          <p className="type-body-s text-muted">
            {data.counts.submitted} waiting to be read
          </p>
        )}
      </div>

      {error || !data ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The queue did not load. No application has been lost; this is a
          connection problem. Reload to try again.
        </div>
      ) : (
        <ApplicationsTable
          applications={data.items}
          counts={data.counts}
          programId={id}
          basePath={`/admin/o/${org}/programs/${id}/applications`}
          status={current}
        />
      )}
    </div>
  );
}
