"use server";

import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";

export type SubmitResult =
  | { ok: true; application: Schemas["Application"] }
  | { ok: false; message: string };

/**
 * Submitting runs on the server so the write and the confirmation that reads it
 * back happen against the same store. The wizard holds every answer in the
 * browser and hands the finished body over; nothing about the form moves here.
 *
 * In development this is also the only thing that makes the confirmation work:
 * MSW mocks in two places, and a POST from the browser lands in the worker's
 * copy of the fixtures while the server-rendered /applied route reads Node's.
 */
export async function submitApplication({
  orgSlug,
  programSlug,
  body,
}: {
  orgSlug: string;
  programSlug: string;
  body: Schemas["ApplicationCreate"];
}): Promise<SubmitResult> {
  const { data, error } = await serverApi.POST(
    "/orgs/{orgSlug}/programs/{programSlug}/applications",
    { params: { path: { orgSlug, programSlug } }, body },
  );

  if (error || !data) {
    return {
      ok: false,
      message: error?.message ?? "That did not send. Your answers are still here.",
    };
  }

  return { ok: true, application: data };
}
