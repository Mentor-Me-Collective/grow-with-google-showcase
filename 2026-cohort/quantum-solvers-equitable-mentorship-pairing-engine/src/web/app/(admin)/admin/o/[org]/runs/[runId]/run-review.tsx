"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, type Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { FairnessSummary } from "./fairness-summary";

type RunDetail = Schemas["RunDetail"];

const dateTime = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "UTC",
});

/**
 * Architecture 5.12. A run is a stored object with a state, not a function
 * call, so this screen follows it rather than waiting on a request.
 *
 * Polling rather than a stream because the contract offers no stream. It stops
 * the moment the run leaves queued or running, so a drafted run costs nothing.
 */
export function RunReview({
  runId,
  orgSlug,
}: {
  runId: string;
  orgSlug: string;
}) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);
  const [publishError, setPublishError] = useState<string | undefined>();

  const {
    data: run,
    isPending,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["run", runId],
    queryFn: async () => {
      const { data, error } = await api.GET("/runs/{runId}", {
        params: { path: { runId } },
      });
      if (error || !data) throw new Error("Could not read the run.");
      return data;
    },
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      return state === "queued" || state === "running" ? 1200 : false;
    },
  });

  const publish = useMutation({
    mutationFn: async () => {
      const { data, error, response } = await api.POST("/runs/{runId}/publish", {
        params: { path: { runId } },
      });
      if (error || !data) {
        throw new Error(
          response.status === 409
            ? "This run is no longer publishable. Reload to see where it got to."
            : (error?.message ?? "Publishing did not finish."),
        );
      }
      return data;
    },
    onSuccess: (published) => {
      // 8.6: on completion the page becomes the published state directly. No
      // success modal.
      queryClient.setQueryData(["run", runId], published);
      setConfirming(false);
      setPublishError(undefined);
    },
    onError: (e: Error) => {
      setConfirming(false);
      setPublishError(e.message);
    },
  });

  if (isPending) {
    return (
      <div className="flex flex-col gap-16" role="status">
        <span className="h-32 w-1/3 animate-pulse rounded-sm bg-sunken" />
        <span className="h-96 w-full animate-pulse rounded-lg bg-sunken" />
        <span className="sr-only">Loading the run</span>
      </div>
    );
  }

  if (isError || !run) {
    return (
      <div
        role="alert"
        className="flex flex-col items-start gap-12 rounded-md border border-danger bg-surface p-24"
      >
        <p className="type-body-m text-secondary">
          This run did not load. Nothing has been published and no strand has
          been created.
        </p>
        <Button variant="secondary" onClick={() => refetch()}>
          Try again
        </Button>
      </div>
    );
  }

  const working = run.state === "queued" || run.state === "running";
  const unmatchedHref = `/admin/o/${orgSlug}/programs/${run.programId}/unmatched`;

  return (
    <div className="flex flex-col gap-32">
      <header className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">
          Run of {dateTime.format(new Date(run.createdAt))}
        </h1>
        <p className="type-body-s text-muted">
          Started by {run.createdBy}
          {run.recipeVersion ? `, recipe v${run.recipeVersion}` : ""}.
          {run.publishedAt
            ? ` Published ${dateTime.format(new Date(run.publishedAt))}${run.publishedBy ? ` by ${run.publishedBy}` : ""}.`
            : ""}
        </p>
      </header>

      {working && <RunProgress progress={run.progress} />}

      {!working && run.fairnessSummary && (
        <FairnessSummary summary={run.fairnessSummary} />
      )}

      {!working && (
        <>
          <PairList pairs={run.pairs} published={run.state === "published"} />

          {run.unmatchedCount > 0 && (
            <section className="flex flex-wrap items-center justify-between gap-16 rounded-md border border-subtle bg-sunken p-16">
              <p className="type-body-m text-secondary">
                {run.unmatchedCount}{" "}
                {run.unmatchedCount === 1 ? "person has" : "people have"} no
                match in this run.
              </p>
              <Link href={unmatchedHref} className="type-body-m text-link underline">
                Open the unmatched queue
              </Link>
            </section>
          )}
        </>
      )}

      {publishError && (
        <p role="alert" className="type-body-m text-danger">
          {publishError}
        </p>
      )}

      {run.state === "drafted" && (
        <PublishBar
          run={run}
          busy={publish.isPending}
          onPublish={() => setConfirming(true)}
        />
      )}

      {run.state === "published" && (
        <p className="rounded-md border border-subtle bg-surface p-16 type-body-m text-secondary">
          Published. {run.publishedCount ?? run.pairs.length} strands are live and
          both sides have been told.
        </p>
      )}

      <ConfirmDialog
        open={confirming}
        title="Publish this run?"
        confirmLabel="Publish the run"
        busyLabel="Publishing"
        busy={publish.isPending}
        onCancel={() => setConfirming(false)}
        onConfirm={() => publish.mutate()}
        body={
          <div className="flex flex-col gap-12">
            <p>
              This creates {run.pairs.length}{" "}
              {run.pairs.length === 1 ? "strand" : "strands"} and emails{" "}
              {run.pairs.length * 2} people. It cannot be undone.
            </p>
            {run.unmatchedCount > 0 && (
              <p>
                {run.unmatchedCount}{" "}
                {run.unmatchedCount === 1 ? "person stays" : "people stay"}{" "}
                unmatched and will not hear anything.
              </p>
            )}
          </div>
        }
      />
    </div>
  );
}

/**
 * 8.6: determinate, because the wait is long and a spinner would say nothing.
 * The width is the only thing that moves and it is driven by the run's own
 * progress figure rather than by a timer.
 */
function RunProgress({ progress }: { progress: number }) {
  const percent = Math.round(progress * 100);

  return (
    <section className="flex flex-col gap-12 rounded-lg border border-subtle bg-surface p-24">
      <h2 className="type-heading-s text-primary">Matching is running</h2>
      <div className="flex items-center gap-12">
        <div
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
          aria-label="Matching progress"
          className="h-8 min-w-0 flex-1 overflow-hidden rounded-sm bg-sunken"
        >
          <div
            className="h-8 rounded-sm bg-accent transition-[inline-size] duration-base ease-out"
            style={{ inlineSize: `${percent}%` }}
          />
        </div>
        <span className="type-data-m text-primary">{percent}%</span>
      </div>
      <p className="type-body-s text-secondary">
        Nothing is sent while this runs. You will see the fairness summary
        before anyone is told anything.
      </p>
    </section>
  );
}

/** 5.12: mentee, mentor, score, priority band. */
function PairList({
  pairs,
  published,
}: {
  pairs: RunDetail["pairs"];
  published: boolean;
}) {
  if (pairs.length === 0) {
    return (
      <div className="rounded-lg border border-subtle bg-surface">
        <EmptyState
          markId="run-no-pairs"
          title="This run paired nobody."
          body="Every mentee is in the unmatched queue with a reason. That is usually mentor capacity, not a fault in the roster."
        />
      </div>
    );
  }

  return (
    <section className="flex flex-col gap-12">
      <h2 className="type-heading-m text-primary">
        {published ? "Published pairs" : "Draft pairs"}
      </h2>

      <div className="overflow-x-auto rounded-md border border-subtle bg-surface">
        <table className="w-full border-collapse">
          <caption className="sr-only">
            Every pair this run drafted, with its score and the mentee&apos;s
            priority band
          </caption>
          <thead>
            <tr className="h-48 bg-sunken">
              <th scope="col" className="px-16 text-left type-label text-secondary">
                Mentee
              </th>
              <th scope="col" className="px-16 text-left type-label text-secondary">
                Mentor
              </th>
              <th scope="col" className="px-16 text-left type-label text-secondary">
                Priority
              </th>
              <th scope="col" className="px-16 text-right type-label text-secondary">
                Score
              </th>
            </tr>
          </thead>
          <tbody>
            {pairs.map((pair) => (
              <tr key={pair.id} className="h-48 border-t border-subtle">
                <td className="px-16 type-body-s text-primary">
                  {pair.mentee.name}
                </td>
                <td className="px-16 type-body-s text-primary">
                  {pair.mentor.name}
                </td>
                <td className="px-16 type-body-s text-primary">
                  {capitalise(pair.priorityBand)}
                </td>
                <td className="px-16 text-right type-data-m text-primary">
                  {pair.score.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 5.12 also lists open, swap, reject, lock and re-run. openapi.yaml
          excludes the pair-level actions until the step that needs them, so
          they are absent rather than drawn and dead. */}
    </section>
  );
}

function PublishBar({
  run,
  busy,
  onPublish,
}: {
  run: RunDetail;
  busy: boolean;
  onPublish: () => void;
}) {
  return (
    <section className="flex flex-wrap items-center justify-between gap-16 border-t border-subtle pt-24">
      <p className="type-body-s text-secondary">
        Nothing has been sent yet. Publishing creates {run.pairs.length}{" "}
        {run.pairs.length === 1 ? "strand" : "strands"} and cannot be undone.
      </p>
      <Button
        size="lg"
        onClick={onPublish}
        loading={busy}
        loadingLabel="Publishing the run"
      >
        Publish
      </Button>
    </section>
  );
}

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
