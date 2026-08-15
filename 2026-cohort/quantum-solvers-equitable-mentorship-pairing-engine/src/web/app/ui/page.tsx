import { notFound } from "next/navigation";
import { Gallery } from "./gallery";

export const metadata = { title: "ui/ primitives" };

/**
 * Dev-only. Every state of every primitive on one page, so a change that
 * breaks the disabled or loading or error rendering is visible immediately
 * rather than on the screen that happens to use it.
 *
 * `notFound()` in production keeps it out of the shipped app.
 */
export default function UiPage() {
  if (process.env.NODE_ENV === "production") notFound();
  return <Gallery />;
}
