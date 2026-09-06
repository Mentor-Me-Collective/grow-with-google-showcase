"use server";

import { revalidatePath } from "next/cache";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";

export type SendResult =
  | { ok: true; broadcast: Schemas["Broadcast"] }
  | { ok: false; message: string };

export async function sendBroadcast({
  programId,
  segment,
  subject,
  body,
  scheduledFor,
}: {
  programId: string;
  segment: Schemas["BroadcastSegment"];
  subject: string;
  body: string;
  scheduledFor?: string | null;
}): Promise<SendResult> {
  const { data, error } = await serverApi.POST(
    "/programs/{programId}/broadcasts",
    {
      params: { path: { programId } },
      body: { segment, subject, body, scheduledFor: scheduledFor ?? null },
    },
  );

  if (error || !data) {
    return { ok: false, message: error?.message ?? "That did not send." };
  }

  revalidatePath("/admin/o/[org]/programs/[id]/comms", "page");
  return { ok: true, broadcast: data };
}
