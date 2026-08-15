"use server";

import { revalidatePath } from "next/cache";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";

export type DecisionResult = { ok: true; decided: number } | { ok: false; message: string };

/**
 * Decisions run on the server because the queue is server-rendered: a write
 * from the browser would land in the MSW worker's copy of the fixtures while
 * the table reads Node's, and the row would spring back on the next render.
 */
export async function decideApplication({
  applicationId,
  decision,
  note,
}: {
  applicationId: string;
  decision: Schemas["DecisionKind"];
  note?: string;
}): Promise<DecisionResult> {
  const { error } = await serverApi.POST("/applications/{applicationId}/decision", {
    params: { path: { applicationId } },
    body: { decision, note: note ?? null },
  });

  if (error) {
    return { ok: false, message: error.message ?? "That decision did not save." };
  }

  // The route pattern, not a filled-in path: revalidating by pattern covers
  // every org and programme, and a half-substituted path matches no route at
  // all. The roster is invalidated too — approving is what puts someone on it.
  revalidatePath("/admin/o/[org]/programs/[id]/applications", "page");
  revalidatePath("/admin/o/[org]/programs/[id]/roster", "page");
  return { ok: true, decided: 1 };
}

export async function decideApplications({
  programId,
  applicationIds,
  decision,
  note,
}: {
  programId: string;
  applicationIds: string[];
  decision: Schemas["DecisionKind"];
  note?: string;
}): Promise<DecisionResult> {
  const { data, error } = await serverApi.POST(
    "/programs/{programId}/applications/decisions",
    {
      params: { path: { programId } },
      body: { applicationIds, decision, note: note ?? null },
    },
  );

  if (error || !data) {
    return { ok: false, message: error?.message ?? "Those decisions did not save." };
  }

  // The route pattern, not a filled-in path: revalidating by pattern covers
  // every org and programme, and a half-substituted path matches no route at
  // all. The roster is invalidated too — approving is what puts someone on it.
  revalidatePath("/admin/o/[org]/programs/[id]/applications", "page");
  revalidatePath("/admin/o/[org]/programs/[id]/roster", "page");

  // Partial success is reported, not swallowed: a coordinator who selected
  // twelve and moved nine needs to know which three did not move.
  if (data.skipped.length > 0) {
    return {
      ok: false,
      message:
        data.decided > 0
          ? `${data.decided} moved. ${data.skipped.length} did not: ${data.skipped[0].reason}`
          : `Nothing moved. ${data.skipped[0].reason}`,
    };
  }

  return { ok: true, decided: data.decided };
}
