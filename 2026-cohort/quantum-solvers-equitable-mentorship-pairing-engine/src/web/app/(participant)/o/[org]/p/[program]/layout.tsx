import { Forbidden } from "@/components/shell/forbidden";
import { ParticipantHeader } from "@/components/shell/participant-header";
import { ParticipantTabs } from "@/components/shell/participant-tabs";
import { requireParticipation } from "@/lib/auth/guard";

/**
 * Resolves the account, the programme, and the role held in it before anything
 * below renders. Pages under here may assume all three.
 */
export default async function ParticipantLayout({
  children,
  params,
}: LayoutProps<"/o/[org]/p/[program]">) {
  const { org, program } = await params;
  const result = await requireParticipation(org, program);

  if (!result.ok) {
    return (
      <Forbidden
        session={result.session}
        reason="You are not a member of this programme."
      />
    );
  }

  return (
    <div className="flex min-h-full flex-1 flex-col bg-page">
      <ParticipantHeader
        session={result.session}
        participation={result.participation}
      />
      <main className="mx-auto w-full max-w-participant flex-1 px-16 py-32">
        {children}
      </main>
      <ParticipantTabs participation={result.participation} />
    </div>
  );
}
