import { notFound } from "next/navigation";
import { db } from "@/lib/api/msw/fixtures";

export const dynamic = "force-dynamic";

/**
 * Dev-only. Dumps the MSW fixture database so the backend's seed is generated
 * from it rather than transcribed by hand.
 *
 * Fidelity is the point: the frontend was built and verified against this exact
 * data, so seeding Postgres with the same rows makes every screen comparable
 * side by side. A hand-ported approximation would turn each difference into a
 * question of whether the port or the API was wrong.
 *
 * Not named with a leading underscore: the App Router treats those as private
 * folders and excludes them from routing entirely.
 */
export function GET() {
  if (process.env.NODE_ENV === "production") notFound();

  return Response.json({
    program: db.program,
    roster: db.roster,
    formVersions: db.formVersions,
    applications: db.applications,
    strands: db.strands,
    strandSummaries: db.strandSummaries,
    messages: db.messages,
    strandMetrics: db.strandMetrics,
    runs: db.runs,
    unmatched: db.unmatched,
    milestones: db.milestones,
    templates: db.templates,
    mergeCodes: db.mergeCodes,
    recipe: db.recipe,
    broadcasts: db.broadcasts,
    auditEvents: db.auditEvents,
    report: db.report,
    resources: db.resources,
    invites: db.invites,
    notifications: db.notifications,
    myAnswers: db.myAnswers,
    session: db.session,
    home: db.home,
    selfMatchingEnabled: db.selfMatchingEnabled,
  });
}
