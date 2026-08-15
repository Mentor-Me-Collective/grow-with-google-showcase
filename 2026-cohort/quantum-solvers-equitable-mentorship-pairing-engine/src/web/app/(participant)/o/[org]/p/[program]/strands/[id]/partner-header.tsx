"use client";

import { useId, useState } from "react";
import type { components } from "@/lib/api/types";
import { Avatar } from "@/components/ui/avatar";
import { ChevronDownIcon } from "@/components/icon/icons";
import { PartnerCard } from "./partner-card";

type S = components["schemas"];

/**
 * Below md the conversation is the page, so the partner card collapses to a
 * header that expands on tap.
 *
 * The "why you were matched" line is not what collapses. Section 9 is explicit
 * that it is always visible and never behind a disclosure, so it stays in the
 * header, truncated to one line, and only the facts underneath fold away.
 */
export function PartnerHeader({
  strand,
  others,
}: {
  strand: S["Strand"];
  others: S["StrandMember"][];
}) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const partner = others[0];
  if (!partner) return null;

  const isGroup = others.length > 1;
  const name = isGroup
    ? others.map((m) => m.name.split(" ")[0]).join(", ")
    : partner.name;

  return (
    <div className="flex flex-col gap-12">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className="flex w-full min-h-field items-center gap-12 rounded-md border border-subtle bg-surface p-12 text-left transition-colors duration-instant ease-out outline-focus outline-offset-2 hover:border-default focus-visible:outline-2"
      >
        <Avatar
          name={partner.name}
          participationId={partner.participationId}
          size={36}
        />
        <span className="flex min-w-0 flex-1 flex-col">
          <span className="truncate type-body-m font-semibold text-primary">{name}</span>
          {strand.matchRationale && (
            <span className="truncate type-body-s text-secondary">
              {strand.matchRationale}
            </span>
          )}
        </span>
        <ChevronDownIcon
          aria-hidden="true"
          className={`size-16 shrink-0 text-secondary transition-transform duration-quick ease-out ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {open && (
        <div id={panelId}>
          <PartnerCard strand={strand} others={others} />
        </div>
      )}
    </div>
  );
}
