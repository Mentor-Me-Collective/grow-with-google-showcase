import Link from "next/link";
import { notFound } from "next/navigation";
import { serverApi } from "@/lib/api/server";
import { requireParticipation } from "@/lib/auth/guard";
import { Avatar } from "@/components/ui/avatar";

export const metadata = { title: "Participant" };

/**
 * Architecture 4.10, the "open a profile" the directory promises.
 *
 * 4.10 also specifies sending a match request. Requests are a model of their
 * own — 4.11, with pending, accepted, declined and expired, and a per-programme
 * cap — and none of it is in the contract. The action is absent rather than
 * drawn and dead.
 */
export default async function ParticipantProfilePage(
  props: PageProps<"/o/[org]/p/[program]/directory/[participationId]">,
) {
  const { org, program, participationId } = await props.params;
  const result = await requireParticipation(org, program);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const { data: profile } = await serverApi.GET(
    "/participations/{participationId}/profile",
    { params: { path: { participationId } } },
  );
  if (!profile) notFound();

  const base = `/o/${org}/p/${program}`;

  return (
    <div className="flex flex-col gap-32">
      <div className="flex flex-col gap-16">
        <Link href={`${base}/directory`} className="type-body-s text-link underline">
          Back to the directory
        </Link>

        <div className="flex items-center gap-16">
          <Avatar
            name={profile.name}
            participationId={profile.participationId}
            size={64}
            neutral={!profile.available}
          />
          <div className="flex flex-col gap-4">
            <h1 className="type-heading-l text-primary">{profile.name}</h1>
            {profile.headline && (
              <p className="type-body-m text-secondary">{profile.headline}</p>
            )}
            {profile.timezone && (
              <p className="type-body-s text-muted">{profile.timezone}</p>
            )}
          </div>
        </div>
      </div>

      <section className="flex flex-col gap-8 rounded-md border border-subtle bg-sunken p-16">
        <h2 className="type-label text-muted">Room to take someone on</h2>
        <p className="type-body-m text-primary">
          {profile.available
            ? profile.capacity !== null && profile.capacity !== undefined
              ? `Yes — mentoring ${profile.load ?? 0} of the ${profile.capacity} they agreed to.`
              : "Yes."
            : `No — already mentoring ${profile.load ?? 0}, which is everyone they agreed to take.`}
        </p>
      </section>

      {profile.skills.length > 0 && (
        <section className="flex flex-col gap-8">
          <h2 className="type-label text-muted">Can help with</h2>
          <p className="type-body-m text-primary">{profile.skills.join(", ")}</p>
        </section>
      )}

      {profile.sections.length > 0 ? (
        <div className="flex flex-col gap-32">
          {profile.sections.map((section) => (
            <section key={section.title} className="flex flex-col gap-16">
              <h2 className="type-heading-m text-primary">{section.title}</h2>
              <dl className="flex flex-col gap-16">
                {section.entries.map((entry) => (
                  <div key={entry.label} className="flex flex-col gap-4">
                    <dt className="type-label text-muted">{entry.label}</dt>
                    <dd className="type-body-m text-primary">{entry.value}</dd>
                  </div>
                ))}
              </dl>
            </section>
          ))}
        </div>
      ) : (
        <p className="type-body-m text-secondary">
          {profile.name.split(" ")[0]} has not filled in the rest of their
          profile yet.
        </p>
      )}
    </div>
  );
}
