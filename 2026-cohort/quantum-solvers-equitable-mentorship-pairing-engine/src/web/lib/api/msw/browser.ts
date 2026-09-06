import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

/** Browser-side interception: client mutations and polling. */
export const worker = setupWorker(...handlers);
