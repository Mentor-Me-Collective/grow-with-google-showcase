/**
 * Strict Mode invokes effects twice in development, and calling
 * `worker.start()` a second time throws. Memoising the promise makes startup
 * idempotent and gives every caller the same readiness signal.
 */
let startPromise: Promise<void> | undefined;

export function startWorkerOnce(): Promise<void> {
  startPromise ??= import("./browser")
    .then(({ worker }) => worker.start({ onUnhandledRequest: "bypass" }))
    .then(() => undefined);
  return startPromise;
}
