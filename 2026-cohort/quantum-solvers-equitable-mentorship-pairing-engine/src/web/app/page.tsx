import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { OrganisationsLanding } from "@/components/marketing/organisations-landing";
import { getSession } from "@/lib/auth/guard";

export const metadata: Metadata = {
  title: "Braid — matching that a coordinator can stand behind",
  description:
    "Braid takes a mentoring round from open applications to published pairs, with a fairness summary, an audit trail, and every decision left in your hands.",
};

/**
 * The root does two jobs, because it has two audiences.
 *
 * Signed out it is the product's front door — the "Braid for organisations"
 * page, which is design-direction 5.2 place five. This is distinct from the
 * *programme* landing page at `/p/:org/:program`: that one recruits
 * participants into one cohort and is the link a coordinator sends out, while
 * this one addresses the coordinator deciding whether to run a cohort at all.
 * Architecture 2 starts its sitemap at the programme landing for that reason,
 * and never says what the root does — this fills the gap rather than
 * overriding it.
 *
 * Signed in it is a signpost, because somebody who is already a member does
 * not need to be sold the product they are using.
 */
export default async function RootPage() {
  const session = await getSession();
  if (!session) return <OrganisationsLanding />;

  const { participations } = session;

  // Somebody in one programme goes straight into it — the intermediate list
  // would be a screen with a single row and one thing to click.
  if (participations.length === 1) {
    const only = participations[0];
    redirect(
      only.isCoordinator
        ? `/admin/o/${only.orgSlug}`
        : `/o/${only.orgSlug}/p/${only.programSlug}`,
    );
  }

  // More than one, or none at all: the programmes list is right in both cases.
  // With none it is an empty state that explains how somebody joins, which is
  // more use than dropping them at a sign-in form they have already passed.
  redirect("/programs");
}
