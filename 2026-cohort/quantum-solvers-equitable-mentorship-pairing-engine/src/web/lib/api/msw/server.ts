import { setupServer } from "msw/node";
import { handlers } from "./handlers";

/** Node-side interception: Server Components, route handlers, the build. */
export const server = setupServer(...handlers);
