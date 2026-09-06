"use client";

import { useState } from "react";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/input";

type State =
  | { kind: "idle" }
  | { kind: "sending" }
  | { kind: "sent" }
  | { kind: "failed"; message: string };

/**
 * Architecture 3.4 also asks for a password path and a forgot-password link.
 * Neither is in the contract — `openapi.yaml` describes Auth as "Magic-link
 * sign in" and carries no password operation — so this screen is the link path
 * only. Adding the second path means adding endpoints first.
 */
export function SignInForm() {
  const [state, setState] = useState<State>({ kind: "idle" });
  const [email, setEmail] = useState("");

  /**
   * The response is 202 whether or not the address has an account, so this
   * cannot say "check your inbox" for a known address and something else for
   * an unknown one without rebuilding the enumeration oracle the endpoint was
   * written to avoid. It says what was done, not what will arrive.
   */
  if (state.kind === "sent") {
    return (
      <div className="flex flex-col gap-16">
        <p
          role="status"
          className="rounded-md border border-subtle bg-surface p-16 type-body-m text-secondary"
        >
          If {email} has an account, a sign-in link is on its way. It works once
          and expires in fifteen minutes.
        </p>
        <div className="flex">
          <Button
            variant="ghost"
            onClick={() => setState({ kind: "idle" })}
          >
            Use a different address
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form
      noValidate
      className="flex flex-col gap-24"
      onSubmit={async (e) => {
        e.preventDefault();
        if (!email.includes("@")) {
          setState({
            kind: "failed",
            message: "Enter the email address you applied with.",
          });
          return;
        }

        setState({ kind: "sending" });
        const { error, response } = await api.POST("/auth/magic-link", {
          body: { email: email.trim() },
        });

        if (!error) {
          setState({ kind: "sent" });
          return;
        }

        setState({
          kind: "failed",
          // The server's 429 names the actual wait, computed from the window
          // that is still open. A fixed "wait a minute" here would contradict
          // it, and be wrong for fifty-seven of those minutes.
          message:
            error.message ??
            (response.status === 429
              ? "That is a few too many links in a row. Try again shortly."
              : "That did not send. Try again."),
        });
      }}
    >
      <Field
        label="Email address"
        type="email"
        autoComplete="email"
        autoFocus
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        helper="The address you applied with."
        error={state.kind === "failed" ? state.message : undefined}
        mark="none"
      />

      <div className="flex">
        <Button
          type="submit"
          size="lg"
          loading={state.kind === "sending"}
          loadingLabel="Sending your link"
        >
          Email me a sign-in link
        </Button>
      </div>
    </form>
  );
}
