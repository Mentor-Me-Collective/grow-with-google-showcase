"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { DataTable, type Column } from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";
import { decideApplications } from "./actions";

type Summary = Schemas["ApplicationSummary"];
type Decision = Schemas["DecisionKind"];

const dateFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  timeZone: "UTC",
});

const FLAG_WORDS: Record<Schemas["ApplicationFlag"], string> = {
  incomplete: "Incomplete",
  duplicate_email: "Duplicate email",
  reapplied: "Already on roster",
  over_subscribed_role: "Role oversubscribed",
};

const DECISION_VERB: Record<Decision, string> = {
  approve: "Approve",
  waitlist: "Waitlist",
  reject: "Reject",
};

export function ApplicationsTable({
  applications,
  counts,
  programId,
  basePath,
  status,
}: {
  applications: Summary[];
  counts: Schemas["ApplicationCounts"];
  programId: string;
  basePath: string;
  status: string;
}) {
  const router = useRouter();
  const [selected, setSelected] = useState<string[]>([]);
  const [pending, startTransition] = useTransition();
  const [confirming, setConfirming] = useState<Decision | null>(null);
  const [error, setError] = useState<string | undefined>();

  const run = (decision: Decision) =>
    startTransition(async () => {
      const result = await decideApplications({
        programId,
        applicationIds: selected,
        decision,
      });
      setConfirming(null);
      if (result.ok) {
        setSelected([]);
        setError(undefined);
        router.refresh();
      } else {
        setError(result.message);
      }
    });

  const columns: Array<Column<Summary>> = [
    {
      key: "name",
      header: "Name",
      cell: (a) => (
        <Link
          href={`${basePath}/${a.id}`}
          className="text-link underline outline-focus outline-offset-2 focus-visible:outline-2"
        >
          {a.name}
        </Link>
      ),
      csv: (a) => a.name,
    },
    { key: "email", header: "Email", cell: (a) => a.email, csv: (a) => a.email },
    {
      key: "role",
      header: "Role",
      cell: (a) => capitalise(a.role),
      csv: (a) => a.role,
    },
    {
      key: "submittedAt",
      header: "Submitted",
      cell: (a) => dateFormat.format(new Date(a.submittedAt)),
      csv: (a) => a.submittedAt,
    },
    {
      key: "completeness",
      header: "Answered",
      numeric: true,
      cell: (a) => `${Math.round(a.completeness * 100)}%`,
      csv: (a) => Math.round(a.completeness * 100),
    },
    {
      key: "flags",
      header: "Worth a look",
      // Named in words. A coloured dot would make the coordinator learn a
      // legend, and section 11 forbids colour carrying meaning alone.
      cell: (a) =>
        a.flags && a.flags.length > 0
          ? a.flags.map((f) => FLAG_WORDS[f]).join(", ")
          : "—",
      csv: (a) => (a.flags ?? []).join(" "),
    },
    {
      key: "status",
      header: "Status",
      cell: (a) => readableStatus(a.status),
      csv: (a) => a.status,
    },
  ];

  return (
    <>
      {error && (
        <p role="alert" className="type-body-s text-danger">
          {error}
        </p>
      )}

      <DataTable
        caption="Applications submitted to this programme"
        columns={columns}
        rows={applications}
        getRowId={(a) => a.id}
        selectable
        selectedIds={selected}
        onSelectionChange={setSelected}
        csvFileName="applications.csv"
        filters={<StatusTabs counts={counts} basePath={basePath} current={status} />}
        bulkActions={(ids) => (
          <>
            <Button
              size="sm"
              onClick={() => setConfirming("approve")}
              disabled={pending}
            >
              Approve {ids.length}
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => setConfirming("waitlist")}
              disabled={pending}
            >
              Waitlist
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => setConfirming("reject")}
              disabled={pending}
            >
              Reject
            </Button>
          </>
        )}
        empty={
          <EmptyState
            markId="applications-empty"
            title={
              status === "submitted"
                ? "Nothing waiting to be read."
                : "Nothing in this pile."
            }
            body={
              status === "submitted"
                ? "New applications land here the moment someone submits one. The programme link is what fills this page."
                : "Applications move here once you decide on them."
            }
          />
        }
      />

      <ConfirmDialog
        open={confirming !== null}
        title={
          confirming ? `${DECISION_VERB[confirming]} ${selected.length}?` : ""
        }
        confirmLabel={confirming ? DECISION_VERB[confirming] : ""}
        busy={pending}
        busyLabel="Saving"
        confirmVariant={confirming === "reject" ? "danger" : "primary"}
        onCancel={() => setConfirming(null)}
        onConfirm={() => confirming && run(confirming)}
        body={
          <div className="flex flex-col gap-12">
            <p>
              {confirming === "approve"
                ? `${selected.length} ${selected.length === 1 ? "person joins" : "people join"} the roster and can be matched in the next run.`
                : confirming === "waitlist"
                  ? `${selected.length} ${selected.length === 1 ? "person moves" : "people move"} to the waitlist. They stay out of matching until you approve them.`
                  : `${selected.length} ${selected.length === 1 ? "application is" : "applications are"} closed. This cannot be undone.`}
            </p>
          </div>
        }
      />
    </>
  );
}

/**
 * Status is in the URL rather than in state: it is the address of the pile
 * being worked, so it survives a refresh and can be sent to a colleague.
 */
function StatusTabs({
  counts,
  basePath,
  current,
}: {
  counts: Schemas["ApplicationCounts"];
  basePath: string;
  current: string;
}) {
  const tabs = [
    { key: "submitted", label: "To read", count: counts.submitted },
    { key: "under_review", label: "Reading", count: counts.under_review },
    { key: "approved", label: "Approved", count: counts.approved },
    { key: "waitlisted", label: "Waitlisted", count: counts.waitlisted },
    { key: "rejected", label: "Closed", count: counts.rejected },
  ];

  return (
    <nav aria-label="Filter by status" className="flex flex-wrap gap-8">
      {tabs.map((tab) => {
        const active = tab.key === current;
        return (
          <Link
            key={tab.key}
            href={`${basePath}?status=${tab.key}`}
            aria-current={active ? "page" : undefined}
            className={[
              "pointer-coarse:min-h-field inline-flex items-center gap-8 rounded-sm px-12 py-8 type-body-s",
              "outline-focus outline-offset-2 focus-visible:outline-2",
              active
                ? "bg-accent text-on-accent"
                : "border border-default text-secondary hover:text-primary",
            ].join(" ")}
          >
            {tab.label}
            <span className={active ? "type-data-m" : "type-data-m text-muted"}>
              {tab.count}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}

function readableStatus(status: Schemas["ApplicationStatus"]) {
  switch (status) {
    case "submitted":
      return "Waiting";
    case "under_review":
      return "Being read";
    case "approved":
      return "Approved";
    case "waitlisted":
      return "Waitlisted";
    case "rejected":
      return "Closed";
  }
}

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
