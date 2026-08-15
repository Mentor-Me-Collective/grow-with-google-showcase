import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { Button } from "@/components/ui/button";
import { RosterTable } from "./roster-table";

export const metadata = { title: "Roster" };

export default async function RosterPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/roster">,
) {
  const { org, id } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const { data, error } = await serverApi.GET("/programs/{programId}/roster", {
    // One cohort is a few dozen people, so the table takes the whole roster
    // and filters in the browser. Paging arrives with a programme big enough
    // to need it.
    params: { path: { programId: id }, query: { pageSize: 200 } },
  });

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-wrap items-baseline justify-between gap-16">
        <h1 className="type-heading-l text-primary">Roster</h1>
        {data && (
          <p className="type-body-s text-muted">
            {data.total} {data.total === 1 ? "person" : "people"} approved
          </p>
        )}
      </div>

      {error || !data ? (
        <div
          role="alert"
          className="flex flex-col items-start gap-12 rounded-md border border-danger bg-surface p-24"
        >
          <p className="type-body-m text-secondary">
            The roster did not load. Nobody has been removed; this is a
            connection problem.
          </p>
          <form>
            <Button type="submit" variant="secondary">
              Try again
            </Button>
          </form>
        </div>
      ) : (
        <RosterTable entries={data.items} />
      )}
    </div>
  );
}
