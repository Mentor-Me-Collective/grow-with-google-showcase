"use client";

import { CheckIcon, SortIcon } from "@/components/icon/icons";
import { Button } from "./button";
import { EmptyState } from "./empty-state";

export type SortState = { key: string; direction: "asc" | "desc" } | null;

export type Column<Row> = {
  key: string;
  header: string;
  /** Right-aligned and set in data-m, per 8.4. */
  numeric?: boolean;
  sortable?: boolean;
  cell: (row: Row) => React.ReactNode;
  /** Value written to CSV. Defaults to nothing, so give it for exportable columns. */
  csv?: (row: Row) => string | number;
};

export type DataTableProps<Row> = {
  /** Describes the table to a screen reader. Not optional. */
  caption: string;
  columns: Array<Column<Row>>;
  rows: Row[];
  getRowId: (row: Row) => string;

  /**
   * 8.4 says every table has a filter bar above it. Required rather than
   * optional so a screen with nothing to filter passes `null` deliberately
   * instead of forgetting.
   */
  filters: React.ReactNode;

  loading?: boolean;
  error?: string;
  onRetry?: () => void;
  empty?: React.ReactNode;

  sort?: SortState;
  onSortChange?: (sort: SortState) => void;

  selectable?: boolean;
  selectedIds?: string[];
  onSelectionChange?: (ids: string[]) => void;
  /** Rendered in the action bar that replaces the header row. */
  bulkActions?: (selectedIds: string[]) => React.ReactNode;

  csvFileName?: string;
};

function Checkbox({
  checked,
  indeterminate,
  onChange,
  label,
}: {
  checked: boolean;
  indeterminate?: boolean;
  onChange: (next: boolean) => void;
  label: string;
}) {
  return (
    <label className="inline-flex size-24 cursor-pointer items-center justify-center">
      <input
        type="checkbox"
        checked={checked}
        ref={(el) => {
          if (el) el.indeterminate = Boolean(indeterminate) && !checked;
        }}
        onChange={(e) => onChange(e.target.checked)}
        className="peer sr-only"
      />
      <span className="sr-only">{label}</span>
      <span
        aria-hidden="true"
        className={[
          "flex size-16 items-center justify-center rounded-xs border",
          "transition-colors duration-instant",
          "peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus",
          checked || indeterminate
            ? "border-accent bg-accent text-on-accent"
            : "border-default bg-surface",
        ].join(" ")}
      >
        {checked && <CheckIcon className="size-12" />}
        {!checked && indeterminate && (
          <span className="h-0 w-8 border-t-2 border-current" />
        )}
      </span>
    </label>
  );
}

function toCsv<Row>(columns: Array<Column<Row>>, rows: Row[]) {
  const exportable = columns.filter((c) => c.csv);
  const escape = (v: string | number) => {
    const s = String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [
    exportable.map((c) => escape(c.header)).join(","),
    ...rows.map((row) => exportable.map((c) => escape(c.csv!(row))).join(",")),
  ];
  return lines.join("\n");
}

export function DataTable<Row>({
  caption,
  columns,
  rows,
  getRowId,
  filters,
  loading = false,
  error,
  onRetry,
  empty,
  sort = null,
  onSortChange,
  selectable = false,
  selectedIds = [],
  onSelectionChange,
  bulkActions,
  csvFileName = "export.csv",
}: DataTableProps<Row>) {
  const columnCount = columns.length + (selectable ? 1 : 0);
  const selected = new Set(selectedIds);
  const allSelected = rows.length > 0 && rows.every((r) => selected.has(getRowId(r)));
  const someSelected = rows.some((r) => selected.has(getRowId(r)));
  const showActionBar = selectable && selectedIds.length > 0;

  const toggleAll = (next: boolean) =>
    onSelectionChange?.(next ? rows.map(getRowId) : []);

  const toggleRow = (id: string, next: boolean) =>
    onSelectionChange?.(
      next ? [...selectedIds, id] : selectedIds.filter((s) => s !== id),
    );

  const nextSort = (key: string): SortState =>
    sort?.key === key && sort.direction === "asc"
      ? { key, direction: "desc" }
      : { key, direction: "asc" };

  const download = () => {
    const blob = new Blob([toCsv(columns, rows)], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = csvFileName;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-12">
      {/* 8.4: a filter bar above, a row count below. */}
      {filters !== null && (
        <div className="flex flex-wrap items-center gap-8">{filters}</div>
      )}

      <div className="overflow-x-auto rounded-md border border-subtle bg-surface">
        <table className="w-full border-collapse">
          <caption className="sr-only">{caption}</caption>

          <thead className="sticky top-0 z-10">
            {showActionBar ? (
              // 8.4: replace the header row in place. Never float a toolbar.
              <tr className="h-48 bg-sunken">
                <th colSpan={columnCount} scope="colgroup" className="px-16 text-left">
                  <div
                    className="flex items-center gap-16"
                    role="status"
                    aria-live="polite"
                  >
                    <span className="type-body-s text-primary">
                      {selectedIds.length} selected
                    </span>
                    <span className="flex items-center gap-8">
                      {bulkActions?.(selectedIds)}
                    </span>
                    <button
                      type="button"
                      onClick={() => onSelectionChange?.([])}
                      className="ml-auto type-body-s text-link underline"
                    >
                      Clear selection
                    </button>
                  </div>
                </th>
              </tr>
            ) : (
              <tr className="h-48 bg-sunken">
                {selectable && (
                  <th scope="col" className="w-48 px-16">
                    <Checkbox
                      checked={allSelected}
                      indeterminate={someSelected}
                      onChange={toggleAll}
                      label="Select all rows"
                    />
                  </th>
                )}
                {columns.map((column) => {
                  const active = sort?.key === column.key;
                  const direction = active ? sort.direction : "asc";
                  return (
                    <th
                      key={column.key}
                      scope="col"
                      aria-sort={
                        active
                          ? direction === "asc"
                            ? "ascending"
                            : "descending"
                          : undefined
                      }
                      className={`px-16 type-label text-secondary ${
                        column.numeric ? "text-right" : "text-left"
                      }`}
                    >
                      {column.sortable && onSortChange ? (
                        <button
                          type="button"
                          onClick={() => onSortChange(nextSort(column.key))}
                          className="group inline-flex items-center gap-4 type-label text-secondary hover:text-primary"
                        >
                          {column.header}
                          {/* Direction shows on hover before click, per 8.4. */}
                          <SortIcon
                            direction={active ? direction : "asc"}
                            className={`size-12 ${
                              active ? "" : "invisible group-hover:visible"
                            }`}
                          />
                        </button>
                      ) : (
                        column.header
                      )}
                    </th>
                  );
                })}
              </tr>
            )}
          </thead>

          <tbody>
            {loading &&
              // Skeleton matches the real column count and row height, because
              // section 12 bans skeletons that do not match what follows.
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="h-48 border-t border-subtle">
                  {Array.from({ length: columnCount }).map((__, j) => (
                    <td key={j} className="px-16">
                      <span className="block h-12 w-64 animate-pulse rounded-sm bg-sunken" />
                    </td>
                  ))}
                </tr>
              ))}

            {!loading && error && (
              <tr>
                <td colSpan={columnCount} className="px-16 py-32">
                  <div className="flex flex-col items-center gap-12 text-center">
                    <p role="alert" className="type-body-m text-danger">
                      {error}
                    </p>
                    {onRetry && (
                      <Button variant="secondary" size="sm" onClick={onRetry}>
                        Try again
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            )}

            {!loading && !error && rows.length === 0 && (
              <tr>
                <td colSpan={columnCount}>
                  {empty ?? (
                    <EmptyState
                      title="Nothing to show yet"
                      body="Rows will appear here once there are any."
                      markId="table-empty-mark"
                    />
                  )}
                </td>
              </tr>
            )}

            {!loading &&
              !error &&
              rows.map((row) => {
                const id = getRowId(row);
                const isSelected = selected.has(id);
                return (
                  <tr
                    key={id}
                    // Zebra off, hairline borders on (8.4). Hover darkens only.
                    className={`h-48 border-t border-subtle transition-colors duration-instant hover:bg-sunken ${
                      isSelected ? "bg-sunken" : ""
                    }`}
                  >
                    {selectable && (
                      <td className="px-16">
                        <Checkbox
                          checked={isSelected}
                          onChange={(next) => toggleRow(id, next)}
                          label={`Select row ${id}`}
                        />
                      </td>
                    )}
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        className={`px-16 ${
                          column.numeric
                            ? "text-right type-data-m text-primary"
                            : "type-body-s text-primary"
                        }`}
                      >
                        {column.cell(row)}
                      </td>
                    ))}
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between gap-16">
        <p className="type-caption text-muted" role="status" aria-live="polite">
          {loading
            ? "Loading rows"
            : `${rows.length} ${rows.length === 1 ? "row" : "rows"}`}
        </p>
        <Button variant="ghost" size="sm" onClick={download} disabled={rows.length === 0}>
          Export CSV
        </Button>
      </div>
    </div>
  );
}
