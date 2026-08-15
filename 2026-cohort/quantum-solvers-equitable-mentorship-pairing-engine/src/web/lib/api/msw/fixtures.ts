import type { components } from "../types";

type S = components["schemas"];

/** Fixed clock so fixtures are deterministic and diffs stay readable. */
export const NOW = new Date("2026-08-08T09:00:00.000Z");

const daysAgo = (n: number) =>
  new Date(NOW.getTime() - n * 86_400_000).toISOString();
/** Same day, a chosen hour. Without it every message is timestamped 09:00. */
const dayAt = (n: number, hour: number, minute: number) => {
  const d = new Date(NOW.getTime() - n * 86_400_000);
  d.setUTCHours(hour, minute, 0, 0);
  return d.toISOString();
};
const daysAhead = (n: number) =>
  new Date(NOW.getTime() + n * 86_400_000).toISOString();

/** Readable, valid-shaped ids. The leading group names the entity kind. */
const uuid = (kind: number, n: number) =>
  `${String(kind).padStart(8, "0")}-0000-4000-8000-${String(n).padStart(12, "0")}`;

const ORG = uuid(1, 1);
const PROGRAM = uuid(2, 1);
const account = (n: number) => uuid(3, n);
const participation = (n: number) => uuid(4, n);
const pair = (n: number) => uuid(7, n);
const strand = (n: number) => uuid(8, n);
const message = (n: number) => uuid(9, n);

export const PROGRAM_ID = PROGRAM;
export const ORG_SLUG = "she-code-africa";
export const PROGRAM_SLUG = "backend-cohort-4";

const organisation: S["Organisation"] = {
  id: ORG,
  slug: ORG_SLUG,
  name: "She Code Africa",
  logoUrl: null,
};

// name, timezone, skills, capacity, load, headline, completeness
type MentorSeed = [string, string, string[], number, number, string, number];

const MENTORS: MentorSeed[] = [
  ["Amara Okonkwo", "Africa/Lagos", ["Python", "Django", "API design"], 3, 3, "Staff engineer, payments", 1],
  ["Tunde Bakare", "Africa/Lagos", ["Go", "Kubernetes", "Observability"], 2, 2, "Platform engineer", 0.95],
  ["Wanjiru Kamau", "Africa/Nairobi", ["Node.js", "TypeScript", "GraphQL"], 3, 2, "Backend lead, fintech", 1],
  ["Chidinma Eze", "Africa/Lagos", ["SQL", "Data engineering", "Airflow"], 2, 2, "Data engineer", 0.9],
  ["Kwame Mensah", "Africa/Accra", ["Java", "Spring", "System design"], 2, 1, "Senior engineer, logistics", 0.85],
  ["Priya Raghunathan", "Europe/London", ["AWS", "Terraform", "Reliability"], 2, 3, "SRE, over capacity", 1],
  ["Ifeoma Nwosu", "Africa/Lagos", ["Security", "Threat modelling"], 1, 1, "Application security", 0.8],
  ["Samuel Adeyemi", "Africa/Lagos", ["Django", "PostgreSQL"], 2, 0, "Backend engineer", 0.7],
];

// name, timezone, skills, band, completeness, headline
type MenteeSeed = [string, string, string[], S["PriorityBand"], number, string];

const MENTEES: MenteeSeed[] = [
  ["Blessing Adewale", "Africa/Lagos", ["Python", "Flask"], "high", 0.9, "Building an expense tracker in Flask"],
  ["Ngozi Obi", "Africa/Lagos", ["JavaScript", "React"], "medium", 0.85, "Front-end developer moving to the back"],
  ["Fatima Yusuf", "Africa/Kano", ["Python"], "high", 0.6, "Teaching herself Python in the evenings"],
  ["David Otieno", "Africa/Nairobi", ["Node.js", "Express"], "medium", 0.8, "Junior engineer, internal tools"],
  ["Grace Mwangi", "Africa/Nairobi", ["Java"], "low", 0.95, "Java developer, first year in industry"],
  ["Emeka Nnamdi", "Africa/Lagos", ["Go", "Docker"], "medium", 0.75, "Support engineer learning Go"],
  ["Aisha Bello", "Africa/Lagos", ["SQL", "Python"], "high", 0.55, "Analyst writing more SQL than spreadsheets"],
  ["Joy Achieng", "Africa/Nairobi", ["TypeScript"], "low", 0.9, "Bootcamp graduate, six months out"],
  ["Tobi Salami", "Africa/Lagos", ["Python", "Django"], "medium", 0.8, "Building a library API on his own"],
  ["Halima Sani", "Africa/Kano", ["HTML", "CSS"], "high", 0.4, "First year of a computer science degree"],
  ["Chinedu Okafor", "Africa/Lagos", ["Java", "Spring"], "low", 0.85, "Contract developer, Spring services"],
  ["Zainab Musa", "Africa/Lagos", ["Python", "Pandas"], "high", 0.65, "Data analyst who wants to ship code"],
  ["Peter Kimani", "Africa/Nairobi", ["Kubernetes"], "medium", 0.9, "Ops engineer learning Kubernetes properly"],
  ["Adaeze Ugo", "Africa/Lagos", ["TypeScript", "Node.js"], "medium", 0.88, "Freelance developer, Node services"],
  ["Yusuf Ibrahim", "Africa/Kano", ["Python"], "high", 0.35, "Career changer, six months in"],
  ["Lerato Molefe", "Africa/Johannesburg", ["Go"], "low", 0.7, "Backend intern, Go and Postgres"],
];

const mentorEntries: S["RosterEntry"][] = MENTORS.map(
  ([name, timezone, , capacity, load, , completeness], i) => ({
    id: participation(i + 1),
    account: {
      id: account(i + 1),
      name,
      email: `${name.toLowerCase().replace(/ /g, ".")}@example.org`,
      emailVerified: true,
      photoUrl: null,
    },
    role: "mentor",
    status: "approved",
    matched: load > 0,
    capacity,
    load,
    profileCompleteness: completeness,
    timezone,
    joinedAt: daysAgo(60 - i),
  }),
);

const menteeEntries: S["RosterEntry"][] = MENTEES.map(
  ([name, timezone, , , completeness], i) => ({
    id: participation(100 + i + 1),
    account: {
      id: account(100 + i + 1),
      name,
      email: `${name.toLowerCase().replace(/ /g, ".")}@example.org`,
      emailVerified: i % 7 !== 0,
      photoUrl: null,
    },
    role: "mentee",
    status: i >= 14 ? "waitlisted" : "approved",
    matched: i < 14,
    capacity: null,
    load: null,
    profileCompleteness: completeness,
    timezone,
    joinedAt: daysAgo(50 - i),
  }),
);

const mentorSkills = (i: number) => MENTORS[i][2];
const menteeSkills = (i: number) => MENTEES[i][2];

/** Mentee index -> mentor index. 14 of 16 mentees matched. */
const ASSIGNMENT: Array<[number, number, number]> = [
  // menteeIdx, mentorIdx, score
  [0, 0, 0.91],
  [1, 2, 0.84],
  [2, 0, 0.72],
  [3, 2, 0.8],
  [4, 4, 0.88],
  [5, 1, 0.86],
  [6, 3, 0.68],
  [7, 5, 0.83],
  [8, 0, 0.79],
  [9, 6, 0.57],
  [10, 4, 0.9],
  [11, 3, 0.74],
  [12, 1, 0.81],
  [13, 5, 0.76],
];

const draftPairs: S["DraftPair"][] = ASSIGNMENT.map(
  ([menteeIdx, mentorIdx, score], i) => ({
    id: pair(i + 1),
    mentee: {
      participationId: menteeEntries[menteeIdx].id,
      name: menteeEntries[menteeIdx].account.name,
      photoUrl: null,
    },
    mentor: {
      participationId: mentorEntries[mentorIdx].id,
      name: mentorEntries[mentorIdx].account.name,
      photoUrl: null,
    },
    score,
    priorityBand: MENTEES[menteeIdx][3],
  }),
);

const bandStat = (band: S["PriorityBand"]): S["PriorityBandStat"] => {
  const scores = ASSIGNMENT.filter(([m]) => MENTEES[m][3] === band).map(
    ([, , s]) => s,
  );
  const sorted = [...scores].sort((a, b) => a - b);
  const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
  const mid = Math.floor(sorted.length / 2);
  const median =
    sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  return {
    band,
    menteeCount: scores.length,
    meanScore: Number(mean.toFixed(3)),
    medianScore: Number(median.toFixed(3)),
  };
};

const scoreDistribution: S["ScoreBucket"][] = [
  [0.5, 0.6],
  [0.6, 0.7],
  [0.7, 0.8],
  [0.8, 0.9],
  [0.9, 1.0],
].map(([rangeStart, rangeEnd]) => ({
  rangeStart,
  rangeEnd,
  count: ASSIGNMENT.filter(
    ([, , s]) => s >= rangeStart && (rangeEnd === 1 ? s <= 1 : s < rangeEnd),
  ).length,
}));

const fairnessSummary: S["FairnessSummary"] = {
  coverageRate: Number((ASSIGNMENT.length / MENTEES.length).toFixed(4)),
  matchedCount: ASSIGNMENT.length,
  unmatchedCount: MENTEES.length - ASSIGNMENT.length,
  totalMentees: MENTEES.length,
  mentorLoad: MENTORS.map(([, , , capacity, load], i) => ({
    mentor: {
      participationId: mentorEntries[i].id,
      name: mentorEntries[i].account.name,
      photoUrl: null,
    },
    load,
    capacity,
  })),
  priorityBands: [bandStat("high"), bandStat("medium"), bandStat("low")],
  scoreDistribution,
};

/* ---------------------------------------------------------------
   Published form schemas. Field ids are the durable thing here: an
   answer is keyed by one for the life of the program, across label
   edits and across versions. Kind 6 is a field, kind 10 an option,
   kind 11 a section, kind 12 a version.
   --------------------------------------------------------------- */

const answered = (
  value: S["AnswerValue"],
  provenance: S["Provenance"],
  daysAgoStamped: number,
): S["AnswerRecord"] => ({
  value,
  provenance,
  answeredAt: daysAgo(daysAgoStamped),
});

const field = (n: number) => uuid(6, n);
const option = (n: number) => uuid(10, n);
const section = (n: number) => uuid(11, n);
const formVersion = (n: number) => uuid(12, n);

// The three downstream flags from architecture 5.4, defaulted off.
type FlagSet = { matching?: boolean; equity?: boolean; admin?: boolean };

const f = (
  n: number,
  type: S["FormFieldType"],
  label: string,
  required: boolean,
  flags: FlagSet,
  rest: Partial<S["FormField"]> = {},
): S["FormField"] => ({
  id: field(n),
  type,
  label,
  help: null,
  required,
  matching: flags.matching ?? false,
  equity: flags.equity ?? false,
  admin: flags.admin ?? false,
  visibleWhen: null,
  ...rest,
});

const opts = (start: number, labels: string[]): S["FormOption"][] =>
  labels.map((label, i) => ({ id: option(start + i), label }));

const MENTORED_BEFORE = opts(1, ["Yes", "No", "I am not sure"]);
const FOCUS_AREAS = opts(10, [
  "Backend fundamentals",
  "System design",
  "Testing",
  "Career direction",
  "Interview preparation",
  "Open source",
]);
const CADENCE = opts(20, ["Weekly", "Fortnightly", "Monthly"]);
const MENTOR_CAPACITY = opts(30, ["One mentee", "Two mentees", "Three mentees"]);

const menteeForm: S["FormVersion"] = {
  id: formVersion(1),
  programId: PROGRAM,
  role: "mentee",
  version: 3,
  publishedAt: daysAgo(45),
  sections: [
    {
      id: section(1),
      title: "About you",
      description: "The basics. Nothing here is scored.",
      fields: [
        f(1, "short_text", "What should we call you?", true, { admin: true }, {
          help: "The name your mentor will see.",
          text: { minLength: 2, maxLength: 80, placeholder: null },
        }),
        f(2, "short_text", "Where are you based?", true, { matching: true }, {
          help: "City and country is enough. We use it to find an overlapping working day.",
          text: { minLength: 2, maxLength: 80, placeholder: null },
        }),
        f(3, "date", "When would you like to start?", false, { admin: true }, {
          date: { min: "2026-09-01", max: "2026-12-31" },
        }),
      ],
    },
    {
      id: section(2),
      title: "Your background",
      description: null,
      fields: [
        f(4, "number", "How many years have you been writing code?", true, { equity: true }, {
          help: "Count anything, including learning on your own.",
          number: { min: 0, max: 40, step: 1, unit: "years" },
        }),
        f(5, "single_select", "Have you been mentored before?", true, { equity: true }, {
          options: MENTORED_BEFORE,
        }),
        // The conditional. Someone who has never had a mentor is exactly the
        // person whose answer needs drawing out, so the follow-up appears for
        // them rather than for everyone.
        f(6, "long_text", "What has been hardest to work out on your own?", true, { equity: true }, {
          help: "Two or three sentences. There is no right answer and this is not a test.",
          text: { minLength: 40, maxLength: 1200, placeholder: null },
          visibleWhen: {
            all: [
              { fieldId: field(5), operator: "equals", value: option(2) },
            ],
          },
        }),
        f(7, "multi_select", "What would you like to work on?", true, { matching: true }, {
          help: "Pick up to three.",
          options: FOCUS_AREAS,
          selection: { min: 1, max: 3 },
        }),
      ],
    },
    {
      id: section(3),
      title: "What you want from mentoring",
      description: null,
      fields: [
        f(8, "long_text", "What would make this six months worth it?", true, { matching: true, equity: true }, {
          help: "Say it in your own words. Plain is better than polished.",
          text: { minLength: 60, maxLength: 2000, placeholder: null },
        }),
        f(9, "scale", "How confident do you feel about your next career step?", true, { equity: true }, {
          scale: { min: 1, max: 5, minLabel: "Not at all", maxLabel: "Very" },
        }),
      ],
    },
    {
      id: section(4),
      title: "Practicalities",
      description: null,
      fields: [
        f(10, "single_select", "How often would you like to meet?", true, { matching: true }, {
          options: CADENCE,
        }),
        f(11, "file", "Attach a CV, if you have one", false, { admin: true }, {
          help: "PDF or Word, up to 5 MB. Not having one will not count against you.",
          file: {
            accept: ["application/pdf", "application/msword", ".docx"],
            maxSizeBytes: 5_242_880,
          },
        }),
      ],
    },
    {
      id: section(5),
      title: "Before you send this",
      description: null,
      fields: [
        f(12, "consent", "Sharing your answers with your mentor", true, { admin: true }, {
          consent: {
            statement:
              "I agree that my answers can be shown to the mentor I am matched with.",
            documentUrl: null,
          },
        }),
        f(13, "consent", "Reporting", false, { admin: true }, {
          consent: {
            statement:
              "I agree that anonymised answers can be used in the programme's public report.",
            documentUrl: null,
          },
        }),
      ],
    },
  ],
};

/** Mentors answer a different form. Architecture 5.4: separate per role. */
const mentorForm: S["FormVersion"] = {
  id: formVersion(2),
  programId: PROGRAM,
  role: "mentor",
  version: 2,
  publishedAt: daysAgo(45),
  sections: [
    {
      id: section(10),
      title: "About you",
      description: null,
      fields: [
        f(20, "short_text", "What should we call you?", true, { admin: true }, {
          text: { minLength: 2, maxLength: 80, placeholder: null },
        }),
        f(21, "short_text", "What do you do day to day?", true, { matching: true }, {
          help: "One line. It appears under your name in the directory.",
          text: { minLength: 2, maxLength: 120, placeholder: null },
        }),
      ],
    },
    {
      id: section(11),
      title: "How you can help",
      description: null,
      fields: [
        f(22, "multi_select", "What can you help someone with?", true, { matching: true }, {
          options: FOCUS_AREAS,
          selection: { min: 1, max: 6 },
        }),
        f(23, "single_select", "How many mentees can you take?", true, { admin: true }, {
          options: MENTOR_CAPACITY,
        }),
        f(24, "long_text", "What was your own path into this work?", false, { matching: true }, {
          help: "Mentees read this. Honest beats impressive.",
          text: { minLength: 0, maxLength: 2000, placeholder: null },
        }),
      ],
    },
    {
      id: section(12),
      title: "Before you send this",
      description: null,
      fields: [
        f(25, "consent", "Code of conduct", true, { admin: true }, {
          consent: {
            statement: "I have read the programme's code of conduct and agree to it.",
            documentUrl: null,
          },
        }),
      ],
    },
  ],
};

export const FORM_VERSIONS: S["FormVersion"][] = [menteeForm, mentorForm];

const member = (
  entry: S["RosterEntry"],
  skills: string[],
  headline: string,
): S["StrandMember"] => ({
  participationId: entry.id,
  name: entry.account.name,
  role: entry.role,
  headline,
  photoUrl: null,
  timezone: entry.timezone,
  skills,
});

/** The signed-in account: mentor with three strands, and coordinator on this
 *  program so every route in the slice is reachable from one session. */
const ME_INDEX = 0;
const me = mentorEntries[ME_INDEX];

const meMember = member(me, mentorSkills(0), MENTORS[0][5]);

type StrandSeed = {
  n: number;
  menteeIdx: number;
  lastActivityDaysAgo: number;
  unread: number;
  nextSessionInDays: number | null;
  /** Omitted means active. An ended strand needs `endedDaysAgo` with it. */
  state?: S["StrandState"];
  endedDaysAgo?: number;
  /** What the monitor reports. Sessions logged matter more than sessions
   *  scheduled, per architecture 4.7, so this is the engagement signal. */
  sessionsLogged?: number;
  milestonesCompleted?: number;
  messages: Array<[fromMe: boolean, daysAgo: number, body: string]>;
};

const STRAND_SEEDS: StrandSeed[] = [
  {
    n: 1,
    sessionsLogged: 4,
    milestonesCompleted: 2,
    menteeIdx: 0,
    lastActivityDaysAgo: 1,
    unread: 2,
    nextSessionInDays: 4,
    messages: [
      [false, 21, "Hello Amara, thank you for taking me on. I have been building a small expense tracker in Flask."],
      [true, 21, "Good to meet you Blessing. Send me the repository when you get a chance and I will read through it before we talk."],
      [false, 20, "Shared it now. The part I am least sure about is how I structured the database layer."],
      [true, 18, "I read it. The structure is reasonable. What I would change first is moving the queries out of the route handlers, so the routes only handle the request and response."],
      [false, 14, "That made a real difference. Routes are about ten lines each now."],
      [true, 7, "Good. Next thing worth learning is writing a test for one of those functions. Pick the one you were most nervous about changing."],
      [false, 2, "Wrote three tests. One of them caught a bug where I was not handling an empty result."],
      [false, 1, "Also wanted to ask about how you decided to move into payments work."],
    ],
  },
  {
    n: 2,
    sessionsLogged: 3,
    milestonesCompleted: 2,
    menteeIdx: 2,
    lastActivityDaysAgo: 5,
    unread: 0,
    nextSessionInDays: 11,
    messages: [
      [true, 19, "Hello Fatima. Before we meet, tell me what you are working on and what you would like to be doing in a year."],
      [false, 17, "I am learning Python on my own. In a year I want to be working as a backend engineer."],
      [true, 12, "That is a clear goal. Let us pick one project and take it further than feels comfortable, rather than starting several."],
      [false, 9, "Agreed. I will finish the library API I started."],
      [true, 5, "Send it over when the first endpoint works end to end."],
    ],
  },
  {
    n: 3,
    sessionsLogged: 1,
    milestonesCompleted: 0,
    menteeIdx: 8,
    lastActivityDaysAgo: 23,
    unread: 0,
    nextSessionInDays: null,
    messages: [
      [true, 25, "Hello Tobi, looking forward to working together. What would be most useful to start with?"],
      [false, 23, "Thank you. I will come back with something specific this week."],
    ],
  },
  {
    // Matched this morning, nothing written. The state the design file draws:
    // somebody is waiting on the other end and the screen has to say so.
    n: 5,
    sessionsLogged: 0,
    milestonesCompleted: 0,
    menteeIdx: 5,
    lastActivityDaysAgo: 0,
    unread: 0,
    nextSessionInDays: null,
    messages: [],
  },
  {
    n: 4,
    sessionsLogged: 6,
    milestonesCompleted: 3,
    menteeIdx: 4,
    lastActivityDaysAgo: 40,
    unread: 0,
    nextSessionInDays: null,
    state: "ended",
    endedDaysAgo: 38,
    messages: [
      [true, 70, "Hello Grace. You said Java and system design. Which of the two is closer to what you need this month?"],
      [false, 68, "System design. I can write Java but I freeze when someone asks me how I would build something."],
      [true, 60, "Then we will draw. Every session, one system on paper before any code."],
      [false, 44, "Drew the ticketing one on my own this week and it held together."],
      [true, 41, "That is the cohort finished. You came in unable to start a diagram and you are now finishing them unprompted. Keep drawing."],
      [false, 40, "Thank you Amara. I will."],
    ],
  },
];

function buildStrands() {
  const strands: S["Strand"][] = [];
  const summaries: S["StrandSummary"][] = [];
  const messages: Record<string, S["Message"][]> = {};
  /** Keyed by strand id. What the monitor reports and the thread cannot show. */
  const metrics: Record<string, { sessionsLogged: number; milestonesCompleted: number }> = {};

  for (const seed of STRAND_SEEDS) {
    const id = strand(seed.n);
    const menteeEntry = menteeEntries[seed.menteeIdx];
    const partner = member(
      menteeEntry,
      menteeSkills(seed.menteeIdx),
      MENTEES[seed.menteeIdx][5],
    );

    const thread: S["Message"][] = seed.messages.map(
      ([fromMe, ago, body], i) => ({
        id: message(seed.n * 100 + i + 1),
        strandId: id,
        author: fromMe
          ? { participationId: me.id, name: me.account.name, photoUrl: null }
          : {
              participationId: menteeEntry.id,
              name: menteeEntry.account.name,
              photoUrl: null,
            },
        body,
        sentAt: dayAt(ago, 8 + ((i * 5) % 11), (i * 17) % 60),
        deliveryState: "delivered",
        clientToken: null,
      }),
    );

    messages[id] = thread;
    const last = thread.length > 0 ? thread[thread.length - 1] : null;
    const state = seed.state ?? "active";
    const endedAt =
      seed.endedDaysAgo === undefined ? null : daysAgo(seed.endedDaysAgo);

    strands.push({
      id,
      programId: PROGRAM,
      state,
      originMode: "batch",
      members: [meMember, partner],
      matchRationale: `Matched on a shared focus in ${menteeSkills(seed.menteeIdx)[0]} and backend fundamentals, with a two-hour timezone overlap. This names the strongest signals; in a whole-cohort assignment the outcome also depends on who else was available.`,
      createdAt: daysAgo(
        seed.messages.length > 0
          ? Math.max(...seed.messages.map(([, ago]) => ago)) + 2
          : 0,
      ),
      endedAt,
    });

    metrics[id] = {
      sessionsLogged: seed.sessionsLogged ?? 0,
      milestonesCompleted: seed.milestonesCompleted ?? 0,
    };

    summaries.push({
      id,
      programId: PROGRAM,
      state,
      originMode: "batch",
      members: [partner],
      lastMessage: last
        ? { authorName: last.author.name, body: last.body, sentAt: last.sentAt }
        : null,
      lastActivityAt: daysAgo(seed.lastActivityDaysAgo),
      unreadCount: seed.unread,
      nextSessionAt:
        seed.nextSessionInDays === null
          ? null
          : daysAhead(seed.nextSessionInDays),
      endedAt,
    });
  }

  return { strands, summaries, messages, metrics };
}

export function createDb() {
  const { strands, summaries, messages, metrics } = buildStrands();

  const program: S["ProgramPublic"] = {
    id: PROGRAM,
    slug: PROGRAM_SLUG,
    name: "Backend mentoring, cohort 4",
    organisation,
    description:
      "A six-month structured mentoring programme pairing early-career backend engineers with senior engineers across Africa and the UK. Pairs meet twice a month and work towards one substantial project.",
    state: "open",
    cohortStart: "2026-09-14",
    cohortEnd: "2027-03-14",
    applicationsCloseAt: daysAhead(21),
    matchingOpensAt: daysAhead(37),
    timeCommitment: "About two hours a month for six months.",
    eligibility:
      "Open to women and non-binary engineers with less than three years of professional experience. Mentors need at least five years.",
    openRoles: ["mentee", "mentor"],
    mentorCount: MENTORS.length,
    menteeCount: MENTEES.length,
    // Capacity is the sum of what the mentors said they could take.
    capacity: MENTORS.reduce((n, [, , , cap]) => n + cap, 0),
    placesRemaining: Math.max(
      0,
      MENTORS.reduce((n, [, , , cap]) => n + cap, 0) - MENTEES.length,
    ),
  };

  /**
   * Architecture 4.1, composed for the screen. The signed-in account is a
   * mentor with three live strands and one that ended, so home renders in its
   * populated state; flip `strandCount` and the empty state takes over.
   */
  const home: S["HomeSummary"] = {
    matchingOpensAt: daysAhead(37),
    mentorCount: MENTORS.length,
    strandCount: 3,
    profileCompleteness: 0.85,
    nextAction: {
      kind: "log_session",
      title: "Log your session with Blessing",
      body: "You met on Tuesday. Two lines is enough, and it is what the report is built from.",
      actionLabel: "Log the session",
      href: `/strands/${uuid(8, 1)}`,
    },
    announcement: {
      id: uuid(14, 1),
      body: "Halfway check-ins open next week. If a strand has gone quiet, say so in yours — it is not a mark against anyone and it is the only way I can help.",
      authorName: "Amara Okonkwo",
      postedAt: daysAgo(3),
    },
    upcomingMilestone: {
      id: uuid(15, 1),
      title: "Agree a shared goal for the cohort",
      dueAt: daysAhead(9),
      completed: false,
    },
  };

  const runs: S["RunDetail"][] = [
    {
      id: uuid(6, 1),
      programId: PROGRAM,
      state: "published",
      progress: 1,
      recipeVersion: 2,
      createdAt: daysAgo(24),
      createdBy: "Amara Okonkwo",
      publishedAt: daysAgo(24),
      publishedBy: "Amara Okonkwo",
      draftedCount: 11,
      publishedCount: 11,
      coverageRate: 0.6875,
      fairnessSummary: null,
      pairs: [],
      unmatchedCount: 5,
    },
    {
      id: uuid(6, 2),
      programId: PROGRAM,
      state: "discarded",
      progress: 1,
      recipeVersion: 3,
      createdAt: daysAgo(10),
      createdBy: "Amara Okonkwo",
      publishedAt: null,
      publishedBy: null,
      draftedCount: 12,
      publishedCount: 0,
      coverageRate: 0.75,
      fairnessSummary: null,
      pairs: [],
      unmatchedCount: 4,
    },
    {
      id: uuid(6, 3),
      programId: PROGRAM,
      state: "drafted",
      progress: 1,
      recipeVersion: 4,
      createdAt: daysAgo(1),
      createdBy: "Amara Okonkwo",
      publishedAt: null,
      publishedBy: null,
      draftedCount: draftPairs.length,
      publishedCount: 0,
      coverageRate: fairnessSummary.coverageRate,
      fairnessSummary,
      pairs: draftPairs,
      unmatchedCount: fairnessSummary.unmatchedCount,
    },
  ];

  const applications: S["Application"][] = [
    {
      id: uuid(5, 1),
      programId: PROGRAM,
      programName: program.name,
      role: "mentee",
      name: "Halima Sani",
      email: "halima.sani@example.org",
      status: "submitted",
      submittedAt: daysAgo(2),
      editableUntil: daysAhead(21),
      matchingOpensAt: daysAhead(37),
      formVersionId: menteeForm.id,
      // Keyed by field id, never by label. Halima answered the conditional
      // follow-up, which is only asked of people who have not been mentored
      // before, and that answer is marked `guided` because it came out of the
      // elicitation prompt rather than the blank box.
      answers: {
        [field(1)]: answered("Halima", "self", 2),
        [field(2)]: answered("Kano, Nigeria", "self", 2),
        [field(4)]: answered(1, "self", 2),
        [field(5)]: answered(option(2), "self", 2),
        [field(6)]: answered(
          "Knowing whether the way I have built something is the normal way or just my way. I can make things work but I cannot tell if they are right.",
          "guided",
          2,
        ),
        [field(7)]: answered([option(10), option(12)], "self", 2),
        [field(8)]: answered(
          "I want to stop guessing. By the end I would like to have shipped one service that other people use and to understand why it is built the way it is.",
          "self",
          2,
        ),
        [field(9)]: answered(2, "self", 2),
        [field(10)]: answered(option(21), "self", 2),
        [field(12)]: answered(true, "self", 2),
      },
    },
  ];

  /**
   * The rest of the intake queue. Halima's application above carries a full
   * answer set because the detail screen reads one; these carry enough to be
   * reviewable and to give the queue every status it can hold.
   *
   * name, email, role, status, submitted days ago, answered field count
   */
  type AppSeed = [
    string,
    string,
    S["Role"],
    S["ApplicationStatus"],
    number,
    number,
  ];

  const APP_SEEDS: AppSeed[] = [
    ["Chiamaka Eze", "chiamaka.eze@example.org", "mentee", "submitted", 1, 9],
    ["Musa Danjuma", "musa.danjuma@example.org", "mentee", "submitted", 1, 5],
    ["Rita Nwachukwu", "rita.nwachukwu@example.org", "mentor", "submitted", 3, 8],
    ["Segun Adebayo", "segun.adebayo@example.org", "mentee", "under_review", 4, 10],
    ["Blessing Adewale", "blessing.adewale@example.org", "mentee", "approved", 19, 10],
    ["Ngozi Obi", "ngozi.obi@example.org", "mentee", "approved", 18, 10],
    ["Yusuf Ibrahim", "yusuf.ibrahim@example.org", "mentee", "waitlisted", 12, 4],
    ["Tunde Bakare", "tunde.bakare@example.org", "mentor", "approved", 40, 8],
    ["Idris Lawal", "idris.lawal@example.org", "mentee", "rejected", 25, 6],
  ];

  // The askable fields, in order, so a seed's "answered count" fills a
  // plausible prefix rather than a random scatter.
  const MENTEE_FIELDS = [1, 2, 4, 5, 6, 7, 8, 9, 10, 12];
  const MENTOR_FIELDS = [1, 2, 4, 5, 6, 7, 8, 12];

  const seededAnswers = (role: S["Role"], count: number, days: number) => {
    const ids = role === "mentor" ? MENTOR_FIELDS : MENTEE_FIELDS;
    const answers: Record<string, S["AnswerRecord"]> = {};
    for (const n of ids.slice(0, count)) {
      answers[field(n)] = answered("Answered", "self", days);
    }
    return answers;
  };

  const seededApplications: S["Application"][] = APP_SEEDS.map(
    ([name, email, role, status, days, answeredCount], i) => ({
      id: uuid(5, i + 2),
      programId: PROGRAM,
      programName: program.name,
      role,
      name,
      email,
      status,
      submittedAt: daysAgo(days),
      editableUntil: daysAhead(21),
      matchingOpensAt: daysAhead(37),
      formVersionId: role === "mentor" ? mentorForm.id : menteeForm.id,
      answers: seededAnswers(role, answeredCount, days),
    }),
  );

  applications.push(...seededApplications);

  /**
   * Everyone in the programme with no strand. Derived rather than written out,
   * so it cannot drift from the roster it is a view of: any mentee the run did
   * not place, plus any mentor holding nothing.
   *
   * The reasons are assigned per person because each one has a different
   * remedy, and a queue where every row says the same thing is a queue nobody
   * reads.
   */
  const REASONS: Record<string, S["UnmatchedReason"]> = {
    "Yusuf Ibrahim": "incomplete_profile",
    "Lerato Molefe": "no_mentor_capacity",
    "Samuel Adeyemi": "no_skill_overlap",
  };

  const unmatchedMentees = menteeEntries
    .filter((e) => !e.matched)
    .map((e) => ({
      participationId: e.id,
      name: e.account.name,
      email: e.account.email,
      role: e.role,
      reason: REASONS[e.account.name] ?? "no_mentor_capacity",
      profileCompleteness: e.profileCompleteness,
      timezone: e.timezone,
      skills: menteeSkills(MENTEES.findIndex((m) => m[0] === e.account.name)),
      joinedAt: e.joinedAt,
      lastRunId: uuid(6, 1),
    }));

  const unmatchedMentors = mentorEntries
    .filter((e) => (e.load ?? 0) === 0)
    .map((e) => ({
      participationId: e.id,
      name: e.account.name,
      email: e.account.email,
      role: e.role,
      reason: REASONS[e.account.name] ?? "no_skill_overlap",
      profileCompleteness: e.profileCompleteness,
      timezone: e.timezone,
      skills: mentorSkills(MENTORS.findIndex((m) => m[0] === e.account.name)),
      joinedAt: e.joinedAt,
      lastRunId: uuid(6, 1),
    }));

  const unmatched: S["UnmatchedEntry"][] = [
    ...unmatchedMentees,
    ...unmatchedMentors,
  ];

  /**
   * The arc from architecture 5.6: what should have happened by week two, week
   * six, week twelve. Each carries the prompt that appears inside strands when
   * it lands, which is what stops a milestone being a note in a coordinator's
   * calendar that nobody in the programme ever sees.
   */
  const milestones: S["ProgramMilestone"][] = [
    {
      id: uuid(13, 1),
      title: "First conversation",
      description:
        "Both sides have met once and agreed how often they will talk.",
      weekOffset: 2,
      strandPrompt:
        "Have you two managed a first conversation yet? Agreeing how often you will meet is most of the work.",
      reminderDaysBefore: 3,
      position: 1,
    },
    {
      id: uuid(13, 2),
      title: "Goals agreed",
      description: "The mentee has named what they want out of the six months.",
      weekOffset: 6,
      strandPrompt:
        "What does the mentee want to be able to do by the end? Write it down here, even roughly.",
      reminderDaysBefore: 7,
      position: 2,
    },
    {
      id: uuid(13, 3),
      title: "Halfway review",
      description: "A check that the pairing is working, while there is time to fix it.",
      weekOffset: 12,
      strandPrompt:
        "You are halfway. What has been useful, and what would you change for the second half?",
      reminderDaysBefore: 7,
      position: 3,
    },
  ];

  /**
   * Default wording, written to be sendable as-is. A coordinator who never
   * opens this page still sends something that reads like a person wrote it.
   */
  const DEFAULT_TEMPLATES: S["MessageTemplate"][] = [
    {
      kind: "welcome",
      subject: "You are in, {participant.firstName}",
      body: "Hello {participant.firstName},\n\nYou are on the roster for {programme.name} at {organisation.name}. Matching runs on {programme.matchingDate}, and you will hear from us either way that day.\n\nThere is nothing you need to do until then. If your profile is not finished, finishing it is the one thing that improves your match.",
      isDefault: true,
      updatedAt: null,
      updatedBy: null,
    },
    {
      kind: "match_notification",
      subject: "You have been matched with {partner.firstName}",
      body: "Hello {participant.firstName},\n\nYou have been matched with {partner.firstName} for {programme.name}.\n\nThe first conversation is the hardest one to arrange and the one that decides whether the rest happen. Open your strand and send them a message today if you can.",
      isDefault: true,
      updatedAt: null,
      updatedBy: null,
    },
    {
      kind: "nudge",
      subject: "It has been quiet in your strand",
      body: "Hello {participant.firstName},\n\nYou and {partner.firstName} have not spoken in a couple of weeks. That is normal and it is not a failure.\n\nIf the timing has stopped working, say so — rearranging is easier than starting again.",
      isDefault: true,
      updatedAt: null,
      updatedBy: null,
    },
    {
      kind: "mid_point_check_in",
      subject: "Halfway through {programme.name}",
      body: "Hello {participant.firstName},\n\nYou are halfway through {programme.name}. We ask everyone the same two questions at this point: what has been useful, and what would you change.\n\nIt takes two minutes and it is what tells us whether to change anything for the second half.",
      isDefault: true,
      updatedAt: null,
      updatedBy: null,
    },
    {
      kind: "closing",
      subject: "{programme.name} has finished",
      body: "Hello {participant.firstName},\n\n{programme.name} has come to an end. Thank you for the time you gave it.\n\nYour strand stays open to read back over. If you and {partner.firstName} want to keep talking, nothing here stops you.",
      isDefault: true,
      updatedAt: null,
      updatedBy: null,
    },
  ];

  const mergeCodes: S["MergeCode"][] = [
    {
      code: "participant.firstName",
      description: "The person being written to",
      sample: "Blessing",
    },
    {
      code: "partner.firstName",
      description: "The other side of their strand",
      sample: "Amara",
    },
    { code: "programme.name", description: "This programme", sample: program.name },
    {
      code: "organisation.name",
      description: "The host organisation",
      sample: organisation.name,
    },
    {
      code: "programme.matchingDate",
      description: "When matching runs",
      sample: "14 September",
    },
  ];

  /**
   * The recipe that produced the seeded run. Weights refer to published field
   * ids, so the criteria screen and the form builder are looking at the same
   * questions.
   */
  const recipe: S["MatchingRecipe"] = {
    name: "Cohort 4 recipe",
    version: 4,
    hardConstraints: [
      { kind: "role_compatible", enabled: true },
      { kind: "shared_skill", enabled: true },
      { kind: "same_timezone_band", enabled: false },
      { kind: "different_team", enabled: false },
    ],
    weights: [
      // Where they are based: overlapping working hours, so similar.
      { fieldId: field(2), weight: 40, direction: "similar" },
      // What they want to work on against what the mentor can help with: the
      // whole point is that the mentor knows what the mentee does not.
      { fieldId: field(7), weight: 90, direction: "complementary" },
      { fieldId: field(8), weight: 55, direction: "similar" },
      { fieldId: field(10), weight: 30, direction: "similar" },
      { fieldId: field(21), weight: 25, direction: "complementary" },
      { fieldId: field(22), weight: 85, direction: "complementary" },
      { fieldId: field(24), weight: 15, direction: "similar" },
    ],
    fairness: {
      mentorCapacityCap: null,
      coverageFloor: 0.8,
      priorityWeights: [
        { fieldId: field(4), weight: 60 },
        { fieldId: field(5), weight: 45 },
        { fieldId: field(9), weight: 35 },
      ],
    },
    updatedAt: daysAgo(9),
    updatedBy: "Amara Okonkwo",
  };

  const broadcasts: S["Broadcast"][] = [
    {
      id: uuid(14, 1),
      segment: "everyone",
      subject: "Matching runs on 14 September",
      body: "Hello {participant.firstName},\n\nMatching for {programme.name} runs on 14 September. If your profile is not finished, this week is the week.",
      recipientCount: 24,
      state: "sent",
      createdAt: daysAgo(12),
      createdBy: "Amara Okonkwo",
      scheduledFor: null,
      deliveredCount: 24,
      failedCount: 0,
    },
    {
      id: uuid(14, 2),
      segment: "incomplete_profiles",
      subject: "Ten minutes on your profile",
      body: "Hello {participant.firstName},\n\nYour profile is not finished, and matching works on what you tell us. Ten minutes now is the difference between a good match and a guess.",
      recipientCount: 6,
      state: "sent",
      createdAt: daysAgo(5),
      createdBy: "Amara Okonkwo",
      scheduledFor: null,
      deliveredCount: 5,
      failedCount: 1,
    },
  ];

  /**
   * The audit trail. Every entry is a deviation from, or a decision about, the
   * algorithm — which is what makes the fairness claim checkable by somebody
   * who was not in the room.
   */
  const auditEvents: S["AuditEvent"][] = [
    {
      id: uuid(15, 1),
      at: daysAgo(2),
      actorName: "Amara Okonkwo",
      action: "application_decided",
      summary: "Approved Halima Sani onto the roster as a mentee.",
      subjectLabel: "Halima Sani",
    },
    {
      id: uuid(15, 2),
      at: daysAgo(4),
      actorName: "Amara Okonkwo",
      action: "manual_pairing",
      summary:
        "Paired Joy Achieng with Priya Raghunathan by hand, outside the run.",
      subjectLabel: "Joy Achieng and Priya Raghunathan",
    },
    {
      id: uuid(15, 3),
      at: daysAgo(6),
      actorName: "Ngozi Adeyemi",
      action: "data_exported",
      summary: "Exported the roster as CSV, 24 rows including email addresses.",
      subjectLabel: "Roster export",
    },
    {
      id: uuid(15, 4),
      at: daysAgo(9),
      actorName: "Amara Okonkwo",
      action: "criteria_saved",
      summary:
        "Changed the matching recipe: raised the weight on what a mentee wants to work on from 70 to 90.",
      subjectLabel: "Cohort 4 recipe, version 4",
    },
    {
      id: uuid(15, 5),
      at: daysAgo(15),
      actorName: "Amara Okonkwo",
      action: "run_published",
      summary: "Published a run of 14 pairs. Two mentees were left unmatched.",
      subjectLabel: "Run of 24 July",
    },
    {
      id: uuid(15, 6),
      at: daysAgo(16),
      actorName: "Ngozi Adeyemi",
      action: "pair_overridden",
      summary:
        "Replaced the proposed mentor for Aisha Bello before publishing, from Samuel Adeyemi to Chidinma Eze.",
      subjectLabel: "Aisha Bello",
    },
    {
      id: uuid(15, 7),
      at: daysAgo(22),
      actorName: "Amara Okonkwo",
      action: "form_published",
      summary: "Published version 3 of the mentee form, adding two questions.",
      subjectLabel: "Mentee form, version 3",
    },
    {
      id: uuid(15, 8),
      at: daysAgo(30),
      actorName: "Ngozi Adeyemi",
      action: "participant_edited",
      summary:
        "Edited Fatima Yusuf's availability on her behalf, after she emailed asking.",
      subjectLabel: "Fatima Yusuf",
    },
  ];

  /**
   * The report. Coverage climbs as intake and matching proceed; sessions dip
   * over the December weeks, which is the shape every real programme has and
   * the thing a funder asks about.
   */
  const report: S["ProgramReport"] = {
    programName: program.name,
    from: "2026-06-01",
    to: "2026-08-08",
    coverageOverTime: [
      { date: "2026-06-08", value: 0 },
      { date: "2026-06-22", value: 0.12 },
      { date: "2026-07-06", value: 0.34 },
      { date: "2026-07-20", value: 0.63 },
      { date: "2026-08-03", value: 0.88 },
    ],
    mentorLoad: fairnessSummary.mentorLoad,
    qualityByBand: fairnessSummary.priorityBands,
    sessionsByWeek: [
      { label: "w/c 29 Jun", count: 2 },
      { label: "w/c 6 Jul", count: 6 },
      { label: "w/c 13 Jul", count: 9 },
      { label: "w/c 20 Jul", count: 7 },
      { label: "w/c 27 Jul", count: 11 },
      { label: "w/c 3 Aug", count: 8 },
    ],
    checkInSentiment: [
      { label: "1", count: 0 },
      { label: "2", count: 1 },
      { label: "3", count: 3 },
      { label: "4", count: 7 },
      { label: "5", count: 5 },
    ],
    checkInResponseRate: 0.64,
    milestoneCompletion: [
      { title: "First conversation", completed: 12, total: 14 },
      { title: "Goals agreed", completed: 8, total: 14 },
      { title: "Halfway review", completed: 3, total: 14 },
    ],
    dropOff: [
      { stage: "applied", count: 31 },
      { stage: "approved", count: 24 },
      { stage: "matched", count: 14 },
      { stage: "first_message", count: 13 },
      { stage: "first_session", count: 11 },
      { stage: "still_active", count: 10 },
    ],
    // Only questions participants agreed to share. The years-of-experience
    // band has a bucket of one, which is withheld rather than shown.
    demographics: [
      {
        fieldId: field(4),
        label: "Years writing code",
        buckets: [
          { label: "Under 1", count: 5 },
          { label: "1 to 2", count: 7 },
          { label: "3 to 5", count: 4 },
        ],
        suppressedBuckets: 1,
      },
      {
        fieldId: field(5),
        label: "Mentored before",
        buckets: [
          { label: "No", count: 11 },
          { label: "Yes", count: 5 },
        ],
        suppressedBuckets: 0,
      },
    ],
    suppressionThreshold: 3,
  };

  const resources: S["Resource"][] = [
    {
      id: uuid(16, 1),
      title: "Programme handbook",
      description:
        "How the six months are structured, what each milestone means, and who to ask when something is not working.",
      kind: "handbook",
      url: "/resources/handbook.pdf",
      sizeBytes: 1_240_000,
      updatedAt: daysAgo(30),
    },
    {
      id: uuid(16, 2),
      title: "What mentors are expected to do",
      description:
        "Two hours a month, and what those two hours should contain. Written to be read before the first conversation.",
      kind: "expectations",
      url: "/resources/mentor-expectations.pdf",
      sizeBytes: 320_000,
      updatedAt: daysAgo(30),
    },
    {
      id: uuid(16, 3),
      title: "What mentees are expected to do",
      description:
        "Turning up prepared, and what preparing actually means when you do not yet know what to ask.",
      kind: "expectations",
      url: "/resources/mentee-expectations.pdf",
      sizeBytes: 298_000,
      updatedAt: daysAgo(30),
    },
    {
      id: uuid(16, 4),
      title: "Conversation starters",
      description:
        "Thirty questions for when a session stalls. Most pairs use these twice and never need them again.",
      kind: "conversation_starters",
      url: "/resources/conversation-starters.pdf",
      sizeBytes: 180_000,
      updatedAt: daysAgo(21),
    },
    {
      id: uuid(16, 5),
      title: "Code of conduct",
      description:
        "What is expected of everyone here, and how to report something that is not right.",
      kind: "code_of_conduct",
      url: "/resources/code-of-conduct.pdf",
      sizeBytes: 96_000,
      updatedAt: daysAgo(60),
    },
  ];

  /**
   * The current account's own answers in this programme. Keyed by field id on
   * the mentor form, because the seeded session is a mentor here.
   */
  const myAnswers: Record<string, S["AnswerRecord"]> = {
    [field(20)]: answered("Amara", "self", 55),
    [field(21)]: answered(
      "I lead the payments platform team. Mostly Python and Django, and a lot of arguing about API design.",
      "self",
      55,
    ),
    // Focus areas: System design and Testing. Not the capacity options, which
    // start at 30 and belong to field 23.
    [field(22)]: answered([option(11), option(12)], "self", 55),
    // Flagged `admin` on the mentor form, so this must never reach a public
    // profile — the fixture carries one precisely so that can be checked.
    [field(23)]: answered(option(32), "self", 55),
    [field(24)]: answered(
      "I started as a self-taught developer writing PHP for a shop in Surulere. Nobody told me what a code review was for two years.",
      "self",
      55,
    ),
  };

  const notifications: S["NotificationPreferences"] = {
    newMessage: true,
    matchPublished: true,
    milestoneReminders: true,
    broadcasts: false,
    digest: "weekly",
  };

  /**
   * Invitations, one of each state worth building a screen for. The expired one
   * exists so the recovery path is reachable without waiting a fortnight.
   */
  const invites: S["Invite"][] = [
    {
      token: "invite-pending",
      state: "pending",
      email: "chiamaka.eze@example.org",
      organisationName: organisation.name,
      programName: program.name,
      orgSlug: ORG_SLUG,
      programSlug: PROGRAM_SLUG,
      role: "mentor",
      invitedByName: "Amara Okonkwo",
      message:
        "You mentored two people informally last year and both of them said it changed the year for them. Would you do it properly with us?",
      expiresAt: daysAhead(10),
      hasAccount: false,
    },
    {
      token: "invite-expired",
      state: "expired",
      email: "musa.danjuma@example.org",
      organisationName: organisation.name,
      programName: program.name,
      orgSlug: ORG_SLUG,
      programSlug: PROGRAM_SLUG,
      role: "mentee",
      invitedByName: "Ngozi Adeyemi",
      message: null,
      expiresAt: daysAgo(3),
      hasAccount: false,
    },
    {
      token: "invite-known",
      state: "pending",
      email: me.account.email,
      organisationName: "University of Lagos",
      programName: "Research writing, 2026",
      orgSlug: "unilag",
      programSlug: "research-writing-2026",
      role: "mentor",
      invitedByName: "Dr Kemi Balogun",
      message: null,
      expiresAt: daysAhead(21),
      // Already has an account, so accepting joins it rather than making a
      // second one under the same address.
      hasAccount: true,
    },
  ];

  const session: S["Session"] = {
    account: me.account,
    participations: [
      {
        id: me.id,
        programId: PROGRAM,
        programName: program.name,
        organisationName: organisation.name,
        orgSlug: ORG_SLUG,
        programSlug: PROGRAM_SLUG,
        role: "mentor",
        status: "approved",
        isCoordinator: true,
      },
      // Role lives on the participation, never the account: the same person is
      // a mentor here and a mentee elsewhere. Only the programme switcher and
      // the guards read this one — it has no roster, runs or strands behind it.
      {
        id: participation(900),
        programId: uuid(2, 2),
        programName: "Research writing, 2026",
        organisationName: "University of Lagos",
        orgSlug: "unilag",
        programSlug: "research-writing-2026",
        role: "mentee",
        status: "approved",
        isCoordinator: false,
      },
    ],
  };

  return {
    organisation,
    program,
    roster: [...mentorEntries, ...menteeEntries],
    runs,
    strands,
    strandSummaries: summaries,
    messages,
    applications,
    unmatched,
    milestones,
    recipe,
    broadcasts,
    auditEvents,
    report,
    resources,
    myAnswers,
    notifications,
    invites,
    /** Muted programmes, by participation id. */
    mutedParticipations: new Set<string>(),
    /** Architecture 4.9: the directory only exists when this is on. */
    selfMatchingEnabled: true,
    strandMetrics: metrics,
    /** Structured clone so resetting a template can restore untouched text. */
    templates: DEFAULT_TEMPLATES.map((t) => ({ ...t })),
    defaultTemplates: DEFAULT_TEMPLATES,
    mergeCodes,
    home,
    formVersions: FORM_VERSIONS,
    drafts: [] as S["ApplicationDraft"][],
    waitlist: [] as Array<{ email: string; role?: S["Role"] }>,
    session,
    /** Tokens handed out by POST /auth/magic-link, consumed by /auth/verify. */
    magicLinkTokens: new Set<string>(["valid-token"]),
    signedIn: true,
    seq: 1000,
  };
}

export type Db = ReturnType<typeof createDb>;

export let db: Db = createDb();

export function resetDb() {
  db = createDb();
}
