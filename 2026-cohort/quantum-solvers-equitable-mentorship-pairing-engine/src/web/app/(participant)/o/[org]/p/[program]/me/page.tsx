import Link from "next/link";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireParticipation } from "@/lib/auth/guard";
import { Avatar } from "@/components/ui/avatar";
import { buttonClasses } from "@/components/ui/button";

export const metadata = { title: "My profile" };

/**
 * Architecture 4.2: what other participants see, kept separate from the edit
 * form so somebody can check their own presentation.
 *
 * A profile is the application answers read back. There is no second shape for
 * it — inventing one would mean a coordinator's question could be asked and
 * then never seen again.
 */
export default async function ProfilePage(
  props: PageProps<"/o/[org]/p/[program]/me">,
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

  if (error || !profile) {
    return (
      <div className="flex flex-col gap-16">
        <h1 className="type-heading-l text-primary">My profile</h1>
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          Your profile did not load. Nothing has been lost. Reload to try again.
        </div>
      </div>
    );
  }

  const percent = Math.round(profile.completeness * 100);
  const thin = profile.thinFieldIds.length;

  return (
    <div className="flex flex-col gap-32">
      <div className="flex flex-wrap items-start justify-between gap-16">
        <div className="flex items-center gap-16">
          <Avatar
            name={profile.name}
            participationId={profile.participationId}
            size={64}
          />
          <div className="flex flex-col gap-4">
            <h1 className="type-heading-l text-primary">{profile.name}</h1>
            <p className="type-body-m text-secondary">
              {profile.headline ?? capitalise(profile.role)}
            </p>
            {profile.timezone && (
              <p className="type-body-s text-muted">{profile.timezone}</p>
            )}
          </div>
        </div>

        <Link href={`${base}/me/edit`} className={buttonClasses()}>
          Edit profile
        </Link>
      </div>

      {/* Completeness is a fact about matching, not a score out of ten, so it
          says what the missing answers cost rather than just how many. */}
      <section className="flex flex-col gap-8 rounded-lg border border-subtle bg-surface p-24">
        <h2 className="type-label text-muted">How complete this is</h2>
        <div className="flex items-center gap-12">
          <div
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percent}
            aria-label="Profile completeness"
            className="h-8 min-w-0 flex-1 overflow-hidden rounded-sm bg-sunken"
          >
            <div
              className="h-8 rounded-sm bg-accent"
              style={{ inlineSize: `${percent}%` }}
            />
          </div>
          <span className="type-data-m text-primary">{percent}%</span>
        </div>
        <p className="type-body-s text-secondary">
          {thin === 0
            ? "Nothing is missing. Matching has everything it can use."
            : `${thin} ${thin === 1 ? "answer is" : "answers are"} empty or too brief to match on. Matching works on what you tell us, so these are the ones worth ten minutes.`}
        </p>
      </section>

      <Answers profile={profile} />
    </div>
  );
}

function Answers({ profile }: { profile: Schemas["ProfileView"] }) {
  const thin = new Set(profile.thinFieldIds);

  return (
    <div className="flex flex-col gap-32">
      {profile.formVersion.sections.map((section) => (
        <section key={section.id} className="flex flex-col gap-16">
          <h2 className="type-heading-m text-primary">{section.title}</h2>

          <dl className="flex flex-col gap-16">
            {section.fields.map((field) => {
              const record = profile.answers[field.id];
              return (
                <div key={field.id} className="flex flex-col gap-4">
                  <dt className="type-label text-muted">
                    {field.label}
                    {/* Named on the profile rather than only in the edit form:
                        this is the screen somebody opens to see how they look. */}
                    {field.admin && (
                      <span className="ml-8 normal-case type-caption text-muted">
                        Only the coordinator sees this
                      </span>
                    )}
                  </dt>
                  <dd className="type-body-m text-primary">
                    {record ? (
                      formatValue(record.value, field)
                    ) : (
                      <span className="text-muted">Not answered yet</span>
                    )}
                  </dd>
                  {thin.has(field.id) && record && (
                    <p className="type-caption text-muted">
                      Short enough that matching has little to work with.
                    </p>
                  )}
                </div>
              );
            })}
          </dl>
        </section>
      ))}
    </div>
  );
}

function formatValue(
  value: Schemas["AnswerValue"],
  field: Schemas["FormField"],
) {
  const label = (id: string) =>
    field.options?.find((o) => o.id === id)?.label ?? id;

  if (Array.isArray(value)) return value.map(label).join(", ");
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string" && field.options) return label(value);
  return String(value);
}

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
