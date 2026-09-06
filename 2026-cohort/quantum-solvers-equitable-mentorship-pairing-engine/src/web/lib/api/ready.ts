import { mockingEnabled } from "./msw/enabled";

let resolveReady: (() => void) | undefined;

/**
 * Browser fetches must wait for the service worker; Server Components must not,
 * because instrumentation.ts starts Node interception before a request is
 * served. Resolved already in every case except a mocked browser.
 */
export const apiReady: Promise<void> =
  mockingEnabled && typeof window !== "undefined"
    ? new Promise<void>((resolve) => {
        resolveReady = resolve;
      })
    : Promise.resolve();

export function markApiReady() {
  resolveReady?.();
}
