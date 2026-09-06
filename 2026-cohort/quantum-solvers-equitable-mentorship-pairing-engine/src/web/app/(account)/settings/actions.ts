"use server";

import { revalidatePath } from "next/cache";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";

export type ActionResult = { ok: true; message?: string } | { ok: false; message: string };

const refresh = () => {
  revalidatePath("/settings", "page");
  revalidatePath("/programs", "page");
};

export async function saveSettings({
  name,
  notifications,
}: {
  name?: string;
  notifications?: Schemas["NotificationPreferences"];
}): Promise<ActionResult> {
  const { error } = await serverApi.PUT("/account/settings", {
    body: {
      ...(name !== undefined ? { name } : {}),
      ...(notifications ? { notifications } : {}),
    },
  });

  if (error) {
    return { ok: false, message: error.message ?? "That did not save." };
  }

  refresh();
  return { ok: true, message: "Saved." };
}

export async function setMuted({
  participationId,
  muted,
}: {
  participationId: string;
  muted: boolean;
}): Promise<ActionResult> {
  const { error } = await serverApi.PUT("/participations/{participationId}/mute", {
    params: { path: { participationId } },
    body: { muted },
  });

  if (error) {
    return { ok: false, message: error.message ?? "That did not save." };
  }

  refresh();
  return {
    ok: true,
    message: muted
      ? "Muted. Your strands carry on as normal."
      : "Email from this programme is back on.",
  };
}

export async function leaveProgram(
  participationId: string,
): Promise<ActionResult> {
  const { error } = await serverApi.POST(
    "/participations/{participationId}/leave",
    { params: { path: { participationId } } },
  );

  if (error) {
    return { ok: false, message: error.message ?? "That did not go through." };
  }

  refresh();
  return { ok: true, message: "You have left the programme." };
}
