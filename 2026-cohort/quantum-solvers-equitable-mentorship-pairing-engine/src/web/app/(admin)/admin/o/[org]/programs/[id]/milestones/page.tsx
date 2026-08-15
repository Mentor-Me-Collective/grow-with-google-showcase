import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { MilestonesEditor } from "./milestones-editor";

export const metadata = { title: "Milestones" };

export default async function MilestonesPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/milestones">,
) {
  const { org, id } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const participation = result.programmes.find((p) => p.programId === id);

  const [{ data: milestones, error }, { data: program }] = await Promise.all([
    serverApi.GET("/programs/{programId}/milestones", {
      params: { path: { programId: id } },
    }),
    // Only for the cohort start date, so each week offset can be shown as a
    // real date. The arc itself is stored in weeks and survives a re-run.
    participation
      ? serverApi.GET("/orgs/{orgSlug}/programs/{programSlug}", {
          params: {
            path: {
              orgSlug: participation.orgSlug,
              programSlug: participation.programSlug,
            },
          },
        })
      : Promise.resolve({ data: undefined }),
  ]);

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Milestones</h1>
        <p className="type-body-m text-secondary">
          The shape of the programme, in weeks from the day it starts. Each
          milestone can carry a prompt that appears inside every strand when it
          arrives.
        </p>
      </div>

      {error || !milestones ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The arc did not load. Nothing has been changed; this is a connection
          problem. Reload to try again.
        </div>
      ) : (
        <MilestonesEditor
          milestones={milestones}
          programId={id}
          cohortStart={program?.cohortStart ?? null}
        />
      )}
    </div>
  );
}
