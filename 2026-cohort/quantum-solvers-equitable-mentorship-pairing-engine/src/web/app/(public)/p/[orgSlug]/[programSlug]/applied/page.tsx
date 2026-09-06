import Link from "next/link";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { PublicHeader, PublicMain } from "@/components/shell/public-shell";
import { buttonClasses } from "@/components/ui/button";
import { ResendLink } from "./resend-link";

export const metadata = { title: "Application received" };

const longDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(new Date(iso));

/**
 * Architecture 3.3, the screen that prevents the "did it go through" email.
 *
 * A route rather than a state inside the wizard, because the confirmation is
 * the one page someone comes back to. Keyed by application id so the link in
 * their inbox lands somewhere real.
 */
export default async function AppliedPage(
  props: PageProps<"/p/[orgSlug]/[programSlug]/applied">,
) {
  const { orgSlug, programSlug } = await props.params;
  const { id } = await props.searchParams;
  const back = `/p/${orgSlug}/${programSlug}`;

  const applicationId = typeof id === "string" ? id : undefined;
  const { data: application } = applicationId
    ? await serverApi.GET("/applications/{applicationId}", {
        params: { path: { applicationId } },
      })
    : { data: undefined };

  // A confirmation that cannot find the application must not imply the
  // application is gone. It is far likelier that the link lost its id.
  if (!application) {
    return (
      <>
        <PublicHeader />
        <PublicMain className="flex flex-col gap-24">
          <h1 className="type-heading-l text-primary">
            We cannot find that application.
          </h1>
          <p className="type-body-l text-secondary">
            The link may be incomplete. If you submitted an application it is
            still with the programme — signing in will show you where it stands.
          </p>
          <div className="flex flex-wrap gap-16">
            <Link href="/signin" className={buttonClasses({ size: "lg" })}>
              Sign in
            </Link>
            <Link
              href={back}
              className={buttonClasses({ size: "lg", variant: "secondary" })}
            >
              Back to the programme
            </Link>
          </div>
        </PublicMain>
      </>
    );
  }

  const programName = application.programName ?? "The programme";

  return (
    <>
      <PublicHeader />
      <PublicMain className="flex flex-col gap-32">
        <div className="flex flex-col gap-16">
          <h1 className="type-heading-l text-primary">Your application is in.</h1>
          <p className="type-body-l text-secondary">
            {programName} has it. We sent a copy to {application.email}.
          </p>
        </div>

        <section className="flex flex-col gap-16 rounded-lg border border-subtle bg-surface p-24">
          <h2 className="type-label text-muted">What happens next</h2>
          <ol className="flex flex-col gap-12 type-body-m text-secondary">
            <li>
              The coordinator reads every application. Yours is marked{" "}
              {readableStatus(application.status)}.
            </li>
            <li>
              {application.matchingOpensAt
                ? `Matching runs on ${longDate(application.matchingOpensAt)}.`
                : "Matching runs once the coordinator closes applications."}
            </li>
            <li>
              You hear either way, by email, at {application.email}.
            </li>
          </ol>
        </section>

        <div className="flex flex-col gap-16 border-t border-subtle pt-24">
          <p className="type-body-s text-muted">
            Nothing arrived? Check the spam folder first — it is usually there.
          </p>
          <ResendLink email={application.email} />
        </div>

        <div className="flex">
          <Link href={back} className="type-body-m text-link underline">
            Back to the programme
          </Link>
        </div>
      </PublicMain>
    </>
  );
}

/** Exhaustive over the enum, so a new status fails the build rather than
 *  falling through to a raw wire value on a page an applicant reads. */
function readableStatus(status: Schemas["ApplicationStatus"]) {
  switch (status) {
    case "submitted":
      return "submitted and waiting to be read";
    case "under_review":
      return "under review";
    case "approved":
      return "approved";
    case "waitlisted":
      return "waitlisted";
    case "rejected":
      return "closed";
  }
}
