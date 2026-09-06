"use client";

import { useState } from "react";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/input";

type State =
  | { kind: "idle" }
  | { kind: "sending" }
  | { kind: "done" }
  | { kind: "failed"; message: string };

/**
 * What a closed, full or not-yet-open programme offers instead of a dead end.
 *
 * The confirmation deliberately does not say "we will email you soon", because
 * the honest version is that the coordinator opens the next round when she
 * opens it and nobody here knows the date.
 */
export function WaitlistForm({
  orgSlug,
  programSlug,
}: {
  orgSlug: string;
  programSlug: string;
}) {
  const [state, setState] = useState<State>({ kind: "idle" });
  const [email, setEmail] = useState("");

  if (state.kind === "done") {
    return (
      <p
        role="status"
        className="rounded-md border border-subtle bg-surface p-16 type-body-m text-secondary"
      >
        We have your address. You will hear from {orgSlug.replace(/-/g, " ")} the
        day the next round opens, and not before.
      </p>
    );
  }

  return (
    <form
      noValidate
      className="flex flex-col gap-16 md:flex-row md:items-start md:gap-16"
      onSubmit={async (e) => {
        e.preventDefault();
        if (!email.includes("@")) {
          setState({
            kind: "failed",
            message: "Enter an email address we can reach you at.",
          });
          return;
        }
        setState({ kind: "sending" });
        const { error } = await api.POST(
          "/orgs/{orgSlug}/programs/{programSlug}/waitlist",
          {
            params: { path: { orgSlug, programSlug } },
            body: { email },
          },
        );
        setState(
          error
            ? { kind: "failed", message: "That did not send. Try again." }
            : { kind: "done" },
        );
      }}
    >
      <div className="md:w-participant md:max-w-full">
        <Field
          label="Email address"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          helper="Used once, for this one message."
          error={state.kind === "failed" ? state.message : undefined}
          mark="none"
        />
      </div>

      <Button
        type="submit"
        size="lg"
        variant="secondary"
        loading={state.kind === "sending"}
        loadingLabel="Adding you"
        className="md:mt-24"
      >
        Tell me when it opens
      </Button>
    </form>
  );
}
