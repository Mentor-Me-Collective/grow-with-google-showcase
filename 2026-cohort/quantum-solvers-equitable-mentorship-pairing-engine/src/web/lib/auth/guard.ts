import { redirect } from "next/navigation";
import { cache } from "react";
import { serverApi } from "@/lib/api/server";
import type { Schemas } from "@/lib/api/client";

export type Session = Schemas["Session"];
export type Participation = Schemas["ParticipationSummary"];

/** Cached per request, so a layout and its pages resolve one session between them. */
export const getSession = cache(async (): Promise<Session | null> => {
  const { data } = await serverApi.GET("/auth/session");
  return data ?? null;
});

export async function requireSession(): Promise<Session> {
  const session = await getSession();
  if (!session) redirect("/signin");
  return session;
}

export type ParticipationResult =
  | { ok: true; session: Session; participation: Participation }
  | { ok: false; session: Session };

/**
 * Resolves the account, the programme, and the role held in it. Layouts render
 * <Forbidden> on a false result; everything below them may assume a true one.
 */
export async function requireParticipation(
  orgSlug: string,
  programSlug: string,
): Promise<ParticipationResult> {
  const session = await requireSession();
  const participation = session.participations.find(
    (p) => p.orgSlug === orgSlug && p.programSlug === programSlug,
  );
  return participation
    ? { ok: true, session, participation }
    : { ok: false, session };
}

export type CoordinatorResult =
  | { ok: true; session: Session; programmes: Participation[] }
  | { ok: false; session: Session };

export async function requireCoordinator(
  orgSlug: string,
): Promise<CoordinatorResult> {
  const session = await requireSession();
  const programmes = session.participations.filter(
    (p) => p.orgSlug === orgSlug && p.isCoordinator,
  );
  return programmes.length > 0
    ? { ok: true, session, programmes }
    : { ok: false, session };
}
