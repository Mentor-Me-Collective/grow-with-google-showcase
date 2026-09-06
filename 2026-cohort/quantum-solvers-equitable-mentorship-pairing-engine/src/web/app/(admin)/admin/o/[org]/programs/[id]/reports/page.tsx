import type { Schemas } from "@/lib/api/client";
import { serverApi } from "@/lib/api/server";
import { requireCoordinator } from "@/lib/auth/guard";
import { BarChart, Funnel, LineChart, MilestoneProgress } from "./charts";
import { ReportToolbar } from "./report-toolbar";

export const metadata = { title: "Report" };

const longDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${iso}T00:00:00Z`));

/**
 * Architecture 5.18: what a coordinator sends a funder. Her deliverable, not a
 * vanity dashboard, which is why every section states what it means rather than
 * leaving a number to speak for itself.
 *
 * Printing is the point of the layout: sections avoid breaking across pages and
 * the navigation is dropped, per architecture 7.
 */
export default async function ReportsPage(
  props: PageProps<"/admin/o/[org]/programs/[id]/reports">,
) {
  const { org, id } = await props.params;
  const { from, to } = await props.searchParams;
  const result = await requireCoordinator(org);
  // The layout has already resolved this and rendered Forbidden if it failed.
  if (!result.ok) return null;

  const { data: report, error } = await serverApi.GET(
    "/programs/{programId}/report",
    {
      params: {
        path: { programId: id },
        query: {
          ...(typeof from === "string" ? { from } : {}),
          ...(typeof to === "string" ? { to } : {}),
        },
      },
    },
  );

  if (error || !report) {
    return (
      <div className="flex flex-col gap-16">
        <h1 className="type-heading-l text-primary">Report</h1>
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          The report did not load. Reload to try again.
        </div>
      </div>
    );
  }

  const matched = report.dropOff.find((d) => d.stage === "matched")?.count ?? 0;
  const active = report.dropOff.find((d) => d.stage === "still_active")?.count ?? 0;

  return (
    <div className="flex flex-col gap-32">
      <header className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">{report.programName}</h1>
        <p className="type-body-m text-secondary">
          {longDate(report.from)} to {longDate(report.to)}
        </p>
      </header>

      <ReportToolbar
        report={report}
        basePath={`/admin/o/${org}/programs/${id}/reports`}
      />

      <Section title="Coverage over time">
        <LineChart
          points={report.coverageOverTime}
          caption={`Coverage reached ${percent(last(report.coverageOverTime)?.value ?? 0)} by ${longDate(report.to)}. Coverage is the share of mentees holding a strand.`}
        />
      </Section>

      <Section title="Where people stopped">
        <Funnel stages={report.dropOff} />
        <p className="type-body-s text-secondary">
          {matched > 0
            ? `Of ${matched} people matched, ${active} are still meeting. Where a programme loses people is more useful than a single retention figure, because it is the part that can be acted on.`
            : "Nobody has been matched in this range yet."}
        </p>
      </Section>

      <Section title="Match quality by priority band">
        <table className="w-full border-collapse">
          <caption className="sr-only">
            Mean and median match score for each priority band
          </caption>
          <thead>
            <tr className="border-b border-subtle">
              <th scope="col" className="py-8 text-left type-label text-secondary">
                Band
              </th>
              <th scope="col" className="py-8 text-right type-label text-secondary">
                Mentees
              </th>
              <th scope="col" className="py-8 text-right type-label text-secondary">
                Mean
              </th>
              <th scope="col" className="py-8 text-right type-label text-secondary">
                Median
              </th>
            </tr>
          </thead>
          <tbody>
            {report.qualityByBand.map((band) => (
              <tr key={band.band} className="border-b border-subtle">
                <th scope="row" className="py-8 text-left type-body-s text-primary">
                  {capitalise(band.band)} priority
                </th>
                <td className="py-8 text-right type-data-m text-primary">
                  {band.menteeCount}
                </td>
                <td className="py-8 text-right type-data-m text-primary">
                  {band.meanScore.toFixed(2)}
                </td>
                <td className="py-8 text-right type-data-m text-primary">
                  {band.medianScore.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="type-body-s text-secondary">
          {bandGapSentence(report.qualityByBand)}
        </p>
      </Section>

      <Section title="Mentor load">
        <ul className="flex flex-col gap-8">
          {report.mentorLoad.map((m) => (
            <li
              key={m.mentor.participationId}
              className="flex items-center gap-12"
            >
              <span className="min-w-0 flex-1 truncate type-body-s text-primary">
                {m.mentor.name}
              </span>
              <span className="w-64 shrink-0 text-right type-data-m text-primary">
                {m.load}/{m.capacity}
              </span>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Sessions logged each week">
        <BarChart
          points={report.sessionsByWeek}
          caption="Sessions logged, not scheduled. Logging is the engagement signal the health monitor and this report both read."
          empty="A strand records how many sessions it has logged but not when any of them happened, so there is nothing to put on a week axis. This fills in once sessions are logged as dated entries."
        />
      </Section>

      <Section title="How people say it is going">
        <BarChart
          points={report.checkInSentiment}
          caption={
            report.checkInResponseRate
              ? `Check-in answers on a five-point scale, from ${percent(report.checkInResponseRate)} of participants. The rest did not reply, and the ones who do not reply are not a random sample.`
              : "Check-in answers on a five-point scale."
          }
          empty="The mid-point check-in goes out as a message rather than a question with recorded answers, so there is nothing counted here yet."
        />
      </Section>

      <Section title="Milestones reached">
        <MilestoneProgress items={report.milestoneCompletion} />
      </Section>

      <Section title="Who is in the programme">
        {report.demographics.length === 0 ? (
          <p className="type-body-m text-secondary">
            Nobody has agreed to share this information, so there is nothing to
            break down.
          </p>
        ) : (
          <>
            {report.demographics.map((breakdown) => (
              <div key={breakdown.fieldId} className="flex flex-col gap-8">
                <h3 className="type-label text-muted">{breakdown.label}</h3>
                <BarChart
                  points={breakdown.buckets}
                  caption=""
                  empty="Every group in this question was too small to show."
                />
                {breakdown.suppressedBuckets > 0 && (
                  <p className="type-caption text-muted">
                    {breakdown.suppressedBuckets}{" "}
                    {breakdown.suppressedBuckets === 1 ? "group is" : "groups are"}{" "}
                    not shown because {breakdown.suppressedBuckets === 1 ? "it has" : "they have"}{" "}
                    {report.suppressionThreshold} or fewer people in{" "}
                    {breakdown.suppressedBuckets === 1 ? "it" : "them"}.
                  </p>
                )}
              </div>
            ))}
            <p className="type-body-s text-secondary">
              Only questions participants agreed to share are counted here, and
              small groups are withheld rather than rounded — in a cohort this
              size, a column of one is an identification.
            </p>
          </>
        )}
      </Section>
    </div>
  );
}

/**
 * `break-inside-avoid` keeps a section off a page boundary when printed, per
 * architecture 7. The heading and its figures are one thing and splitting them
 * across a page is what makes a printed report look like a screenshot.
 */
function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="flex break-inside-avoid flex-col gap-16 border-t border-subtle pt-24">
      <h2 className="type-heading-m text-primary">{title}</h2>
      {children}
    </section>
  );
}

const percent = (n: number) => `${Math.round(n * 100)}%`;
const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const last = <T,>(items: T[]) => items[items.length - 1];

function bandGapSentence(bands: Schemas["PriorityBandStat"][]) {
  const present = bands.filter((b) => b.menteeCount > 0);
  if (present.length < 2) {
    return "Only one band has mentees in it, so there is no gap to compare.";
  }
  const means = present.map((b) => b.meanScore);
  const gap = Math.max(...means) - Math.min(...means);
  return gap < 0.05
    ? `The gap between the best and worst band average is ${gap.toFixed(2)}. High-priority mentees came out about as well as everyone else.`
    : `The gap between the best and worst band average is ${gap.toFixed(2)}. High-priority mentees did not do as well as the rest, and that is the number worth explaining.`;
}
