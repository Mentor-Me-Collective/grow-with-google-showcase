"use client";

import { useMemo, useState } from "react";
import type { Schemas } from "@/lib/api/client";
import { DataTable, type Column, type SortState } from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";

type Entry = Schemas["RosterEntry"];

type RoleFilter = "all" | Schemas["Role"];
type MatchFilter = "all" | "matched" | "unmatched";

const dateFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

/**
 * Architecture 5.9. Filtering happens here rather than through the endpoint:
 * the whole roster of a cohort is one page of a few dozen rows, and a round
 * trip per checkbox would make the table feel worse for no benefit. The
 * endpoint's role, status and matched parameters are the right tool once a
 * programme is large enough to paginate, and the server component already
 * passes page size for that reason.
 */
export function RosterTable({ entries }: { entries: Entry[] }) {
  const [role, setRole] = useState<RoleFilter>("all");
  const [matched, setMatched] = useState<MatchFilter>("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortState>({ key: "name", direction: "asc" });
  const [selected, setSelected] = useState<string[]>([]);

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = entries.filter((e) => {
      if (role !== "all" && e.role !== role) return false;
      if (matched === "matched" && !e.matched) return false;
      if (matched === "unmatched" && e.matched) return false;
      if (needle && !e.account.name.toLowerCase().includes(needle)) return false;
      return true;
    });

    if (!sort) return filtered;
    const direction = sort.direction === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => direction * compare(sort.key, a, b));
  }, [entries, role, matched, query, sort]);

  const columns: Array<Column<Entry>> = [
    {
      key: "name",
      header: "Name",
      sortable: true,
      cell: (e) => e.account.name,
      csv: (e) => e.account.name,
    },
    {
      key: "role",
      header: "Role",
      sortable: true,
      cell: (e) => capitalise(e.role),
      csv: (e) => e.role,
    },
    {
      key: "matched",
      header: "Matched",
      sortable: true,
      // Colour never carries meaning alone, so this is a word, not a dot.
      cell: (e) => (e.matched ? "Yes" : "No"),
      csv: (e) => (e.matched ? "yes" : "no"),
    },
    {
      key: "load",
      header: "Load",
      numeric: true,
      sortable: true,
      /**
       * Mentors only, and load may exceed capacity — a mentor over capacity is
       * the thing a coordinator most needs to see, so it is stated as a
       * fraction rather than hidden behind a colour.
       */
      cell: (e) =>
        e.capacity === null || e.capacity === undefined
          ? "—"
          : `${e.load ?? 0}/${e.capacity}`,
      csv: (e) =>
        e.capacity === null || e.capacity === undefined
          ? ""
          : `${e.load ?? 0}/${e.capacity}`,
    },
    {
      key: "profileCompleteness",
      header: "Profile",
      numeric: true,
      sortable: true,
      cell: (e) => `${Math.round(e.profileCompleteness * 100)}%`,
      csv: (e) => Math.round(e.profileCompleteness * 100),
    },
    {
      key: "timezone",
      header: "Time zone",
      cell: (e) => e.timezone ?? "—",
      csv: (e) => e.timezone ?? "",
    },
    {
      key: "joinedAt",
      header: "Joined",
      sortable: true,
      cell: (e) => dateFormat.format(new Date(e.joinedAt)),
      csv: (e) => e.joinedAt,
    },
  ];

  return (
    <DataTable
      caption="Everyone approved into this programme"
      columns={columns}
      rows={rows}
      getRowId={(e) => e.id}
      sort={sort}
      onSortChange={setSort}
      selectable
      selectedIds={selected}
      onSelectionChange={setSelected}
      csvFileName="roster.csv"
      empty={
        entries.length === 0 ? (
          <EmptyState
            markId="roster-empty"
            title="Nobody has been approved yet."
            body="Approved applicants land here. Until then the applications queue is where the work is."
          />
        ) : (
          <EmptyState
            markId="roster-filtered"
            title="No one matches those filters."
            body="Widen the filters to see the rest of the roster."
          />
        )
      }
      /**
       * 5.9 also lists invite, CSV import, change role, remove, message and
       * export. Only export exists in the contract today, so the action bar
       * carries the count alone rather than buttons that would do nothing.
       */
      bulkActions={() => null}
      filters={
        <>
          <label className="flex items-center gap-8 type-body-s text-secondary">
            Search
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Name"
              className="h-field rounded-sm border border-default bg-surface px-12 type-body-s text-primary placeholder:text-muted focus:border-accent focus:outline-none focus:ring-3 focus:ring-focus-halo"
            />
          </label>

          <Select
            label="Role"
            value={role}
            onChange={(v) => setRole(v as RoleFilter)}
            options={[
              { value: "all", label: "Everyone" },
              { value: "mentor", label: "Mentors" },
              { value: "mentee", label: "Mentees" },
            ]}
          />

          <Select
            label="Matched"
            value={matched}
            onChange={(v) => setMatched(v as MatchFilter)}
            options={[
              { value: "all", label: "Any" },
              { value: "matched", label: "Matched" },
              { value: "unmatched", label: "Unmatched" },
            ]}
          />
        </>
      }
    />
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <label className="flex items-center gap-8 type-body-s text-secondary">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-field rounded-sm border border-default bg-surface px-12 type-body-s text-primary focus:border-accent focus:outline-none focus:ring-3 focus:ring-focus-halo"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function compare(key: string, a: Entry, b: Entry) {
  switch (key) {
    case "role":
      return a.role.localeCompare(b.role);
    case "matched":
      return Number(a.matched) - Number(b.matched);
    case "load":
      return (a.load ?? -1) - (b.load ?? -1);
    case "profileCompleteness":
      return a.profileCompleteness - b.profileCompleteness;
    case "joinedAt":
      return a.joinedAt.localeCompare(b.joinedAt);
    default:
      return a.account.name.localeCompare(b.account.name);
  }
}

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
