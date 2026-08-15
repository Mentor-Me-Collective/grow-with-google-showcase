import Link from "next/link";
import { notFound } from "next/navigation";
import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { DecisionBar } from "./decision-bar";

export const metadata = { title: "Application" };

const dateTime = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "UTC",
});

/**
 * Architecture 5.8's "open", and the reason the review queue is usable at all:
 * nobody can approve someone without reading what they wrote.
 *
 * The answers are rendered against the form version this application was
 * answered on, not the current published one. A coordinator who edits the form
 * next week must still see last week's applications as their authors saw them.
 */
export default async function ApplicationDetailPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/applications/[applicationId]">,
) {
  const { org, id, applicationId } = await props.params;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const { data: application } = await serverApi.GET(
    "/applications/{applicationId}",
    { params: { path: { applicationId } } },
  );
  if (!application) notFound();

  const { data: version } = await serverApi.GET(
    "/form-versions/{formVersionId}",
    { params: { path: { formVersionId: application.formVersionId } } },
  );

  const back = `/admin/o/${org}/programs/${id}/applications`;
  const decided = application.status !== "submitted" && application.status !== "under_review";

  return (
    <div className="flex flex-col gap-32">
      <div className="flex flex-col gap-8">
        <Link href={back} className="type-body-s text-link underline">
          Back to applications
        </Link>
        <h1 className="type-heading-l text-primary">{application.name}</h1>
        <p className="type-body-s text-muted">
          Applying as a {application.role}. Submitted{" "}
          {dateTime.format(new Date(application.submittedAt))}.{" "}
          {application.email}
        </p>
        {decided && (
          <p className="type-body-s text-secondary">
            {readableStatus(application.status)}
            {application.decidedBy ? ` by ${application.decidedBy}` : ""}
            {application.decidedAt
              ? ` on ${dateTime.format(new Date(application.decidedAt))}`
              : ""}
            .
          </p>
        )}
      </div>

      {version ? (
        <Answers version={version} answers={application.answers} />
      ) : (
        <p className="rounded-md border border-subtle bg-sunken p-16 type-body-m text-secondary">
          The form this was answered on could not be loaded, so the answers
          below cannot be labelled. Nothing has been lost — reload to try again.
        </p>
      )}

      <DecisionBar
        applicationId={application.id}
        name={application.name}
        role={application.role}
        decided={decided}
      />
    </div>
  );
}

function Answers({
  version,
  answers,
}: {
  version: Schemas["FormVersion"];
  answers: Record<string, Schemas["AnswerRecord"]>;
}) {
  return (
    <div className="flex flex-col gap-32">
      {version.sections.map((section) => (
        <section key={section.id} className="flex flex-col gap-16">
          <h2 className="type-heading-m text-primary">{section.title}</h2>

          <dl className="flex flex-col gap-16">
            {section.fields.map((field) => {
              const record = answers[field.id];
              return (
                <div key={field.id} className="flex flex-col gap-4">
                  <dt className="type-label text-muted">{field.label}</dt>
                  <dd className="type-body-m text-primary">
                    {record ? (
                      <>
                        {formatValue(record.value, field)}
                        {/* Provenance matters when reading someone's words back:
                            a guided answer came out of a prompt, not a blank box. */}
                        {record.provenance === "guided" && (
                          <span className="type-caption text-muted">
                            {" "}
                            — answered with a prompt
                          </span>
                        )}
                      </>
                    ) : (
                      <span className="text-muted">Not answered</span>
                    )}
                  </dd>
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

function readableStatus(status: Schemas["ApplicationStatus"]) {
  switch (status) {
    case "approved":
      return "Approved";
    case "waitlisted":
      return "Waitlisted";
    case "rejected":
      return "Closed";
    case "under_review":
      return "Being read";
    case "submitted":
      return "Waiting";
  }
}
