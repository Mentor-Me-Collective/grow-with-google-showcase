import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { UnmatchedQueue } from "./unmatched-queue";

export const metadata = { title: "Unmatched" };

export default async function UnmatchedPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/unmatched">,
) {
  const { org, id } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const { data, error } = await serverApi.GET("/programs/{programId}/unmatched", {
    params: { path: { programId: id }, query: { pageSize: 100 } },
  });

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Unmatched</h1>
        <p className="type-body-m text-secondary">
          Everyone in this programme without a strand, and what would fix it.
        </p>
      </div>

      {error || !data ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The queue did not load. Nobody has been matched or unmatched by this;
          it is a connection problem. Reload to try again.
        </div>
      ) : (
        <UnmatchedQueue
          entries={data.items}
          availableMentors={data.availableMentors}
          programId={id}
        />
      )}
    </div>
  );
}
