import Link from "next/link";
import type { Session } from "@/lib/auth/guard";

/**
 * Architecture 6: a 403 names what happened and offers exactly one way
 * forward. Here that is the list of programmes the person is actually in.
 */
export function Forbidden({
  session,
  reason,
}: {
  session: Session;
  reason: string;
}) {
  return (
    <main className="mx-auto flex max-w-public flex-col gap-24 px-16 py-64">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">You cannot open this page</h1>
        <p className="type-body-m text-secondary">{reason}</p>
      </div>

      {session.participations.length > 0 ? (
        <div className="flex flex-col gap-8">
          <h2 className="type-label text-muted">Your programmes</h2>
          <ul className="flex flex-col gap-8">
            {session.participations.map((participation) => (
              <li key={participation.id}>
                <Link
                  href={`/o/${participation.orgSlug}/p/${participation.programSlug}`}
                  className="flex min-h-48 flex-col justify-center rounded-md border border-subtle px-16 py-12 transition-colors duration-instant hover:border-default"
                >
                  <span className="type-body-m text-primary">
                    {participation.programName}
                  </span>
                  <span className="type-caption text-muted">
                    {participation.organisationName} · {participation.role}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="type-body-m text-secondary">
          You are not in any programme yet.
        </p>
      )}
    </main>
  );
}
