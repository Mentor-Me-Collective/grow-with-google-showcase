"use server";

import { revalidatePath } from "next/cache";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";

export type SaveResult =
  | { ok: true; recipe: Schemas["MatchingRecipe"] }
  | { ok: false; message: string };

export type TestResult =
  | { ok: true; summary: Schemas["FairnessSummary"] }
  | { ok: false; message: string };

export async function saveRecipe({
  programId,
  recipe,
}: {
  programId: string;
  recipe: Schemas["MatchingRecipeSave"];
}): Promise<SaveResult> {
  const { data, error } = await serverApi.PUT("/programs/{programId}/criteria", {
    params: { path: { programId } },
    body: recipe,
  });

  if (error || !data) {
    return { ok: false, message: error?.message ?? "The recipe did not save." };
  }

  revalidatePath("/admin/o/[org]/programs/[id]/criteria", "page");
  return { ok: true, recipe: data };
}

/** Returns the fairness summary only. There are no pairs to return. */
export async function testRecipe({
  programId,
  recipe,
}: {
  programId: string;
  recipe: Schemas["MatchingRecipeSave"];
}): Promise<TestResult> {
  const { data, error } = await serverApi.POST(
    "/programs/{programId}/criteria/test-run",
    { params: { path: { programId } }, body: recipe },
  );

  if (error || !data) {
    return { ok: false, message: error?.message ?? "The test did not run." };
  }

  return { ok: true, summary: data };
}
