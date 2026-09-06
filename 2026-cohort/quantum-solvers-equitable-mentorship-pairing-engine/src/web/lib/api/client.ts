import createClient from "openapi-fetch";
import { apiReady } from "./ready";
import type { components, paths } from "./types";

export const baseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/v1";

export const api = createClient<paths>({
  baseUrl,
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  // Resolved per call rather than captured at construction, so a fetch
  // installed later — MSW does exactly this — is still used. Awaiting
  // apiReady holds browser requests until the worker is listening.
  fetch: async (request) => {
    await apiReady;
    return globalThis.fetch(request);
  },
});

export type Schemas = components["schemas"];
export type Problem = Schemas["Problem"];
