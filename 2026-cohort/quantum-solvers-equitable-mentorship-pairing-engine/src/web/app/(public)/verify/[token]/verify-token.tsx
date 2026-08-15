"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import type { Schemas } from "@/lib/api/client";
import { buttonClasses } from "@/components/ui/button";

type Result =
  | { kind: "ok"; session: Schemas["Session"] }
  | { kind: "spent" }
  | { kind: "failed"; message: string };

/**
 * A magic-link token is single use, and React invokes effects twice in
 * development. Without this the second invocation spends a token the first one
 * already consumed and a good link renders as expired — the one failure this
 * screen exists to handle gracefully, manufactured by our own strict mode.
 *
 * Keyed by token rather than a bare flag so two different links in one session
 * do not share an answer. Same shape as startWorkerOnce.
 */
const inFlight = new Map<string, Promise<Result>>();

function verifyOnce(token: string): Promise<Result> {
  const existing = inFlight.get(token);
  if (existing) return existing;

  const promise = api
    .POST("/auth/verify", { body: { token } })
    .then(({ data, error, response }): Result => {
      if (data) return { kind: "ok", session: data };
      if (response.status === 410) return { kind: "spent" };
      return {
        kind: "failed",
        message: error?.message ?? "That link could not be checked.",
      };
    })
    .catch((): Result => ({
      kind: "failed",
      message: "That link could not be checked.",
    }));

  inFlight.set(token, promise);
  return promise;
}

/**
 * Architecture 3.5: consume the token, open the session, land the person where
 * they were going. Expired and spent tokens get a resend action rather than an
 * error page, because a dead link is the most likely way in and a wall here
 * ends the journey.
 */
export function VerifyToken({ token }: { token: string }) {
  const router = useRouter();
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    let live = true;
    void verifyOnce(token).then((r) => {
      if (!live) return;
      setResult(r);
      if (r.kind !== "ok") return;

      // refresh() first: every page below here is a Server Component reading
      // the session cookie, and replace() alone would navigate to a tree
      // rendered before the session existed.
      router.refresh();
      router.replace(destination(r.session));
    });
    return () => {
      live = false;
    };
  }, [token, router]);

  if (result === null || result.kind === "ok") {
    return (
      <p role="status" className="type-body-l text-secondary">
        Signing you in…
      </p>
    );
  }

  if (result.kind === "spent") {
    return (
      <div className="flex flex-col gap-24">
        <h1 className="type-heading-l text-primary">That link is spent.</h1>
        <p className="type-body-l text-secondary">
          Sign-in links work once and expire after fifteen minutes. Nothing is
          wrong with your account and nothing has been lost.
        </p>
        <div className="flex">
          <Link href="/signin" className={buttonClasses({ size: "lg" })}>
            Send me a new link
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-24">
      <h1 className="type-heading-l text-primary">We could not check that link.</h1>
      <p className="type-body-l text-secondary">{result.message}</p>
      <div className="flex flex-wrap gap-16">
        <button
          type="button"
          className={buttonClasses({ size: "lg" })}
          onClick={() => {
            inFlight.delete(token);
            setResult(null);
            void verifyOnce(token).then(setResult);
          }}
        >
          Try again
        </button>
        <Link
          href="/signin"
          className={buttonClasses({ size: "lg", variant: "secondary" })}
        >
          Send me a new link
        </Link>
      </div>
    </div>
  );
}

/**
 * One programme means there is only one place to be, so go there. More than one
 * is a choice, and the account scope is where that choice lives; so is none,
 * where /programs is the screen that explains why it is empty.
 */
function destination(session: Schemas["Session"]) {
  const [only, ...rest] = session.participations;
  return only && rest.length === 0
    ? `/o/${only.orgSlug}/p/${only.programSlug}`
    : "/programs";
}
