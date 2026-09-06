import Link from "next/link";
import { serverApi } from "@/lib/api/server";
import { requireParticipation } from "@/lib/auth/guard";
import { ProfileForm } from "./profile-form";

export const metadata = { title: "Edit profile" };

export default async function ProfileEditPage(
  props: PageProps<"/o/[org]/p/[program]/me/edit">,
) {
  const { org, program } = await props.params;
  const result = await requireParticipation(org, program);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const base = `/o/${org}/p/${program}`;
  const { data: profile, error } = await serverApi.GET(
    "/programs/{programId}/me",
    { params: { path: { programId: result.participation.programId } } },
  );

  return (
    <div className="flex flex-col gap-32">
      <div className="flex flex-col gap-8">
        <Link href={`${base}/me`} className="type-body-s text-link underline">
          Back to my profile
        </Link>
        <h1 className="type-heading-l text-primary">Edit your profile</h1>
        <p className="type-body-m text-secondary">
          The same questions you answered when you applied. Each section saves on
          its own, so you can do one and come back.
        </p>
      </div>

      {error || !profile ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          Your answers did not load, so nothing is shown here rather than an
          empty form that might overwrite them. Reload to try again.
        </div>
      ) : (
        <ProfileForm
          profile={profile}
          programId={result.participation.programId}
          backHref={`${base}/me`}
        />
      )}
    </div>
  );
}
