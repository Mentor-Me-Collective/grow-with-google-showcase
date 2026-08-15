"use server";

import { revalidatePath } from "next/cache";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";

export type SaveResult = { ok: true } | { ok: false; message: string };

/**
 * Server-side because the profile it feeds is server-rendered. A save from the
 * browser would land in the MSW worker's copy of the fixtures, report success,
 * and be invisible on the profile screen a second later.
 */
export async function saveProfileSection({
  programId,
  answers,
}: {
  programId: string;
  answers: Record<string, Schemas["AnswerInput"]>;
}): Promise<SaveResult> {
  const { error } = await serverApi.PUT("/programs/{programId}/me", {
    params: { path: { programId } },
    body: { answers },
  });

  if (error) {
    return {
      ok: false,
      message: error.message ?? "That did not save. Your answers are still here.",
    };
  }

  revalidatePath("/o/[org]/p/[program]/me", "page");
  revalidatePath("/o/[org]/p/[program]/me/edit", "page");
  // Home shows profile completeness, which this changes.
  revalidatePath("/o/[org]/p/[program]", "page");
  return { ok: true };
}
