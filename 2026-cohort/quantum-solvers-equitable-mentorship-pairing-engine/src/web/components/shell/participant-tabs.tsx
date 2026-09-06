import type { Participation } from "@/lib/auth/guard";
import { NavLink } from "./nav-link";
import { participantNav } from "./nav-items";

/** The mobile counterpart to the header nav. Hidden from md up. */
export function ParticipantTabs({
  participation,
}: {
  participation: Participation;
}) {
  const items = participantNav(participation.orgSlug, participation.programSlug);

  return (
    <nav
      aria-label="Programme"
      className="sticky bottom-0 border-t border-subtle bg-surface md:hidden"
    >
      <ul className="flex">
        {items.map(({ label, href, exact, Icon }) => (
          <li key={href} className="flex-1">
            <NavLink
              href={href}
              exact={exact}
              // The top rule is the non-colour indicator: colour alone must
              // never carry the active state (accessibility floor, 11).
              className="flex min-h-48 flex-col items-center justify-center gap-4 border-t-2 py-8 type-caption transition-colors duration-instant"
              activeClassName="border-strong text-primary"
              idleClassName="border-surface text-muted"
            >
              <Icon className="size-24" />
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
