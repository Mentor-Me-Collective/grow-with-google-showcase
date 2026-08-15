"use client";

import { useState } from "react";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";

type State = "idle" | "sending" | "sent" | "failed";

/**
 * Architecture 3.3 calls this "resend verification email". The contract has one
 * mechanism for reaching an inbox — the magic link — and it is the same message
 * either way, so this sends that rather than inventing a second kind of mail.
 */
export function ResendLink({ email }: { email: string }) {
  const [state, setState] = useState<State>("idle");

  if (state === "sent") {
    return (
      <p role="status" className="type-body-s text-secondary">
        Sent again to {email}. It can take a minute to arrive.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex">
        <Button
          variant="secondary"
          loading={state === "sending"}
          loadingLabel="Sending the link"
          onClick={async () => {
            setState("sending");
            const { error } = await api.POST("/auth/magic-link", {
              body: { email },
            });
            setState(error ? "failed" : "sent");
          }}
        >
          Send the link again
        </Button>
      </div>
      {state === "failed" && (
        <p role="alert" className="type-caption text-danger">
          That did not send. Try again in a moment.
        </p>
      )}
    </div>
  );
}
