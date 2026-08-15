"use server";

import { revalidatePath } from "next/cache";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";

export type SaveResult =
  | { ok: true; milestones: Schemas["ProgramMilestone"][] }
  | { ok: false; message: string };

export async function saveMilestones({
  programId,
  items,
}: {
  programId: string;
  items: Schemas["ProgramMilestoneInput"][];
}): Promise<SaveResult> {
  const { data, error } = await serverApi.PUT("/programs/{programId}/milestones", {
    params: { path: { programId } },
    body: { items },
  });

  if (error || !data) {
    return { ok: false, message: error?.message ?? "The arc did not save." };
  }

  revalidatePath("/admin/o/[org]/programs/[id]/milestones", "page");
  return { ok: true, milestones: data };
}
