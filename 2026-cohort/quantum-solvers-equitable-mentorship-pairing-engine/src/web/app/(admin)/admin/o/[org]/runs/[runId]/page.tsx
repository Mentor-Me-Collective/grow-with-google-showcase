import { requireCoordinator } from "@/lib/auth/guard";
import { RunReview } from "./run-review";

export const metadata = { title: "Run review" };

/**
 * Org-scoped rather than under the programme, per architecture 5.12: a run id
 * is unique on its own and the review is reached from a run, not from a
 * programme's navigation.
 *
 * The run itself is read in the browser rather than here. A run is followed
 * from queued to drafted by polling and then published, all of which are client
 * concerns; fetching the first copy on the server would put the run's opening
 * state and every state after it on opposite sides of the mock boundary, and a
 * run started a second ago would render as missing.
 */
export default async function RunReviewPage(
  props: PageProps<"/admin/o/[org]/runs/[runId]">,
) {
  const { org, runId } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  return <RunReview runId={runId} orgSlug={org} />;
}
