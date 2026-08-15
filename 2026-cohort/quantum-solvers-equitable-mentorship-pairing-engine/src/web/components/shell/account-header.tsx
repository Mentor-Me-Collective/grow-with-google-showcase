import { WeaveMark } from "@/components/brand/weave-mark";
import type { Session } from "@/lib/auth/guard";
import { AvatarMenu } from "./avatar-menu";
import { NavLink } from "./nav-link";

/** Account scope: no programme, so no switcher. */
export function AccountHeader({ session }: { session: Session }) {
  return (
    <header className="border-b border-subtle bg-surface">
      <div className="mx-auto flex max-w-participant items-center gap-16 px-16 py-8">
        <span className="flex shrink-0 items-center gap-8">
          <WeaveMark size={32} id="account-mark" />
          <span className="type-heading-s text-primary">Braid</span>
        </span>
        <div className="flex-1" />
        <AvatarMenu account={session.account} />
      </div>

      <nav
        aria-label="Account"
        className="mx-auto flex max-w-participant gap-4 px-16"
      >
        {[
          { label: "Settings", href: "/settings" },
          { label: "My programmes", href: "/programs" },
        ].map(({ label, href }) => (
          <NavLink
            key={href}
            href={href}
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
