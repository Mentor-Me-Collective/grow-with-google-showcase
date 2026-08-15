import Link from "next/link";
import type { components } from "@/lib/api/types";
import { serverApi } from "@/lib/api/server";
import { requireParticipation } from "@/lib/auth/guard";
import { buttonClasses } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { StrandCard, StrandCardError } from "@/components/strand/strand-card";

type S = components["schemas"];

const longDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(new Date(iso));

const WORDS = [
  "No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
  "Ten", "Eleven", "Twelve",
];
const inWords = (n: number) => (n < WORDS.length ? WORDS[n] : String(n));

export const metadata = { title: "Home" };

/**
 * Architecture 4.1: answers one question, which is what should I do right now.
 *
 * Two states, and the empty one matters more. Design direction 1: a participant
 * signs up in September and is matched in October, and for three weeks this
 * screen is the whole product. If that period reads as abandonment they leave
 * before the product has had a chance to work.
 */
export default async function HomePage(
  props: PageProps<"/o/[org]/p/[program]">,
) {
  const { org, program } = await props.params;
  const result = await requireParticipation(org, program);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const programId = result.participation.programId;
  const base = `/o/${org}/p/${program}`;

  const [{ data: home, error: homeError }, { data: strands }] = await Promise.all([
    serverApi.GET("/programs/{programId}/home", {
      params: { path: { programId } },
    }),
    serverApi.GET("/programs/{programId}/strands", {
      params: { path: { programId }, query: { state: "active" } },
    }),
  ]);

  if (homeError || !home) {
    return (
      <div className="flex flex-col gap-16">
        <h1 className="type-heading-l text-primary">Home</h1>
        <StrandCardError />
      </div>
    );
  }

  const active = strands ?? [];
  const firstName = result.session.account.name.split(" ")[0];

  if (active.length === 0) {
    return <Waiting home={home} base={base} firstName={firstName} />;
  }

  return (
    <div className="flex flex-col gap-48">
      <h1 className="sr-only">Home</h1>

      {home.announcement && <AnnouncementBanner announcement={home.announcement} />}

      {/* One next-action card, sized larger than anything below it. */}
      {home.nextAction ? (
        <NextActionCard action={home.nextAction} base={base} />
      ) : (
        <p className="rounded-lg border border-subtle bg-surface p-32 type-heading-s text-secondary">
          Nothing needs you right now. {firstName}, that is allowed.
        </p>
      )}

      <section className="flex flex-col gap-16">
        <h2 className="type-label text-muted">Your strands</h2>
        <div className="flex flex-col gap-12">
          {active.map((strand) => (
            <StrandCard
              key={strand.id}
              strand={strand}
              href={`${base}/strands/${strand.id}`}
            />
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-24 border-t border-subtle pt-32 md:flex-row md:gap-48">
        <ProfileCompleteness value={home.profileCompleteness} href={`${base}/me/edit`} />
        {home.upcomingMilestone && <NextMilestone milestone={home.upcomingMilestone} />}
      </section>
    </div>
  );
}

/**
 * Before matching. The screen the anchor message is actually for.
 *
 * The display face is allowed here — 5.2 place two of five, the empty state on
 * home before matching — and this is the only participant screen that gets it.
 *
 * The copy does three things at once, per 8.5: it sets a date, it shows the
 * reader they are already part of something populated, and it gives them one
 * useful action. It never says "nothing here yet".
 */
function Waiting({
  home,
  base,
  firstName,
}: {
  home: S["HomeSummary"];
  base: string;
  firstName: string;
}) {
  const opens = home.matchingOpensAt ? longDate(home.matchingOpensAt) : null;
  const complete = home.profileCompleteness >= 1;

  return (
    <div className="flex flex-col gap-32">
      <h1 className="sr-only">Home</h1>

      {home.announcement && <AnnouncementBanner announcement={home.announcement} />}

      <div className="rounded-lg border border-subtle bg-surface">
        <EmptyState
          markId="home-waiting"
          emphasis="display"
          title={opens ? `Matching opens ${opens}.` : "You are in."}
          body={
            complete
              ? `${inWords(home.mentorCount)} mentors have joined so far. Your profile is ready, so you will be in the first round. Nothing else is needed from you.`
              : `${inWords(home.mentorCount)} mentors have joined so far. Finish your profile before then and you will be included in the first round.`
          }
          action={
            complete ? undefined : (
              <Link href={`${base}/me/edit`} className={buttonClasses({ size: "lg" })}>
                Finish your profile
              </Link>
            )
          }
        />
      </div>

      <div className="flex flex-col gap-24 md:flex-row md:gap-48">
        <ProfileCompleteness value={home.profileCompleteness} href={`${base}/me/edit`} />
        {home.upcomingMilestone && <NextMilestone milestone={home.upcomingMilestone} />}
      </div>

      <p className="type-body-s text-muted">
        {firstName}, there is nothing to do here until matching runs. We will
        write to you the day it does.
      </p>
    </div>
  );
}

/**
 * Larger than anything below it, per section 9. Nothing is done here: every
 * action on home is a link into the page that resolves it.
 */
function NextActionCard({
  action,
  base,
}: {
  action: S["NextAction"];
  base: string;
}) {
  return (
    <section className="flex flex-col gap-16 rounded-lg border border-subtle bg-surface p-32">
      <h2 className="type-heading-l text-primary">{action.title}</h2>
      {action.body && <p className="type-body-l text-secondary">{action.body}</p>}
      <div className="flex">
        <Link href={`${base}${action.href}`} className={buttonClasses({ size: "lg" })}>
          {action.actionLabel}
        </Link>
      </div>
    </section>
  );
}

function AnnouncementBanner({
  announcement,
}: {
  announcement: S["Announcement"];
}) {
  return (
    <aside className="flex flex-col gap-8 rounded-md border border-subtle bg-sunken p-16">
      <p className="type-label text-muted">
        From {announcement.authorName}
      </p>
      <p className="type-body-m text-secondary">{announcement.body}</p>
    </aside>
  );
}

/**
 * A bar and a number. Colour never carries meaning alone, so the percentage is
 * spelled out beside it and the bar is only the shape of the same fact.
 */
function ProfileCompleteness({ value, href }: { value: number; href: string }) {
  const percent = Math.round(value * 100);
  const done = percent >= 100;

  return (
    <div className="flex min-w-0 flex-1 flex-col gap-8">
      <h2 className="type-label text-muted">Your profile</h2>
      <div className="flex items-center gap-12">
        <div
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
          aria-label="Profile completeness"
          className="h-8 min-w-0 flex-1 overflow-hidden rounded-sm bg-sunken"
        >
          <div
            className="h-8 rounded-sm bg-accent"
            style={{ inlineSize: `${percent}%` }}
          />
        </div>
        <span className="type-data-m text-primary">{percent}%</span>
      </div>
      {done ? (
        <p className="type-body-s text-muted">Complete. Nothing missing.</p>
      ) : (
        <Link href={href} className="type-body-s text-link underline">
          Finish the rest
        </Link>
      )}
    </div>
  );
}

function NextMilestone({ milestone }: { milestone: S["Milestone"] }) {
  return (
    <div className="flex min-w-0 flex-1 flex-col gap-8">
      <h2 className="type-label text-muted">Next milestone</h2>
      <p className="type-body-m text-primary">{milestone.title}</p>
      <p className="type-body-s text-muted">
        Due {longDate(milestone.dueAt)}
      </p>
    </div>
  );
}
