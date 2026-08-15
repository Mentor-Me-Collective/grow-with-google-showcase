import { cookies } from "next/headers";
import createClient from "openapi-fetch";
import { baseUrl } from "./client";
import type { paths } from "./types";

/**
 * Server-side client. `credentials: "include"` means nothing outside a browser,
 * so the session cookie has to be forwarded by hand on every request.
 *
 * Importing `next/headers` is what keeps this module off the client: it fails
 * the build if it ever reaches a client bundle.
 */
export const serverApi = createClient<paths>({
  baseUrl,
  // Same reason as the browser client: openapi-fetch would otherwise capture
  // globalThis.fetch at construction, and whether that happens before or after
  // instrumentation.ts installs MSW's is module-ordering luck.
  fetch: (request) => globalThis.fetch(request),
});

serverApi.use({
  async onRequest({ request }) {
    request.headers.set("cookie", (await cookies()).toString());
    return request;
  },
});
