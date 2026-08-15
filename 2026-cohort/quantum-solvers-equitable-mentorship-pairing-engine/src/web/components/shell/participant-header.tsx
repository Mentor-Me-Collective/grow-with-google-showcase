import { WeaveMark } from "@/components/brand/weave-mark";
import type { Participation, Session } from "@/lib/auth/guard";
import { AvatarMenu } from "./avatar-menu";
import { NavLink } from "./nav-link";
import { participantNav } from "./nav-items";
import { ProgramSwitcher } from "./program-switcher";

export function ParticipantHeader({
  session,
  participation,
}: {
  session: Session;
  participation: Participation;
}) {
  const items = participantNav(participation.orgSlug, participation.programSlug);

  return (
    <header className="border-b border-subtle bg-surface">
      <div className="mx-auto flex max-w-participant items-center gap-16 px-16 py-8">
        <span className="flex shrink-0 items-center gap-8">
          <WeaveMark size={32} id="participant-mark" />
          <span className="sr-only">{participation.organisationName}</span>
        </span>

        <div className="min-w-0 flex-1">
          <ProgramSwitcher
            programmes={session.participations}
            current={participation}
          />
        </div>

        <AvatarMenu account={session.account} />
      </div>

      {/* Below md this is replaced by the bottom tab bar. */}
      <nav
        aria-label="Programme"
        className="mx-auto hidden max-w-participant gap-4 px-16 md:flex"
      >
        {items.map(({ label, href, exact }) => (
          <NavLink
            key={href}
            href={href}
            exact={exact}
            className="flex min-h-48 items-center border-b-2 px-12 type-body-m transition-colors duration-instant"
            activeClassName="border-strong text-primary"
            idleClassName="border-surface text-secondary hover:text-primary"
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
