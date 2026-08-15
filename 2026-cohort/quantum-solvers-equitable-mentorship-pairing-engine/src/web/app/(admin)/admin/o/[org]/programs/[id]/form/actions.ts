"use server";

import { revalidatePath } from "next/cache";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";

export type DraftResult =
  | { ok: true; draft: Schemas["FormVersion"] }
  | { ok: false; message: string };

export async function saveDraft({
  programId,
  role,
  sections,
}: {
  programId: string;
  role: Schemas["Role"];
  sections: Schemas["FormSection"][];
}): Promise<DraftResult> {
  const { data, error } = await serverApi.PUT(
    "/programs/{programId}/forms/{role}/draft",
    { params: { path: { programId, role } }, body: { sections } },
  );

  if (error || !data) {
    return { ok: false, message: error?.message ?? "The draft did not save." };
  }

  revalidatePath("/admin/o/[org]/programs/[id]/form", "page");
  return { ok: true, draft: data };
}

export async function publishDraft({
  programId,
  role,
}: {
  programId: string;
  role: Schemas["Role"];
}): Promise<DraftResult> {
  const { data, error } = await serverApi.POST(
    "/programs/{programId}/forms/{role}/publish",
    { params: { path: { programId, role } } },
  );

  if (error || !data) {
    return { ok: false, message: error?.message ?? "Publishing did not finish." };
  }

  revalidatePath("/admin/o/[org]/programs/[id]/form", "page");
  return { ok: true, draft: data };
}
