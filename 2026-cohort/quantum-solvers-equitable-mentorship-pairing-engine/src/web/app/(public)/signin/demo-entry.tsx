"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";

type Side = "coordinator" | "participant";

/**
 * A way into a deployed copy for somebody who cannot receive our email.
 *
 * The seeded people have example.org addresses, so the magic-link path is
 * closed to a reviewer, and a sign-in form they cannot pass is the same as no
 * deployment at all. Rendered only when the API is running in demo mode, and
 * the endpoint behind it 404s otherwise — so this cannot become a way into a
 * real cohort's data.
 */
export function DemoEntry() {
  const router = useRouter();
  const [busy, setBusy] = useState<Side | null>(null);
  const [error, setError] = useState<string | undefined>();

  const enter = async (side: Side) => {
    setBusy(side);
    const { data, error: failed } = await api.POST("/auth/demo", {
      body: { as: side },
    });

    if (failed || !data) {
      setBusy(null);
      setError("The demo is not available on this deployment.");
      return;
    }

    const first = data.participations[0];
    router.refresh();
    router.replace(
      side === "coordinator" && first
        ? `/admin/o/${first.orgSlug}`
        : first
          ? `/o/${first.orgSlug}/p/${first.programSlug}`
          : "/programs",
    );
  };

  return (
    <section className="flex flex-col gap-12 border-t border-subtle pt-24">
      <div className="flex flex-col gap-4">
        <h2 className="type-heading-s text-primary">Just looking?</h2>
        <p className="type-body-s text-secondary">
          Go straight in as somebody from the sample programme. Nothing you do
          here reaches a real person.
        </p>
      </div>

      <div className="flex flex-wrap gap-12">
        <Button
          variant="secondary"
          loading={busy === "coordinator"}
          loadingLabel="Opening the coordinator view"
          onClick={() => enter("coordinator")}
        >
          Explore as a coordinator
        </Button>
        <Button
          variant="secondary"
          loading={busy === "participant"}
          loadingLabel="Opening the participant view"
          onClick={() => enter("participant")}
        >
          Explore as a participant
        </Button>
      </div>

      {error && (
        <p role="alert" className="type-body-s text-danger">
          {error}
        </p>
      )}
    </section>
  );
}
