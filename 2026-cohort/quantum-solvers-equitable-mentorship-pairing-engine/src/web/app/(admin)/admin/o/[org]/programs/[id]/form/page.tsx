import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { FormBuilder } from "./form-builder";

export const metadata = { title: "Form builder" };

export default async function FormBuilderPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/form">,
) {
  const { org, id } = await props.params;
  const { role } = await props.searchParams;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const current: Schemas["Role"] = role === "mentor" ? "mentor" : "mentee";

  const { data, error } = await serverApi.GET("/programs/{programId}/forms", {
    params: { path: { programId: id }, query: { role: current } },
  });

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Form</h1>
        <p className="type-body-m text-secondary">
          What applicants are asked. Editing never changes the live form —
          changes go to a draft until you publish them.
        </p>
      </div>

      {error || !data ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The form did not load. Nothing has been changed and applicants are
          unaffected. Reload to try again.
        </div>
      ) : (
        <FormBuilder
          // Remounts when the role changes, so the working copy is never the
          // other role's questions held over in state.
          key={current}
          state={data}
          programId={id}
          role={current}
          basePath={`/admin/o/${org}/programs/${id}/form`}
        />
      )}
    </div>
  );
}
