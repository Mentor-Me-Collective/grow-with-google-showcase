import Link from "next/link";
import { notFound } from "next/navigation";
import type { components } from "@/lib/api/types";
import { serverApi } from "@/lib/api/server";
import { buttonClasses } from "@/components/ui/button";
import {
  PublicFooter,
  PublicHeader,
  PublicMain,
} from "@/components/shell/public-shell";
import { WaitlistForm } from "./waitlist-form";

type Program = components["schemas"]["ProgramPublic"];

const DAY = 86_400_000;

const longDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(new Date(iso));

const daysUntil = (iso: string | null | undefined, now: Date) =>
  iso ? Math.max(0, Math.ceil((new Date(iso).getTime() - now.getTime()) / DAY)) : null;

/** Twelve, not 12. A count read as a sentence is not a statistic. */
const WORDS = [
  "No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
  "Ten", "Eleven", "Twelve",
];
const inWords = (n: number) => (n < WORDS.length ? WORDS[n] : String(n));

export async function generateMetadata(
  props: PageProps<"/p/[orgSlug]/[programSlug]">,
) {
  const { orgSlug, programSlug } = await props.params;
  const { data } = await serverApi.GET(
    "/orgs/{orgSlug}/programs/{programSlug}",
    { params: { path: { orgSlug, programSlug } } },
  );
  if (!data) return { title: "Programme" };
  return {
    title: `${data.name} — ${data.organisation.name}`,
    description: data.description,
  };
}

export default async function ProgramLandingPage(
  props: PageProps<"/p/[orgSlug]/[programSlug]">,
) {
  const { orgSlug, programSlug } = await props.params;
  const { data: program } = await serverApi.GET(
    "/orgs/{orgSlug}/programs/{programSlug}",
    { params: { path: { orgSlug, programSlug } } },
  );

  // A closed or full programme still resolves, per architecture 3.1. Only a
  // programme that does not exist is a 404.
  if (!program) notFound();

  const now = new Date();
  const open = program.state === "open";

  return (
    <>
      <PublicHeader
        right={
          <Link
            href="/signin"
            className="inline-flex h-control-md items-center rounded-md px-16 type-body-m text-primary transition-colors duration-instant ease-out outline-focus outline-offset-2 hover:bg-sunken focus-visible:outline-2"
          >
            Sign in
          </Link>
        }
      />

      <PublicMain className="flex flex-col gap-48">
        <p className="type-label text-muted">
          {program.organisation.name} · {program.name}
        </p>

        <Stats program={program} now={now} />

        <hr className="border-t border-subtle" />

        <Hero program={program} orgSlug={orgSlug} programSlug={programSlug} />

        <div className="flex flex-col gap-16 border-t border-subtle pt-32">
          <h2 className="type-heading-s text-primary">About this programme</h2>
          <p className="max-w-public type-body-m text-secondary">
            {program.description}
          </p>
        </div>

        {!open && program.openRoles.length > 0 && (
          <p className="type-body-s text-muted">
            Applications are not open. Leaving your address above is the only
            thing to do here for now.
          </p>
        )}
      </PublicMain>

      <PublicFooter>
        <span>Run by {program.organisation.name}</span>
        {program.cohortStart && (
          <span>First sessions from {longDate(program.cohortStart)}</span>
        )}
        {program.timeCommitment && <span>{program.timeCommitment}</span>}
        {program.eligibility && (
          <span className="basis-full">{program.eligibility}</span>
        )}
      </PublicFooter>
    </>
  );
}

/**
 * Section 9: the hero is a live count. Three numbers in the mono face at
 * display size, and nothing competes with them.
 *
 * Section 1: scarcity is shown, not hidden. A full round prints a zero in muted
 * ink rather than dropping the number, because a missing number reads as an
 * arbitrary system and a zero reads as an honest one.
 */
function Stats({ program, now }: { program: Program; now: Date }) {
  const days = daysUntil(program.applicationsCloseAt, now);
  const spent = program.state === "closed" || program.state === "full";

  // A closed or full round has no places and no days left, whatever the stored
  // close date still says. Showing the real remaining figure beside a shut form
  // would be worse than showing nothing: it reads as a place you could have had.
  const stats: Array<{ value: number | null; label: string; spent: boolean }> = [
    {
      value: program.mentorCount,
      label: "Mentors joined",
      spent: false,
    },
    {
      value: spent ? 0 : (program.placesRemaining ?? null),
      label: "Places remaining",
      spent: spent || program.placesRemaining === 0,
    },
    {
      value: spent ? 0 : days,
      label: "Days until applications close",
      spent: spent || days === 0,
    },
  ];

  return (
    <dl className="flex flex-col gap-16 md:grid md:grid-cols-3 md:gap-24">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="flex items-baseline gap-12 md:flex-col md:items-start md:gap-8"
        >
          <dd
            className={`type-data-l md:type-data-xl ${stat.spent ? "text-muted" : "text-primary"}`}
          >
            {stat.value ?? "—"}
          </dd>
          <dt className={`type-label ${stat.spent ? "text-muted" : "text-secondary"}`}>
            {stat.label}
          </dt>
        </div>
      ))}
    </dl>
  );
}

/**
 * The headline is the anchor message, not the programme name. The name is the
 * eyebrow above the counts. Design direction 5.2 allows the display face here,
 * as place five of five.
 */
function Hero({
  program,
  orgSlug,
  programSlug,
}: {
  program: Program;
  orgSlug: string;
  programSlug: string;
}) {
  const { headline, body } = heroCopy(program);
  const canApply = program.state === "open" && program.openRoles.length > 0;

  // One bold thing per screen. Mentee is the primary path because the
  // programme's scarce resource is mentors, not places to apply for.
  const primaryRole = program.openRoles.includes("mentee") ? "mentee" : "mentor";
  const otherRole = primaryRole === "mentee" ? "mentor" : "mentee";
  const showOther = program.openRoles.includes(otherRole);

  return (
    <div className="flex flex-col gap-32">
      <h1 className="max-w-public type-display-l text-primary md:type-display-xl">
        {headline}
      </h1>

      <p className="max-w-public type-body-l text-secondary">{body}</p>

      {canApply ? (
        <div className="flex flex-col gap-16 md:flex-row md:items-center md:gap-24">
          <Link
            href={`/p/${orgSlug}/${programSlug}/apply?role=${primaryRole}`}
            className={buttonClasses({ size: "lg" })}
          >
            {primaryRole === "mentee" ? "Apply to be mentored" : "Apply to mentor"}
          </Link>
          {showOther && (
            <p className="type-body-m text-secondary">
              Or{" "}
              <Link
                href={`/p/${orgSlug}/${programSlug}/apply?role=${otherRole}`}
                className="text-link underline"
              >
                {otherRole === "mentor" ? "join as a mentor" : "apply to be mentored"}
              </Link>
              .
            </p>
          )}
        </div>
      ) : (
        <WaitlistForm orgSlug={orgSlug} programSlug={programSlug} />
      )}
    </div>
  );
}

function heroCopy(program: Program) {
  const mentors = inWords(program.mentorCount);
  const closes = program.applicationsCloseAt
    ? longDate(program.applicationsCloseAt)
    : null;
  const matching = program.matchingOpensAt
    ? longDate(program.matchingOpensAt)
    : null;

  switch (program.state) {
    case "open": {
      const dates =
        closes && matching
          ? ` Applications close on ${closes} and matching runs on ${matching}.`
          : closes
            ? ` Applications close on ${closes}.`
            : "";
      return {
        headline: "You are not the only one in the room.",
        body: `${mentors} people who have done the work you are starting have signed up to walk it with you.${dates}`,
      };
    }

    case "not_yet_open":
      return {
        headline: "This round has not opened yet.",
        body: `${mentors} mentors have signed up so far. Leave your address and we will write to you the day applications open.`,
      };

    case "full":
      return {
        headline: "This round is full.",
        body: `Every place has been taken. ${mentors} mentors are already matched. Leave your address and we will write to you the day the next round opens.`,
      };

    case "closed":
    default:
      return {
        headline: "Applications have closed.",
        body: `Applications closed${closes ? ` on ${closes}` : ""}. The next round opens later in the year and we will write to you the day it does.`,
      };
  }
}
