"use server";

import { revalidatePath } from "next/cache";
import { serverApi } from "@/lib/api/server";

export type MatchResult = { ok: true } | { ok: false; message: string };

/**
 * Server-side for the same reason the application decisions are: the queue is
 * server-rendered, and a pairing written from the browser would be invisible to
 * the render that has to drop the row.
 */
export async function pairManually({
  programId,
  menteeParticipationId,
  mentorParticipationId,
}: {
  programId: string;
  menteeParticipationId: string;
  mentorParticipationId: string;
}): Promise<MatchResult> {
  const { error } = await serverApi.POST("/programs/{programId}/strands", {
    params: { path: { programId } },
    body: { menteeParticipationId, mentorParticipationId },
  });

  if (error) {
    return {
      ok: false,
      message: error.message ?? "That pairing did not save.",
    };
  }

  // By route pattern, not a filled-in path. The roster changes too: the mentee
  // is now matched and the mentor's load went up by one.
  revalidatePath("/admin/o/[org]/programs/[id]/unmatched", "page");
  revalidatePath("/admin/o/[org]/programs/[id]/roster", "page");
  return { ok: true };
}
