import { cookies } from "next/headers";
import createClient from "openapi-fetch";
import { baseUrl } from "./client";
import type { paths } from "./types";

/**
 * Where *this process* reaches the API, which is not always where the browser
 * reaches it. Running under Docker or on a platform with private networking,
 * the browser uses a published address while the server next to it should use
 * the internal one — and `NEXT_PUBLIC_API_URL` cannot be both. Left unset the
 * two are identical, which is the case everywhere else.
 *
 * Deliberately not `NEXT_PUBLIC_`: that prefix is inlined into the client
 * bundle at build time, and this address is a runtime detail of the server.
 */
const internalBaseUrl = process.env.API_URL_INTERNAL ?? baseUrl;

/**
 * Server-side client. `credentials: "include"` means nothing outside a browser,
 * so the session cookie has to be forwarded by hand on every request.
 *
 * Importing `next/headers` is what keeps this module off the client: it fails
 * the build if it ever reaches a client bundle.
 */
export const serverApi = createClient<paths>({
  baseUrl: internalBaseUrl,
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
