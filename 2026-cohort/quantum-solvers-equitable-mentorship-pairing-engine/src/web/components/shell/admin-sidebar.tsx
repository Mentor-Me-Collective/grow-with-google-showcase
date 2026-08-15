"use client";

import { usePathname } from "next/navigation";
import { WeaveMark } from "@/components/brand/weave-mark";
import type { Participation, Session } from "@/lib/auth/guard";
import { AvatarMenu } from "./avatar-menu";
import { NavLink } from "./nav-link";
import { adminNav } from "./nav-items";
import { ProgramSwitcher } from "./program-switcher";

export function AdminSidebar({
  session,
  programmes,
  current,
}: {
  session: Session;
  programmes: Participation[];
  current: Participation;
}) {
  const pathname = usePathname();

  // Most sidebar links need a programme id, but /admin/o/:org carries none.
  // Take it from the URL when present, otherwise fall back to the default.
  const fromPath = pathname.match(/\/programs\/([^/]+)/)?.[1];
  const programId = fromPath ?? current.programId;
  const selected =
    programmes.find((p) => p.programId === programId) ?? current;

  const groups = adminNav(current.orgSlug, programId);

  return (
    // Dropped when printing, per architecture 7: the one deliverable that gets
    // printed is the report, and navigation on paper is furniture.
    <div className="flex w-sidebar shrink-0 flex-col gap-24 overflow-y-auto border-r border-subtle bg-surface px-16 py-16 print:hidden">
      <div className="flex items-center justify-between gap-8">
        <span className="flex min-w-0 items-center gap-8">
          <WeaveMark size={32} id="admin-mark" />
          <span className="truncate type-heading-s text-primary">
            {current.organisationName}
          </span>
        </span>
        <AvatarMenu account={session.account} />
      </div>

      <ProgramSwitcher
        programmes={programmes}
        current={selected}
        hrefFor={(p) => `/admin/o/${p.orgSlug}/programs/${p.programId}/roster`}
      />

      <nav aria-label="Coordinator" className="flex flex-col gap-24">
        {groups.map((group) => (
          <div key={group.label} className="flex flex-col gap-4">
            <h2 className="px-12 type-label text-muted">
              {group.label}
            </h2>
            <ul className="flex flex-col">
              {group.items.map((item) => (
                <li key={item.href}>
                  <NavLink
                    href={item.href}
                    exact={item.exact}
                    className="flex min-h-48 items-center rounded-md border-l-2 px-12 type-body-s transition-colors duration-instant"
                    activeClassName="border-strong bg-sunken text-primary"
                    idleClassName="border-surface text-secondary hover:bg-sunken hover:text-primary"
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </div>
  );
}
