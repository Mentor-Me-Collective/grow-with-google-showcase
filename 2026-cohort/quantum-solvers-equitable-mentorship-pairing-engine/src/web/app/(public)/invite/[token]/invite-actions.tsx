"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, type Schemas } from "@/lib/api/client";
import { Button, buttonClasses } from "@/components/ui/button";
import { Field } from "@/components/ui/input";

type State =
  | { kind: "idle" }
  | { kind: "working" }
  | { kind: "declined" }
  | { kind: "failed"; message: string };

/**
 * Accepting opens a session, so somebody arriving from an email lands inside
 * the programme rather than on a sign-in form holding an invitation they have
 * already accepted.
 */
export function InviteActions({ invite }: { invite: Schemas["Invite"] }) {
  const router = useRouter();
  const [state, setState] = useState<State>({ kind: "idle" });
  const [name, setName] = useState("");

  if (state.kind === "declined") {
    return (
      <div className="flex flex-col gap-16">
        <p role="status" className="type-body-l text-secondary">
          You have declined. {invite.invitedByName} will see that you are not
          joining, and nobody will write to you about it again.
        </p>
      </div>
    );
  }

  const respond = async (accept: boolean) => {
    if (accept && !invite.hasAccount && name.trim().length < 2) {
      setState({ kind: "failed", message: "Tell us what to call you." });
      return;
    }

    setState({ kind: "working" });
    const { data, error, response } = await api.POST("/invites/{token}", {
      params: { path: { token: invite.token } },
      body: { accept, name: accept && !invite.hasAccount ? name.trim() : null },
    });

    if (!accept && !error) {
      setState({ kind: "declined" });
      return;
    }

    if (error || !data) {
      setState({
        kind: "failed",
        message:
          response.status === 410
            ? "That invitation has expired since this page loaded."
            : (error?.message ?? "That did not go through."),
      });
      return;
    }

    // refresh() first: everything below is server-rendered from the session
    // this call just created.
    router.refresh();
    router.replace(`/o/${data.orgSlug}/p/${data.programSlug}`);
  };

  return (
    <div className="flex flex-col gap-24">
      {invite.hasAccount ? (
        <p className="rounded-md border border-subtle bg-sunken p-16 type-body-m text-secondary">
          {invite.email} already has a Braid account. Accepting adds this
          programme to it — you will not end up with a second one.
        </p>
      ) : (
        <Field
          label="What should we call you?"
          value={name}
          mark="none"
          autoComplete="name"
          onChange={(e) => setName(e.target.value)}
          helper="The name everyone in the programme will see."
          error={state.kind === "failed" ? state.message : undefined}
        />
      )}

      {invite.hasAccount && state.kind === "failed" && (
        <p role="alert" className="type-body-m text-danger">
          {state.message}
        </p>
      )}

      <div className="flex flex-wrap gap-16">
        <Button
          size="lg"
          loading={state.kind === "working"}
          loadingLabel="Setting you up"
          onClick={() => respond(true)}
        >
          {invite.hasAccount ? "Accept and join" : "Accept and create my account"}
        </Button>
        <Button
          size="lg"
          variant="secondary"
          disabled={state.kind === "working"}
          onClick={() => respond(false)}
        >
          Decline
        </Button>
      </div>

      <p className="type-body-s text-muted">
        Declining is not rude and nobody is told why.{" "}
        <Link href="/signin" className="text-link underline">
          Already have an account?
        </Link>
      </p>
    </div>
  );
}

/** What an expired invitation offers instead of a dead end. */
export function RequestNewInvite({ token }: { token: string }) {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "failed">(
    "idle",
  );

  if (state === "sent") {
    return (
      <p role="status" className="type-body-m text-secondary">
        Asked. Whoever invited you will get a note that your link lapsed, and
        can send a fresh one.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap gap-16">
        <Button
          size="lg"
          loading={state === "sending"}
          loadingLabel="Asking"
          onClick={async () => {
            setState("sending");
            const { error } = await api.POST("/invites/{token}/reissue", {
              params: { path: { token } },
            });
            setState(error ? "failed" : "sent");
          }}
        >
          Ask for a new invitation
        </Button>
        <Link
          href="/signin"
          className={buttonClasses({ size: "lg", variant: "secondary" })}
        >
          Sign in instead
        </Link>
      </div>
      {state === "failed" && (
        <p role="alert" className="type-body-s text-danger">
          That did not send. Try again in a moment.
        </p>
      )}
    </div>
  );
}
