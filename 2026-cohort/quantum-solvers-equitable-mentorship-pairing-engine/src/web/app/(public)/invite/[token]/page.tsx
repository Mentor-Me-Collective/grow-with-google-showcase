import Link from "next/link";
import { serverApi } from "@/lib/api/server";
import { PublicMain } from "@/components/shell/public-shell";
import { buttonClasses } from "@/components/ui/button";
import { InviteActions, RequestNewInvite } from "./invite-actions";

export const metadata = { title: "Invitation" };

const longDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(new Date(iso));

/**
 * Architecture 3.7. Somebody arriving here was added by a coordinator rather
 * than applying, so the page has to answer who is asking and why them, before
 * it asks for anything.
 */
export default async function InvitePage(
  props: PageProps<"/invite/[token]">,
) {
  const { token } = await props.params;
  const { data: invite } = await serverApi.GET("/invites/{token}", {
    params: { path: { token } },
  });

  if (!invite) {
    return (
      <PublicMain className="flex flex-col gap-24">
        <h1 className="type-heading-l text-primary">
          We cannot find that invitation.
        </h1>
        <p className="type-body-l text-secondary">
          The link may be incomplete. Copying the whole line from the email
          usually fixes it.
        </p>
        <div className="flex">
          <Link href="/signin" className={buttonClasses({ size: "lg" })}>
            Sign in
          </Link>
        </div>
      </PublicMain>
    );
  }

  // Expired is not an error page. Architecture 6 asks for a way forward, and
  // the way forward is the person who sent it.
  if (invite.state === "expired") {
    return (
      <PublicMain className="flex flex-col gap-24">
        <h1 className="type-heading-l text-primary">This invitation has lapsed.</h1>
        <p className="type-body-l text-secondary">
          {invite.invitedByName} invited you to {invite.programName} at{" "}
          {invite.organisationName}, and the link ran out
          {invite.expiresAt ? ` on ${longDate(invite.expiresAt)}` : ""}. That is
          all that has happened — the place was not withdrawn.
        </p>
        <RequestNewInvite token={invite.token} />
      </PublicMain>
    );
  }

  if (invite.state !== "pending") {
    return (
      <PublicMain className="flex flex-col gap-24">
        <h1 className="type-heading-l text-primary">
          {invite.state === "accepted"
            ? "You have already accepted this."
            : "You have already declined this."}
        </h1>
        <p className="type-body-l text-secondary">
          {invite.state === "accepted"
            ? "Signing in will take you to the programme."
            : `Nothing more is needed. If you have changed your mind, ${invite.invitedByName} can send a new invitation.`}
        </p>
        <div className="flex">
          <Link href="/signin" className={buttonClasses({ size: "lg" })}>
            Sign in
          </Link>
        </div>
      </PublicMain>
    );
  }

  return (
    <PublicMain className="flex flex-col gap-32">
      <div className="flex flex-col gap-16">
        <h1 className="type-heading-l text-primary">
          {invite.invitedByName} has invited you to {invite.programName}.
        </h1>
        <p className="type-body-l text-secondary">
          {invite.organisationName} runs this programme, and you have been asked
          to join as a {invite.role}. The invitation was sent to {invite.email}.
        </p>
        {invite.expiresAt && (
          <p className="type-body-s text-muted">
            This link works until {longDate(invite.expiresAt)}.
          </p>
        )}
      </div>

      {invite.message && (
        <blockquote className="border-l-2 border-default pl-16 type-body-l text-secondary">
          {invite.message}
          <footer className="mt-8 type-body-s text-muted">
            — {invite.invitedByName}
          </footer>
        </blockquote>
      )}

      <InviteActions invite={invite} />
    </PublicMain>
  );
}
