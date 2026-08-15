"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { decideApplication } from "../actions";

type Decision = Schemas["DecisionKind"];

const VERB: Record<Decision, string> = {
  approve: "Approve",
  waitlist: "Waitlist",
  reject: "Reject",
};

export function DecisionBar({
  applicationId,
  name,
  role,
  decided,
}: {
  applicationId: string;
  name: string;
  role: Schemas["Role"];
  decided: boolean;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [confirming, setConfirming] = useState<Decision | null>(null);
  const [error, setError] = useState<string | undefined>();

  if (decided) return null;

  const run = (decision: Decision) =>
    startTransition(async () => {
      const result = await decideApplication({ applicationId, decision });
      setConfirming(null);
      if (result.ok) {
        setError(undefined);
        router.refresh();
      } else {
        setError(result.message);
      }
    });

  return (
    <section className="flex flex-col gap-12 border-t border-subtle pt-24">
      {error && (
        <p role="alert" className="type-body-s text-danger">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-12">
        <Button size="lg" onClick={() => setConfirming("approve")} disabled={pending}>
          Approve
        </Button>
        <Button
          size="lg"
          variant="secondary"
          onClick={() => setConfirming("waitlist")}
          disabled={pending}
        >
          Waitlist
        </Button>
        <Button
          size="lg"
          variant="secondary"
          onClick={() => setConfirming("reject")}
          disabled={pending}
        >
          Reject
        </Button>
      </div>

      <ConfirmDialog
        open={confirming !== null}
        title={confirming ? `${VERB[confirming]} ${name}?` : ""}
        confirmLabel={confirming ? VERB[confirming] : ""}
        busy={pending}
        busyLabel="Saving"
        confirmVariant={confirming === "reject" ? "danger" : "primary"}
        onCancel={() => setConfirming(null)}
        onConfirm={() => confirming && run(confirming)}
        body={
          <p>
            {confirming === "approve"
              ? `${name} joins the roster as a ${role} and can be matched in the next run.`
              : confirming === "waitlist"
                ? `${name} moves to the waitlist and stays out of matching until you approve them.`
                : `${name}'s application is closed. This cannot be undone.`}
          </p>
        }
      />
    </section>
  );
}
