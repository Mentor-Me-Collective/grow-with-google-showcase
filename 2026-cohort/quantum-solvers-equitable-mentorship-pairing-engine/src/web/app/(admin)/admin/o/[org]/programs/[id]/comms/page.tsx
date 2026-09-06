import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { BroadcastComposer } from "./broadcast-composer";

export const metadata = { title: "Broadcast" };

export default async function CommsPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/comms">,
) {
  const { org, id } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const [{ data: listing, error }, { data: templateSet }] = await Promise.all([
    serverApi.GET("/programs/{programId}/broadcasts", {
      params: { path: { programId: id } },
    }),
    // The template picker starts from wording already reviewed, rather than
    // from a blank box every time.
    serverApi.GET("/programs/{programId}/templates", {
      params: { path: { programId: id } },
    }),
  ]);

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Broadcast</h1>
        <p className="type-body-m text-secondary">
          One message to a group at once. Everything sent is kept, so you can
          see what this cohort has already been told.
        </p>
      </div>

      {error || !listing ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          This did not load, and nothing has been sent. Reload to try again.
        </div>
      ) : (
        <BroadcastComposer
          listing={listing}
          templates={templateSet?.items ?? []}
          programId={id}
        />
      )}
    </div>
  );
}
