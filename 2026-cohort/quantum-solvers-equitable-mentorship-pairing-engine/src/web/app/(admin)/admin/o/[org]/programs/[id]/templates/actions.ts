"use server";

import { revalidatePath } from "next/cache";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";

export type TemplateResult =
  | { ok: true; template: Schemas["MessageTemplate"] }
  | { ok: false; message: string };

export async function saveTemplate({
  programId,
  kind,
  subject,
  body,
}: {
  programId: string;
  kind: Schemas["TemplateKind"];
  subject: string;
  body: string;
}): Promise<TemplateResult> {
  const { data, error } = await serverApi.PUT(
    "/programs/{programId}/templates/{kind}",
    { params: { path: { programId, kind } }, body: { subject, body } },
  );

  if (error || !data) {
    return { ok: false, message: error?.message ?? "That template did not save." };
  }

  revalidatePath("/admin/o/[org]/programs/[id]/templates", "page");
  return { ok: true, template: data };
}

export async function resetTemplate({
  programId,
  kind,
}: {
  programId: string;
  kind: Schemas["TemplateKind"];
}): Promise<TemplateResult> {
  const { data, error } = await serverApi.DELETE(
    "/programs/{programId}/templates/{kind}",
    { params: { path: { programId, kind } } },
  );

  if (error || !data) {
    return { ok: false, message: error?.message ?? "That reset did not go through." };
  }

  revalidatePath("/admin/o/[org]/programs/[id]/templates", "page");
  return { ok: true, template: data };
}
