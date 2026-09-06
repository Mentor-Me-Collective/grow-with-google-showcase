"use client";

import Link from "next/link";
import { CheckIcon, ChevronDownIcon } from "@/components/icon/icons";
import type { Participation } from "@/lib/auth/guard";
import { useDropdown } from "./use-dropdown";

export function ProgramSwitcher({
  programmes,
  current,
  hrefFor = (p) => `/o/${p.orgSlug}/p/${p.programSlug}`,
}: {
  programmes: Participation[];
  current: Participation;
  /** The coordinator shell points the same control at its own routes. */
  hrefFor?: (participation: Participation) => string;
}) {
  const { open, setOpen, close, triggerRef, panelRef } = useDropdown();

  return (
    <div className="relative min-w-0">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-haspopup="menu"
        // w-full: a button is fit-content by default, so without this it
        // refuses to shrink inside a min-w-0 parent and truncate never fires.
        className="flex min-h-48 w-full min-w-0 items-center gap-8 rounded-md px-12 type-body-m text-primary transition-colors duration-instant hover:bg-sunken"
      >
        <span className="truncate">{current.programName}</span>
        <ChevronDownIcon className="size-16 shrink-0 text-muted" />
      </button>

      {open && (
        <div
          ref={panelRef}
          role="menu"
          aria-label="Switch programme"
          className="absolute left-0 top-full z-10 mt-4 w-max min-w-full rounded-md border border-subtle bg-surface p-4 shadow-raised"
        >
          {programmes.map((programme) => {
            const isCurrent = programme.id === current.id;
            return (
              <Link
                key={programme.id}
                role="menuitem"
                href={hrefFor(programme)}
                onClick={() => close(false)}
                aria-current={isCurrent ? "true" : undefined}
                className="flex min-h-48 items-center gap-12 rounded-sm px-12 py-8 transition-colors duration-instant hover:bg-sunken"
              >
                <CheckIcon
                  className={`size-16 shrink-0 text-primary ${isCurrent ? "" : "invisible"}`}
                />
                <span className="flex flex-col">
                  <span className="type-body-s text-primary">
                    {programme.programName}
                  </span>
                  <span className="type-caption text-muted">
                    {programme.organisationName} · {programme.role}
                  </span>
                </span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
