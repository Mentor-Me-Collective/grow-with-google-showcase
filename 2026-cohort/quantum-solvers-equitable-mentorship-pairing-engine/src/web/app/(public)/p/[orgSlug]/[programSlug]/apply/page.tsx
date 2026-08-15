import Link from "next/link";
import { notFound } from "next/navigation";
import { serverApi } from "@/lib/api/server";
import { PublicHeader, PublicMain } from "@/components/shell/public-shell";
import { buttonClasses } from "@/components/ui/button";
import { ApplyWizard } from "./apply-wizard";

const ROLES = ["mentee", "mentor"] as const;
type Role = (typeof ROLES)[number];

const isRole = (v: string | undefined): v is Role =>
  v !== undefined && (ROLES as readonly string[]).includes(v);

export const metadata = { title: "Apply" };

export default async function ApplyPage(
  props: PageProps<"/p/[orgSlug]/[programSlug]/apply">,
) {
  const { orgSlug, programSlug } = await props.params;
  const { role } = await props.searchParams;
  const chosen = Array.isArray(role) ? role[0] : role;

  const { data: program } = await serverApi.GET(
    "/orgs/{orgSlug}/programs/{programSlug}",
    { params: { path: { orgSlug, programSlug } } },
  );
  if (!program) notFound();

  const back = `/p/${orgSlug}/${programSlug}`;

  // Role is not defaulted. Guessing it would mean someone fills twenty minutes
  // of the wrong form and finds out at the end.
  if (!isRole(chosen)) return <ChooseRole back={back} program={program.name} />;

  if (program.state !== "open" || !program.openRoles.includes(chosen)) {
    return (
      <Shut
        back={back}
        title="This form is closed."
        body={
          program.state === "open"
            ? `${program.name} is not taking ${chosen} applications.`
            : `${program.name} is not taking applications at the moment.`
        }
      />
    );
  }

  const { data: form } = await serverApi.GET(
    "/orgs/{orgSlug}/programs/{programSlug}/form-schema",
    {
      params: { path: { orgSlug, programSlug }, query: { role: chosen } },
    },
  );
  if (!form) {
    return (
      <Shut
        back={back}
        title="This form is not ready yet."
        body={`${program.name} has not published its ${chosen} questions. Try again in a day or two.`}
      />
    );
  }

  return (
    <ApplyWizard
      version={form}
      role={chosen}
      programName={program.name}
      orgSlug={orgSlug}
      programSlug={programSlug}
    />
  );
}

function ChooseRole({ back, program }: { back: string; program: string }) {
  return (
    <>
      <PublicHeader />
      <PublicMain className="flex flex-col gap-24">
        <h1 className="type-heading-l text-primary">
          Which way round are you applying?
        </h1>
        <p className="type-body-m text-secondary">
          {program} runs two different forms. Pick the one that describes you and
          we will only ask you those questions.
        </p>
        <div className="flex flex-col gap-16 md:flex-row">
          <Link href={`${back}/apply?role=mentee`} className={buttonClasses({ size: "lg" })}>
            I want to be mentored
          </Link>
          <Link
            href={`${back}/apply?role=mentor`}
            className={buttonClasses({ size: "lg", variant: "secondary" })}
          >
            I want to mentor
          </Link>
        </div>
      </PublicMain>
    </>
  );
}

function Shut({
  back,
  title,
  body,
}: {
  back: string;
  title: string;
  body: string;
}) {
  return (
    <>
      <PublicHeader />
      <PublicMain className="flex flex-col gap-24">
        <h1 className="type-heading-l text-primary">{title}</h1>
        <p className="type-body-m text-secondary">{body}</p>
        <div className="flex">
          <Link href={back} className={buttonClasses({ variant: "secondary" })}>
            Back to the programme
          </Link>
        </div>
      </PublicMain>
    </>
  );
}
