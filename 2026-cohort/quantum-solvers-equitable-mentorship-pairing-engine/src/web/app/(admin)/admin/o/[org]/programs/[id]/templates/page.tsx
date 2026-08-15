import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { TemplatesEditor } from "./templates-editor";

export const metadata = { title: "Templates" };

export default async function TemplatesPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/templates">,
) {
  const { org, id } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const { data, error } = await serverApi.GET("/programs/{programId}/templates", {
    params: { path: { programId: id } },
  });

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Templates</h1>
        <p className="type-body-m text-secondary">
          Every message the programme sends on your behalf. They arrive written,
          so a programme that never opens this page still sounds like a person.
        </p>
      </div>

      {error || !data ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The templates did not load. Nothing has been changed and no message
          has been sent. Reload to try again.
        </div>
      ) : (
        <TemplatesEditor
          templates={data.items}
          mergeCodes={data.mergeCodes}
          programId={id}
        />
      )}
    </div>
  );
}
