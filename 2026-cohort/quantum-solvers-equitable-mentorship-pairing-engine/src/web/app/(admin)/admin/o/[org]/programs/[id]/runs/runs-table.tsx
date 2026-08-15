"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api, type Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";

type Run = Schemas["Run"];

const dateTime = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "UTC",
});

/** 5.11: every run with its timestamp, recipe, counts, coverage and publisher. */
export function RunsTable({
  runs,
  programId,
  orgSlug,
}: {
  runs: Run[];
  programId: string;
  orgSlug: string;
}) {
  const router = useRouter();
  const [conflict, setConflict] = useState<string | undefined>();

  const start = useMutation({
    mutationFn: async () => {
      const { data, error, response } = await api.POST(
        "/programs/{programId}/runs",
        { params: { path: { programId } } },
      );
      if (error || !data) {
        throw new Error(
          response.status === 409
            ? "A run is already going. Open it rather than starting a second."
            : (error?.message ?? "The run did not start."),
        );
      }
      return data;
    },
    onSuccess: (run) => {
      setConflict(undefined);
      // Straight into review: the run is already queued and the review screen
      // is what follows it to drafted.
      router.push(`/admin/o/${orgSlug}/runs/${run.id}`);
    },
    onError: (e: Error) => setConflict(e.message),
  });

  const columns: Array<Column<Run>> = [
    {
      key: "createdAt",
      header: "Started",
      cell: (r) => (
        <Link
          href={`/admin/o/${orgSlug}/runs/${r.id}`}
          className="text-link underline outline-focus outline-offset-2 focus-visible:outline-2"
        >
          {dateTime.format(new Date(r.createdAt))}
        </Link>
      ),
      csv: (r) => r.createdAt,
    },
    {
      key: "state",
      header: "State",
      cell: (r) => readableState(r.state),
      csv: (r) => r.state,
    },
    {
      key: "recipeVersion",
      header: "Recipe",
      numeric: true,
      cell: (r) => (r.recipeVersion ? `v${r.recipeVersion}` : "—"),
      csv: (r) => r.recipeVersion ?? "",
    },
    {
      key: "draftedCount",
      header: "Drafted",
      numeric: true,
      cell: (r) => r.draftedCount ?? 0,
      csv: (r) => r.draftedCount ?? 0,
    },
    {
      key: "publishedCount",
      header: "Published",
      numeric: true,
      cell: (r) => r.publishedCount ?? 0,
      csv: (r) => r.publishedCount ?? 0,
    },
    {
      key: "coverageRate",
      header: "Coverage",
      numeric: true,
      cell: (r) =>
        r.coverageRate === null || r.coverageRate === undefined
          ? "—"
          : `${Math.round(r.coverageRate * 100)}%`,
      csv: (r) =>
        r.coverageRate === null || r.coverageRate === undefined
          ? ""
          : Math.round(r.coverageRate * 100),
    },
    {
      key: "publishedBy",
      header: "Published by",
      cell: (r) => r.publishedBy ?? "—",
      csv: (r) => r.publishedBy ?? "",
    },
  ];

  return (
    <div className="flex flex-col gap-16">
      <div className="flex flex-wrap items-center justify-between gap-16">
        <h1 className="type-heading-l text-primary">Matching runs</h1>
        <Button
          onClick={() => start.mutate()}
          loading={start.isPending}
          loadingLabel="Starting the run"
        >
          Start a run
        </Button>
      </div>

      {conflict && (
        <p role="alert" className="type-body-s text-danger">
          {conflict}
        </p>
      )}

      <DataTable
        caption="Every matching run for this programme"
        columns={columns}
        rows={runs}
        getRowId={(r) => r.id}
        csvFileName="runs.csv"
        filters={null}
        empty={
          <EmptyState
            markId="runs-empty"
            title="No runs yet."
            body="A run pairs everyone on the roster at once and shows you the fairness summary before anything is published. Nothing is sent until you publish it."
            action={
              <Button
                onClick={() => start.mutate()}
                loading={start.isPending}
                loadingLabel="Starting the run"
              >
                Start the first run
              </Button>
            }
          />
        }
      />
    </div>
  );
}

/** Exhaustive: a new run state fails the build rather than leaking a wire value. */
function readableState(state: Schemas["RunState"]) {
  switch (state) {
    case "queued":
      return "Queued";
    case "running":
      return "Running";
    case "drafted":
      return "Drafted, not published";
    case "published":
      return "Published";
    case "discarded":
      return "Discarded";
  }
}
