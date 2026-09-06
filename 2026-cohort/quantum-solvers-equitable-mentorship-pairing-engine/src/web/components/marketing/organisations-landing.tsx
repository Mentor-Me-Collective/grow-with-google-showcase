import Link from "next/link";
import { WeaveMark } from "@/components/brand/weave-mark";
import { buttonClasses } from "@/components/ui/button";

/**
 * The product's front door, from `Braid For Organizations.dc.html`.
 *
 * This is design-direction 5.2 place five — "marketing and the program landing
 * page hero" — which is the one place outside the four in-product moments where
 * the display face is allowed. It is used here exactly twice: the hero headline
 * and the closing headline. Every other heading on the page is Switzer.
 *
 * Where this departs from the design file, it is because the file draws values
 * the token layer does not have. Those departures are noted at each site rather
 * than collected somewhere nobody reads: a 76px headline becomes `display-xl`
 * at 56, the hero's radial gradient and the header's backdrop blur are dropped
 * per the "no gradients, no glassmorphism" rule, and off-scale spacing snaps to
 * the nine steps in section 6.
 *
 * The figures are the seeded sample round, named as such. See `SAMPLE`.
 */

/** The demo the reader can run in two clicks, which is the only proof this
    product currently has and is worth more than an unverifiable aggregate. */
const SAMPLE = [
  { v: "24", k: "applications in the sample round" },
  { v: "9", k: "pairs proposed, 5 left for a human" },
  { v: "0.85", k: "mean fit for high-priority mentees" },
  { v: "79%", k: "of mentees holding a strand after publish" },
] as const;

const HERO_STATS = [
  { v: "9", k: "pairs proposed" },
  { v: "0.85", k: "median fit score" },
  { v: "5", k: "need a human" },
  { v: "4s", k: "time to solve" },
] as const;

const HERO_PAIRS = [
  { a: "Aisha Bello", b: "Tunde Bakare", score: "0.94", note: "Both Tuesdays, same stack" },
  { a: "Fatima Yusuf", b: "Chidinma Eze", score: "0.91", note: "Asked for the same thing" },
  { a: "Joy Achieng", b: "Priya Raghunathan", score: "0.88", note: "Second choice honoured" },
  { a: "Ifeoma Nwosu", b: "— unmatched", score: "—", note: "No mentor free at weekends" },
] as const;

const STEPS = [
  {
    n: "01",
    title: "Open applications",
    body: "Your own questions, one link, one page. Mentors and mentees answer the same availability and stage questions, so they can be compared at all.",
    time: "Setup, 20 minutes",
  },
  {
    n: "02",
    title: "Watch the ratio",
    body: "A daily view of signups, mentor-to-mentee ratio, and who is about to fall through — while you can still recruit against the gap.",
    time: "Two minutes a day",
  },
  {
    n: "03",
    title: "Review the run",
    body: "Braid proposes pairs with a score and a reason for each, and shows the fairness summary before it shows a single name. Nothing is final until you publish.",
    time: "Under an hour",
  },
  {
    n: "04",
    title: "Publish and follow through",
    body: "Both sides get their match with a shared strand for messages and session notes. You get milestone prompts and a report at the end.",
    time: "One click",
  },
] as const;

/** What the engine weighs, stated as behaviour rather than as outcomes nobody
    has measured yet. The bar is the weight, not a result. */
const WEIGHTED = [
  {
    label: "Overlapping working hours",
    value: "Hard rule",
    pct: "100%",
    note: "A pair who cannot find an hour together is not a pair. This one is a filter, not a score.",
  },
  {
    label: "What the mentee asked to work on",
    value: "Weight 90",
    pct: "90%",
    note: "Matched against what each mentor offered, through a shared vocabulary rather than free text.",
  },
  {
    label: "Priority band",
    value: "Weight 60",
    pct: "60%",
    note: "Lifts mentees earlier in their career, and the run then reports whether it actually worked.",
  },
] as const;

const GUARANTEES = [
  {
    title: "The distribution before the names",
    body: "The run review opens on coverage, mentor load, and mean match quality per priority band. The pair list is underneath it. That ordering is deliberate: a list of names cannot tell you whether the round was fair.",
  },
  {
    title: "Nothing publishes itself",
    body: "A run produces a draft. You swap, reject, lock and re-run as often as you like, and the pairs reach participants only when you press publish.",
  },
  {
    title: "Every deviation is on the record",
    body: "Criteria edits, form versions, manual pairings, overrides and exports are written to an audit log in plain words, with who did it and when.",
  },
] as const;

const SEGMENTS = [
  {
    name: "University chapters",
    body: "Alumni matched to final-year students, one round a term, run by two volunteers.",
  },
  {
    name: "Professional associations",
    body: "Members mentoring members across cities, where fairness between chapters matters.",
  },
  {
    name: "Employer resource groups",
    body: "Internal programmes that have to survive an HR review and a reorganisation.",
  },
  {
    name: "NGOs and fellowships",
    body: "Cohort programmes with funders who need outcomes reported, not anecdotes.",
  },
] as const;

const TRUST = [
  {
    title: "Every score, broken down",
    body: "Availability, stage, focus area, language and preference — each with its own weight and its own contribution to the number.",
  },
  {
    title: "You set the weights",
    body: "If your programme cares most about availability, say so. The model is a set of dials, not a black box.",
  },
  {
    title: "Overrides are on the record",
    body: "Who changed a pair, when, and why. The run history survives a coordinator handover.",
  },
  {
    title: "Participant data stays yours",
    body: "Applications are visible to coordinators only, reporting is opt-in per participant, and any group of three or fewer is withheld from a report rather than rounded.",
  },
] as const;

/** The woven field behind the hero and the closing section. The mark is a
    weave, so the background is the mark's own geometry at page scale — drawn
    rather than tiled, and inert to a screen reader. */
function WovenField({
  viewBox,
  paths,
  className = "",
}: {
  viewBox: string;
  paths: readonly string[];
  className?: string;
}) {
  return (
    <svg
      viewBox={viewBox}
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
    >
      <g fill="none" stroke="var(--border-subtle)" strokeWidth="1.25">
        {paths.map((d) => (
          <path key={d} d={d} />
        ))}
      </g>
    </svg>
  );
}

const HERO_WEAVE = [
  "M-40 120 C 300 120, 380 300, 720 300 C 1060 300, 1140 120, 1480 120",
  "M-40 300 C 300 300, 380 120, 720 120 C 1060 120, 1140 300, 1480 300",
  "M-40 330 C 300 330, 380 520, 720 520 C 1060 520, 1140 330, 1480 330",
  "M-40 520 C 300 520, 380 330, 720 330 C 1060 330, 1140 520, 1480 520",
  "M-40 560 C 300 560, 380 740, 720 740 C 1060 740, 1140 560, 1480 560",
  "M-40 740 C 300 740, 380 560, 720 560 C 1060 560, 1140 740, 1480 740",
] as const;

const CLOSING_WEAVE = [
  "M-40 90 C 300 90, 380 260, 720 260 C 1060 260, 1140 90, 1480 90",
  "M-40 260 C 300 260, 380 90, 720 90 C 1060 90, 1140 260, 1480 260",
  "M-40 300 C 300 300, 380 470, 720 470 C 1060 470, 1140 300, 1480 300",
  "M-40 470 C 300 470, 380 300, 720 300 C 1060 300, 1140 470, 1480 470",
] as const;

const NAV = [
  { href: "#how", label: "How it works" },
  { href: "#weighting", label: "Weighting" },
  { href: "#who", label: "Who it is for" },
  { href: "#trust", label: "Fairness" },
] as const;

/** Section shell. 96 top and bottom is the largest step on the scale; the
    design's 112 does not exist and 96 is the nearest that does. */
function Section({
  id,
  className = "",
  children,
}: {
  id?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className={`border-b border-subtle ${className}`}>
      <div className="mx-auto flex w-full max-w-coordinator flex-col px-16 py-64 md:px-32 md:py-96">
        {children}
      </div>
    </section>
  );
}

function Eyebrow({ children, dim = false }: { children: React.ReactNode; dim?: boolean }) {
  return (
    <span className={`type-label ${dim ? "text-on-inverse opacity-70" : "text-muted"}`}>
      {children}
    </span>
  );
}

export function OrganisationsLanding() {
  return (
    <div className="flex flex-col bg-page">
      {/* The design gives this a translucent blurred bar. Glassmorphism is out
          under the hard rules, so it is the page colour with the same hairline
          — which also stops the woven field showing through as noise. */}
      <header className="sticky top-0 z-20 border-b border-subtle bg-page">
        <div className="mx-auto flex h-header-sm max-w-coordinator items-center justify-between gap-16 px-16 md:h-header md:px-32">
          <Link
            href="/"
            aria-label="Braid, home"
            className="flex items-center rounded-sm outline-focus outline-offset-2 pointer-coarse:min-h-field focus-visible:outline-2"
          >
            <WeaveMark size={32} id="marketing-mark" title={null} />
            <span className="wordmark text-primary">Braid</span>
          </Link>

          <nav aria-label="Sections" className="flex items-center gap-16 md:gap-32">
            <ul className="hidden items-center gap-32 md:flex">
              {NAV.map((item) => (
                <li key={item.href}>
                  <a
                    href={item.href}
                    className="type-body-m inline-flex items-center rounded-sm font-medium text-primary outline-focus outline-offset-2 pointer-coarse:min-h-field hover:text-secondary focus-visible:outline-2"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
            <Link href="/signin" className={buttonClasses({ size: "md" })}>
              See a sample round
            </Link>
          </nav>
        </div>
      </header>

      {/* ---------------------------------------------------------------- */}
      {/* Hero                                                             */}
      {/* ---------------------------------------------------------------- */}
      <section className="relative overflow-hidden border-b border-subtle">
        <WovenField viewBox="0 0 1440 760" paths={HERO_WEAVE} className="opacity-55" />

        <div className="relative mx-auto flex w-full max-w-coordinator flex-col items-center gap-32 px-16 py-64 text-center md:gap-48 md:px-32 md:py-96">
          <Eyebrow>For the people who run mentoring programmes</Eyebrow>

          {/* 5.2 place five. The design sets 76/80; the scale's largest is
              display-xl at 56/60 and there is no fourteenth token. */}
          <h1 className="type-display-xl max-w-[20ch] text-balance text-primary">
            Matching that a coordinator can stand behind.
          </h1>

          <p className="type-body-l max-w-[62ch] text-pretty text-secondary">
            Braid takes a mentoring round from open applications to published
            pairs — with a fairness summary, an audit trail, and every decision
            left in your hands. Built for one person running a programme on
            nights and weekends.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-16">
            <Link href="/signin" className={buttonClasses({ size: "lg" })}>
              See a sample round
            </Link>
            <Link
              href="/p/she-code-africa/backend-cohort-4"
              className={buttonClasses({ variant: "secondary", size: "lg" })}
            >
              Look at a programme page
            </Link>
          </div>

          <span className="type-caption text-muted">
            The sample round is real and runs in your browser · No card, no sales call
          </span>

          {/* The product, rather than a picture of it. Same figures as the
              seeded cohort, so the reader meets them again on the demo. */}
          <div className="mt-24 w-full max-w-[1000px] overflow-hidden rounded-lg border border-subtle bg-surface text-left">
            <div className="flex items-center justify-between gap-16 border-b border-subtle bg-sunken px-16 py-12">
              <div className="flex flex-wrap items-baseline gap-12">
                <span className="type-body-s font-semibold text-primary">Run review</span>
                <span className="type-body-s text-muted">
                  Backend mentoring, cohort 4 · She Code Africa
                </span>
              </div>
              <span className="type-data-m text-secondary">run 04</span>
            </div>

            <dl className="grid grid-cols-2 border-b border-subtle md:grid-cols-4">
              {HERO_STATS.map((s, i) => (
                <div
                  key={s.k}
                  className={`flex flex-col gap-4 p-16 ${
                    i > 0 ? "border-subtle md:border-l" : ""
                  } ${i % 2 === 1 ? "border-l border-subtle md:border-l" : ""}`}
                >
                  <dd className="type-data-l text-primary">{s.v}</dd>
                  <dt className="type-caption text-muted">{s.k}</dt>
                </div>
              ))}
            </dl>

            <table className="w-full border-collapse">
              <caption className="sr-only">
                Four of the nine pairs this run proposed
              </caption>
              <thead className="sr-only">
                <tr>
                  <th scope="col">Mentee</th>
                  <th scope="col">Mentor</th>
                  <th scope="col">Fit score</th>
                  <th scope="col">Why</th>
                </tr>
              </thead>
              <tbody>
                {HERO_PAIRS.map((p) => (
                  <tr key={p.a} className="border-b border-subtle">
                    <th
                      scope="row"
                      className="type-body-s px-16 py-12 text-left font-medium text-primary"
                    >
                      {p.a}
                    </th>
                    <td className="type-body-s px-16 py-12 text-secondary">{p.b}</td>
                    <td className="type-data-m px-16 py-12 text-primary">{p.score}</td>
                    <td className="type-caption hidden px-16 py-12 text-muted sm:table-cell">
                      {p.note}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="flex items-center justify-between gap-16 px-16 py-12">
              <span className="type-caption text-muted">4 of 9 pairs shown</span>
              <span className="type-body-s font-medium text-link">Publish round</span>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- */}
      {/* The sample round                                                 */}
      {/* ---------------------------------------------------------------- */}
      <section className="bg-inverse text-on-inverse">
        <div className="mx-auto flex w-full max-w-coordinator flex-col gap-48 px-16 py-64 md:px-32 md:py-96">
          <Eyebrow dim>From the sample round, which you can run yourself</Eyebrow>

          <dl className="grid grid-cols-1 gap-48 sm:grid-cols-2 lg:grid-cols-4">
            {SAMPLE.map((s) => (
              <div key={s.k} className="flex flex-col gap-12">
                <dd className="type-data-xl">{s.v}</dd>
                <dt className="type-body-m max-w-[24ch] text-pretty opacity-80">{s.k}</dt>
              </div>
            ))}
          </dl>

          {/* The design carries an aggregate across 128 programmes here. Braid
              has not run one yet, so this says what is actually true instead. */}
          <p className="type-caption max-w-[80ch] text-pretty opacity-70">
            Braid is new and has no track record to quote. These are the figures
            from the seeded cohort of twenty-four people that ships with it —
            press <span className="font-semibold">Start a run</span> and you will
            get them, or something close, on your own machine in about four
            seconds.
          </p>
        </div>
      </section>

      {/* ---------------------------------------------------------------- */}
      {/* How it works                                                     */}
      {/* ---------------------------------------------------------------- */}
      <Section id="how">
        <div className="flex max-w-[60ch] flex-col gap-16">
          <Eyebrow>How it works</Eyebrow>
          <h2 className="type-heading-l text-balance text-primary">
            Four steps, and you are still the one deciding.
          </h2>
          <p className="type-body-l text-pretty text-secondary">
            Braid does the arithmetic and shows its work. It never publishes a
            pair you have not seen.
          </p>
        </div>

        <ol className="mt-48 grid grid-cols-1 gap-32 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((st) => (
            <li key={st.n} className="flex flex-col gap-16 border-t border-subtle pt-24">
              <span className="type-data-m text-muted">{st.n}</span>
              <h3 className="type-heading-m text-balance text-primary">{st.title}</h3>
              <p className="type-body-m text-pretty text-secondary">{st.body}</p>
              <span className="type-caption text-muted">{st.time}</span>
            </li>
          ))}
        </ol>
      </Section>

      {/* ---------------------------------------------------------------- */}
      {/* What it weighs                                                   */}
      {/* ---------------------------------------------------------------- */}
      <Section id="weighting" className="bg-sunken">
        <div className="grid grid-cols-1 gap-48 lg:grid-cols-[minmax(320px,1fr)_minmax(360px,1.1fr)] lg:gap-64">
          <div className="flex flex-col gap-24">
            <Eyebrow>Weighting</Eyebrow>
            <h2 className="type-heading-l text-balance text-primary">
              Pairs that hold past the second month.
            </h2>
            <p className="type-body-l max-w-[52ch] text-pretty text-secondary">
              Programmes lose pairs early, and usually to a mismatch nobody
              caught at the start. Braid weights the things that make people keep
              showing up — availability, stage, language, and what each side
              actually asked for. These are the defaults; they are yours to
              change.
            </p>

            <dl className="mt-8 flex flex-col border-t border-subtle">
              {WEIGHTED.map((o) => (
                <div key={o.label} className="flex flex-col gap-8 border-b border-subtle py-16">
                  <div className="flex items-baseline justify-between gap-16">
                    <dt className="type-body-m font-medium text-primary">{o.label}</dt>
                    <dd className="type-data-m shrink-0 text-primary">{o.value}</dd>
                  </div>
                  {/* Presentational: the number is stated above it in text. */}
                  <div
                    aria-hidden="true"
                    className="h-4 overflow-hidden rounded-full bg-subtle"
                  >
                    <div
                      className="h-4 rounded-full bg-accent"
                      style={{ inlineSize: o.pct }}
                    />
                  </div>
                  <p className="type-caption text-pretty text-muted">{o.note}</p>
                </div>
              ))}
            </dl>
          </div>

          {/* The design puts three testimonials here. Braid has no users to
              quote, so the column carries the three promises a coordinator can
              check against the running product instead. */}
          <ul className="flex flex-col gap-24">
            {GUARANTEES.map((g) => (
              <li
                key={g.title}
                className="flex flex-col gap-12 rounded-lg border border-subtle bg-page p-24 md:p-32"
              >
                <h3 className="type-heading-s text-balance text-primary">{g.title}</h3>
                <p className="type-body-m text-pretty text-secondary">{g.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </Section>

      {/* ---------------------------------------------------------------- */}
      {/* Who it is for                                                    */}
      {/* ---------------------------------------------------------------- */}
      <Section id="who">
        <div className="flex max-w-[56ch] flex-col gap-16">
          <Eyebrow>Who it is for</Eyebrow>
          <h2 className="type-heading-l text-balance text-primary">
            Small programmes with real stakes.
          </h2>
          <p className="type-body-l text-pretty text-secondary">
            Braid is built for the coordinator who has a spreadsheet, a deadline,
            and no engineering team.
          </p>
        </div>

        <ul className="mt-48 grid grid-cols-1 gap-24 sm:grid-cols-2 lg:grid-cols-4">
          {SEGMENTS.map((g) => (
            <li
              key={g.name}
              className="flex flex-col gap-12 rounded-lg border border-subtle bg-surface p-24"
            >
              <h3 className="type-heading-s text-balance text-primary">{g.name}</h3>
              <p className="type-body-s text-pretty text-secondary">{g.body}</p>
            </li>
          ))}
        </ul>
      </Section>

      {/* ---------------------------------------------------------------- */}
      {/* Fairness                                                         */}
      {/* ---------------------------------------------------------------- */}
      <Section id="trust" className="bg-sunken">
        <div className="flex max-w-[60ch] flex-col gap-16">
          <Eyebrow>Fairness</Eyebrow>
          <h2 className="type-heading-l text-balance text-primary">
            If you cannot explain a pair, we have failed.
          </h2>
          <p className="type-body-l text-pretty text-secondary">
            Every score breaks down into named factors with weights you set.
            Every override is signed and dated. When a board member asks why two
            people were matched, the answer is one click away.
          </p>
        </div>

        <ul className="mt-48 grid grid-cols-1 gap-32 sm:grid-cols-2">
          {TRUST.map((t) => (
            <li key={t.title} className="flex flex-col gap-12 border-t border-subtle pt-24">
              <h3 className="type-heading-s text-balance text-primary">{t.title}</h3>
              <p className="type-body-m text-pretty text-secondary">{t.body}</p>
            </li>
          ))}
        </ul>
      </Section>

      {/* ---------------------------------------------------------------- */}
      {/* Closing                                                          */}
      {/* ---------------------------------------------------------------- */}
      <section className="relative overflow-hidden">
        <WovenField viewBox="0 0 1440 420" paths={CLOSING_WEAVE} className="opacity-50" />

        <div className="relative mx-auto flex w-full max-w-coordinator flex-col items-center gap-32 px-16 py-64 text-center md:px-32 md:py-96">
          {/* The second and last use of the display face on this page. */}
          <h2 className="type-display-xl max-w-[22ch] text-balance text-primary">
            Bring us your next round.
          </h2>
          <p className="type-body-l max-w-[54ch] text-pretty text-secondary">
            Run the sample cohort end to end — open the applications, start a
            run, read the fairness summary, publish it, and watch the pairs
            appear on the participant side. It takes about ten minutes and needs
            nothing from you.
          </p>
          <div className="flex flex-wrap justify-center gap-16">
            <Link href="/signin" className={buttonClasses({ size: "lg" })}>
              See a sample round
            </Link>
            <a
              href="https://github.com/DGbolaga/braid"
              className={buttonClasses({ variant: "secondary", size: "lg" })}
            >
              Read the source
            </a>
          </div>
        </div>
      </section>

      <footer className="border-t border-subtle bg-page">
        <div className="mx-auto flex w-full max-w-coordinator flex-wrap items-center justify-between gap-24 px-16 py-48 md:px-32">
          <Link
            href="/"
            aria-label="Braid, home"
            className="flex items-center rounded-sm outline-focus outline-offset-2 pointer-coarse:min-h-field focus-visible:outline-2"
          >
            <WeaveMark size={32} id="footer-mark" title={null} />
            <span className="wordmark text-primary">Braid</span>
          </Link>

          <nav aria-label="Footer">
            <ul className="flex flex-wrap gap-24 md:gap-32">
              {NAV.map((item) => (
                <li key={item.href}>
                  <a
                    href={item.href}
                    className="type-body-s inline-flex items-center rounded-sm text-secondary outline-focus outline-offset-2 pointer-coarse:min-h-field hover:text-primary focus-visible:outline-2"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <span className="type-caption text-muted">
            Built for the Mentor Me Collective × Grow with Google 2026 cohort
          </span>
        </div>
      </footer>
    </div>
  );
}
