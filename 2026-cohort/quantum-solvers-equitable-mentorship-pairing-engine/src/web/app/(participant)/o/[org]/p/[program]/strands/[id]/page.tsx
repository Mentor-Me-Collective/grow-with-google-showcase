import Link from "next/link";
import { notFound } from "next/navigation";
import { serverApi } from "@/lib/api/server";
import { requireParticipation } from "@/lib/auth/guard";
import { Conversation } from "./conversation";
import { PartnerCard } from "./partner-card";
import { PartnerHeader } from "./partner-header";

export const metadata = { title: "Strand" };

/**
 * Architecture 4.7 and design direction 9. Two columns on desktop at 380 and
 * 520, the conversation being the wider one; on mobile the conversation is the
 * page and the partner card collapses into a header that expands on tap.
 *
 * Architecture 4.7 also specifies a third region — shared goals, milestone
 * checklist, session history, suggested agenda, shared resources — and nine
 * actions. Section 9 and the design file both draw two columns and two actions,
 * so the working state is not here. It needs endpoints that do not exist yet.
 */
export default async function StrandPage({
  params,
}: {
  params: Promise<{ org: string; program: string; id: string }>;
}) {
  const { org, program, id } = await params;
  const result = await requireParticipation(org, program);
  if (!result.ok) return null;

  const [{ data: strand }, { data: page }] = await Promise.all([
    serverApi.GET("/strands/{strandId}", { params: { path: { strandId: id } } }),
    serverApi.GET("/strands/{strandId}/messages", {
      params: { path: { strandId: id } },
    }),
  ]);

  if (!strand) notFound();

  const me = result.participation.id;
  const others = strand.members.filter((m) => m.participationId !== me);
  const isGroup = others.length > 1;
  const partner = others[0];
  const messages = page?.items ?? [];
  const back = `/o/${org}/p/${program}`;

  return (
    <div className="flex flex-col gap-24">
      <Link href={back} className="type-body-s text-link underline md:hidden">
        Back
      </Link>

      {/* Below md the partner card is a tappable header above the thread. */}
      <div className="md:hidden">
        <PartnerHeader strand={strand} others={others} />
      </div>

      <div className="flex flex-col gap-24 md:flex-row md:items-start">
        <aside className="hidden w-partner shrink-0 md:block">
          <PartnerCard strand={strand} others={others} />
        </aside>

        <div className="min-w-0 flex-1">
          <Conversation
            strandId={strand.id}
            title={
              isGroup
                ? `Your strand with ${others.length} others`
                : `Your strand with ${firstName(partner?.name)}`
            }
            privacyLine={
              isGroup
                ? `Only the ${others.length + 1} of you can read this`
                : "Only the two of you can read this"
            }
            writeTo={isGroup ? "the strand" : firstName(partner?.name)}
            me={me}
            initialMessages={messages}
            partner={partner}
            createdAt={strand.createdAt}
            ended={strand.state === "ended"}
          />
        </div>
      </div>
    </div>
  );
}

const firstName = (name: string | undefined) => name?.split(" ")[0] ?? "them";

