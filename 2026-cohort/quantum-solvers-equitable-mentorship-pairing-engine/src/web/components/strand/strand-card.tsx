import Link from "next/link";
import type { components } from "@/lib/api/types";
import { Avatar, RoleChip, strandColour, type Tone } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

type StrandSummary = components["schemas"]["StrandSummary"];

/** 8.3: a strand goes quiet after fourteen days with no activity. */
const QUIET_AFTER_DAYS = 14;
const DAY = 86_400_000;

function capitalise(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Whole weeks up to eight, then whole months. 8.3 gives the threshold and the
 * phrasing but not the rounding; this floors, so the line never overstates how
 * long the silence has been. The floor cannot produce "1 week", because the
 * state does not begin until day fourteen.
 */
function quietFor(days: number) {
  const weeks = Math.floor(days / 7);
  if (weeks < 8) return `Quiet for ${weeks} weeks`;
  const months = Math.round(days / 30.44);
  return `Quiet for ${months} month${months === 1 ? "" : "s"}`;
}

/**
 * Dates format against a fixed zone so the server and the client agree on the
 * string. The member's own zone arrives with the profile work.
 */
function formatSession(iso: string, timeZone: string) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone,
  }).format(new Date(iso));
}

function formatEnded(iso: string, timeZone: string) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    timeZone,
  }).format(new Date(iso));
}

// Geometry only. The border colour is set per state at the call site: two
// border-colour utilities on one element resolve by stylesheet order rather
// than by the order they are written, so the shell must not hold a default.
const CARD_SHELL =
  "block rounded-md border bg-surface p-16 " +
  "transition-colors duration-instant ease-out " +
  "outline-focus outline-offset-2 focus-visible:outline-2";

/**
 * 8.3, the most-seen component in the participant shell. Border and no shadow,
 * radius-md, 16px padding, a 40px avatar, the name in heading-s, the partner's
 * role in a chip tinted with their strand colour, and one line of preview.
 *
 * The right side carries one thing rather than two: 8.3 reads "unread count
 * ... or the next session time", so an unread strand shows its count and the
 * session waits until the messages have been read.
 *
 * Quiet and ended both replace the preview with a plain muted line. Neither is
 * an error, so neither gets red, an icon, or a raised voice.
 */
export function StrandCard({
  strand,
  href,
  now = new Date(),
  timeZone = "UTC",
}: {
  strand: StrandSummary;
  href: string;
  /** Injected so a fixed clock can be demonstrated and tested. */
  now?: Date;
  timeZone?: string;
}) {
  const members = strand.members;
  const isGroup = members.length > 1;
  const ended = strand.state === "ended";
  const partner = members[0];

  const daysQuiet = strand.lastActivityAt
    ? Math.floor(
        (now.getTime() - new Date(strand.lastActivityAt).getTime()) / DAY,
      )
    : null;
  const quiet = !ended && daysQuiet !== null && daysQuiet >= QUIET_AFTER_DAYS;

  const unread = ended ? 0 : strand.unreadCount;
  const session = !ended && unread === 0 ? strand.nextSessionAt : null;

  const title = isGroup
    ? members.map((m) => m.name).join(", ")
    : (partner?.name ?? "This strand");

  // The group chip carries the count, including the person reading it, so the
  // preview line is not spent saying how many people are in the strand.
  const chip = isGroup
    ? `Group of ${members.length + 1}`
    : capitalise(partner?.role ?? "");

  const chipTone: Tone =
    ended || isGroup || !partner ? "none" : strandColour(partner.participationId);

  // One line under the name. The strand's condition outranks its last message,
  // because "this ended in March" is more use than what was said before it did.
  let secondary: { text: string; muted: boolean } | null = null;
  if (ended) {
    secondary = {
      text: strand.endedAt
        ? `Ended ${formatEnded(strand.endedAt, timeZone)}`
        : "Ended",
      muted: true,
    };
  } else if (quiet && daysQuiet !== null) {
    secondary = { text: quietFor(daysQuiet), muted: true };
  } else if (strand.lastMessage) {
    secondary = { text: strand.lastMessage.body, muted: false };
  }

  // Colour never carries meaning alone, so the count, the ended date and the
  // quiet line all reach a screen reader as words rather than as a pink dot.
  const label = [
    title,
    chip,
    unread > 0
      ? `${unread} unread ${unread === 1 ? "message" : "messages"}`
      : null,
    session ? `Next session ${formatSession(session, timeZone)}` : null,
    secondary?.muted ? secondary.text : null,
  ]
    .filter(Boolean)
    .join(". ");

  return (
    <Link
      href={href}
      aria-label={label}
      className={`${CARD_SHELL} border-subtle hover:border-default`}
    >
      <span className="flex items-center gap-12">
        {isGroup ? (
          <span className="flex shrink-0 items-center">
            {members.slice(0, 3).map((m, i) => (
              <span
                key={m.participationId}
                // Overlap by 12, with an outline in the card colour so the
                // edges stay separable instead of merging into one shape.
                // Outline rather than a ring: rings are box-shadows, and a
                // card never carries a shadow.
                className={
                  i === 0
                    ? "rounded-full"
                    : "-ml-12 rounded-full outline-2 outline-surface"
                }
              >
                <Avatar
                  name={m.name}
                  participationId={m.participationId}
                  neutral={ended}
                />
              </span>
            ))}
          </span>
        ) : partner ? (
          <Avatar
            name={partner.name}
            participationId={partner.participationId}
            neutral={ended}
          />
        ) : null}

        <span className="flex min-w-0 flex-1 flex-col gap-4">
          <span className="flex min-w-0 items-center gap-8">
            <span className="truncate type-heading-s text-primary">{title}</span>
            <RoleChip tone={chipTone}>{chip}</RoleChip>
          </span>

          {secondary && (
            <span
              className={`truncate type-body-s ${
                secondary.muted ? "text-muted" : "text-secondary"
              }`}
            >
              {secondary.text}
            </span>
          )}
        </span>

        {unread > 0 && (
          <span className="badge-count inline-flex items-center justify-center rounded-full bg-accent type-data-m text-on-accent">
            {unread}
          </span>
        )}

        {session && (
          <span className="shrink-0 type-data-m text-primary">
            {formatSession(session, timeZone)}
          </span>
        )}
      </span>
    </Link>
  );
}

/** Same geometry as a real card, so the list does not jump when it resolves. */
export function StrandCardSkeleton() {
  return (
    <div aria-hidden="true" className={`${CARD_SHELL} border-subtle animate-pulse`}>
      <div className="flex items-center gap-12">
        <div className="avatar rounded-full bg-sunken" />
        <div className="flex min-w-0 flex-1 flex-col gap-8">
          <div className="h-24 w-1/3 rounded-sm bg-sunken" />
          <div className="h-16 w-2/3 rounded-sm bg-sunken" />
        </div>
      </div>
    </div>
  );
}

/**
 * The card's error state. Says what failed and what is still true, because the
 * first thing someone fears when a conversation will not load is that they
 * have lost it.
 */
export function StrandCardError({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className={`${CARD_SHELL} border-danger`} role="alert">
      <div className="flex flex-wrap items-center justify-between gap-12">
        <p className="type-body-s text-secondary">
          This strand did not load. Your messages are safe.
        </p>
        {onRetry && (
          <Button size="sm" variant="secondary" onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>
    </div>
  );
}
