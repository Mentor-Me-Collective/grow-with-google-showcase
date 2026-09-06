import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { AuditTable } from "./audit-table";

export const metadata = { title: "Audit log" };

const one = (value: string | string[] | undefined) =>
  typeof value === "string" ? value : undefined;

export default async function AuditPage(props: PageProps<"/admin/o/[org]/audit">) {
  const { org } = await props.params;
  const search = await props.searchParams;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const filters = {
    actor: one(search.actor),
    action: one(search.action),
    from: one(search.from),
    to: one(search.to),
  };

  const { data, error } = await serverApi.GET("/orgs/{orgSlug}/audit", {
    params: {
      path: { orgSlug: org },
      query: {
        ...(filters.actor ? { actor: filters.actor } : {}),
        ...(filters.action
          ? { action: filters.action as Schemas["AuditAction"] }
          : {}),
        ...(filters.from ? { from: filters.from } : {}),
        ...(filters.to ? { to: filters.to } : {}),
        pageSize: 100,
      },
    },
  });

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Audit log</h1>
        <p className="type-body-m text-secondary">
          Who changed what, and when. A matching run is only defensible if the
          places somebody overruled it are written down, so this is where they
          are.
        </p>
      </div>

      {error || !data ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The log did not load. Nothing has been changed or hidden; this is a
          connection problem. Reload to try again.
        </div>
      ) : (
        <AuditTable
          page={data}
          basePath={`/admin/o/${org}/audit`}
          filters={filters}
        />
      )}
    </div>
  );
}
