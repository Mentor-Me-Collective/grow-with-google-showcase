"use server";

import { revalidatePath } from "next/cache";
import { serverApi } from "@/lib/api/server";

export type StrandActionResult =
  | { ok: true; message: string }
  | { ok: false; message: string };

const refresh = () => {
  revalidatePath("/admin/o/[org]/programs/[id]/strands", "page");
  // The dashboard counts quiet strands, so it is stale the moment one changes.
  revalidatePath("/admin/o/[org]", "page");
};

export async function nudgeStrand(
  strandId: string,
): Promise<StrandActionResult> {
  const { data, error } = await serverApi.POST("/strands/{strandId}/nudge", {
    params: { path: { strandId } },
  });

  if (error || !data) {
    return { ok: false, message: error?.message ?? "The nudge did not send." };
  }

  refresh();
  return {
    ok: true,
    message: `Nudge sent to ${data.sentTo} ${data.sentTo === 1 ? "person" : "people"}.`,
  };
}

export async function setStrandState({
  strandId,
  state,
  reason,
}: {
  strandId: string;
  state: "active" | "paused" | "ended";
  reason?: string;
}): Promise<StrandActionResult> {
  const { error } = await serverApi.PUT("/strands/{strandId}/state", {
    params: { path: { strandId } },
    body: { state, reason: reason ?? null },
  });

  if (error) {
    return { ok: false, message: error.message ?? "That did not save." };
  }

  refresh();
  return {
    ok: true,
    message:
      state === "ended"
        ? "Strand ended. The conversation stays readable to both sides."
        : state === "paused"
          ? "Strand paused."
          : "Strand resumed.",
  };
}
