import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { CriteriaEditor } from "./criteria-editor";

export const metadata = { title: "Matching criteria" };

export default async function CriteriaPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/criteria">,
) {
  const { org, id } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const { data, error } = await serverApi.GET("/programs/{programId}/criteria", {
    params: { path: { programId: id } },
  });

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Matching criteria</h1>
        <p className="type-body-m text-secondary">
          How pairs are scored. Built from the questions on the published form,
          so a weight can only exist for something you actually ask.
        </p>
      </div>

      {error || !data ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The recipe did not load. Nothing has been changed and no run is
          affected. Reload to try again.
        </div>
      ) : (
        <CriteriaEditor
          state={data}
          programId={id}
          formHref={`/admin/o/${org}/programs/${id}/form`}
        />
      )}
    </div>
  );
}
