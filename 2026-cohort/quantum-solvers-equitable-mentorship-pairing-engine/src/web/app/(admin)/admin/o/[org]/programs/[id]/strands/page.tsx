import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { StrandMonitor } from "./strand-monitor";

export const metadata = { title: "Strands" };

const HEALTHS = new Set(["on_track", "slow", "quiet", "not_started", "ended"]);

export default async function StrandsMonitorPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/strands">,
) {
  const { org, id } = await props.params;
  const { health } = await props.searchParams;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const current =
    typeof health === "string" && HEALTHS.has(health)
      ? (health as Schemas["StrandHealth"])
      : "all";

  const { data, error } = await serverApi.GET(
    "/programs/{programId}/strand-monitor",
    {
      params: {
        path: { programId: id },
        query: {
          ...(current === "all" ? {} : { health: current }),
          pageSize: 100,
        },
      },
    },
  );

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Strands</h1>
        <p className="type-body-m text-secondary">
          Every pairing in the programme and how it is going. Health is worked
          out from what has actually happened, not from anything anyone flagged.
        </p>
      </div>

      {error || !data ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The monitor did not load. No strand has been changed; this is a
          connection problem. Reload to try again.
        </div>
      ) : (
        <StrandMonitor
          entries={data.items}
          healthCounts={data.healthCounts}
          basePath={`/admin/o/${org}/programs/${id}/strands`}
          current={current}
        />
      )}
    </div>
  );
}
