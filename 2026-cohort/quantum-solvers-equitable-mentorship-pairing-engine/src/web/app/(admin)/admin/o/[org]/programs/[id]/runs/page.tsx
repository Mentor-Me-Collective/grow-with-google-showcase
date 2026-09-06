import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { RunsTable } from "./runs-table";

export const metadata = { title: "Matching runs" };

export default async function RunsPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/runs">,
) {
  const { org, id } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const { data } = await serverApi.GET("/programs/{programId}/runs", {
    params: { path: { programId: id } },
  });

  return <RunsTable runs={data?.items ?? []} programId={id} orgSlug={org} />;
}
