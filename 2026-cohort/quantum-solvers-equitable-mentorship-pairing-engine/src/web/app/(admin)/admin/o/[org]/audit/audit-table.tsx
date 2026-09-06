"use client";

import Link from "next/link";
import type { Schemas } from "@/lib/api/client";
import { DataTable, type Column } from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";

type AuditEvent = Schemas["AuditEvent"];
type Action = Schemas["AuditAction"];

/** Plain words. A log that needs the reader to know the schema is not
 *  inspectable by the people it exists for. */
const ACTION_WORD: Record<Action, string> = {
  criteria_saved: "Criteria changed",
  form_published: "Form published",
  run_published: "Run published",
  pair_overridden: "Pair overridden",
  manual_pairing: "Paired by hand",
  application_decided: "Application decided",
  participant_edited: "Edited on someone's behalf",
  strand_ended: "Strand ended",
  broadcast_sent: "Message sent",
  template_edited: "Template edited",
  data_exported: "Data exported",
};

const dateTime = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "UTC",
});

export function AuditTable({
  page,
  basePath,
  filters,
}: {
  page: Schemas["AuditPage"];
  basePath: string;
  filters: { actor?: string; action?: string; from?: string; to?: string };
}) {
  const columns: Array<Column<AuditEvent>> = [
    {
      key: "at",
      header: "When",
      cell: (e) => dateTime.format(new Date(e.at)),
      csv: (e) => e.at,
    },
    {
      key: "actorName",
      header: "Who",
      cell: (e) => e.actorName,
      csv: (e) => e.actorName,
    },
    {
      key: "action",
      header: "What",
      cell: (e) => ACTION_WORD[e.action],
      csv: (e) => e.action,
    },
    {
      key: "summary",
      header: "Detail",
      cell: (e) => e.summary,
      csv: (e) => e.summary,
    },
  ];

  const href = (patch: Record<string, string | undefined>) => {
    const params = new URLSearchParams();
    const merged = { ...filters, ...patch };
    for (const [key, value] of Object.entries(merged)) {
      if (value) params.set(key, value);
    }
    const query = params.toString();
    return query ? `${basePath}?${query}` : basePath;
  };

  return (
    <DataTable
      caption="Everything changed in this organisation, newest first"
      columns={columns}
      rows={page.items}
      getRowId={(e) => e.id}
      csvFileName="audit-log.csv"
      empty={
        <EmptyState
          markId="audit-empty"
          title="Nothing recorded in this range."
          body="Every change a coordinator makes lands here — criteria, forms, published runs, hand-picked pairs and exports. Widen the filters to see more."
        />
      }
      filters={
        <>
          <Chips
            label="Who"
            current={filters.actor}
            options={page.actors.map((a) => ({ value: a, label: a }))}
            href={(value) => href({ actor: value })}
          />
          <Chips
            label="What"
            current={filters.action}
            options={(Object.keys(ACTION_WORD) as Action[]).map((a) => ({
              value: a,
              label: ACTION_WORD[a],
            }))}
            href={(value) => href({ action: value })}
          />
        </>
      }
    />
  );
}

function Chips({
  label,
  current,
  options,
  href,
}: {
  label: string;
  current: string | undefined;
  options: Array<{ value: string; label: string }>;
  href: (value: string | undefined) => string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-8">
      <span className="type-label text-muted">{label}</span>
      <Link
        href={href(undefined)}
        aria-current={current ? undefined : "page"}
        className={chipClass(!current)}
      >
        Any
      </Link>
      {options.map((option) => (
        <Link
          key={option.value}
          href={href(option.value)}
          aria-current={current === option.value ? "page" : undefined}
          className={chipClass(current === option.value)}
        >
          {option.label}
        </Link>
      ))}
    </div>
  );
}

const chipClass = (active: boolean) =>
  [
    "pointer-coarse:min-h-field inline-flex items-center rounded-sm px-8 py-4 type-body-s",
    "outline-focus outline-offset-2 focus-visible:outline-2",
    active
      ? "bg-accent text-on-accent"
      : "border border-default text-secondary hover:text-primary",
  ].join(" ");
