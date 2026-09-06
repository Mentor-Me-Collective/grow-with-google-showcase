import { HttpResponse, http } from "msw";
import type { components } from "../types";
import { ORG_SLUG, PROGRAM_ID, PROGRAM_SLUG, db } from "./fixtures";

type S = components["schemas"];

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/v1";
const url = (path: string) => `${BASE}${path}`;

const problem = (status: number, code: string, message: string) =>
  HttpResponse.json<S["Problem"]>({ code, message }, { status });

const unauthorized = () =>
  problem(401, "no_session", "Sign in to continue.");
const notFound = (what: string) =>
  problem(404, "not_found", `No such ${what}.`);

const requireSession = () => (db.signedIn ? null : unauthorized());

const nextId = (kind: number) =>
  `${String(kind).padStart(8, "0")}-0000-4000-8000-${String(++db.seq).padStart(12, "0")}`;

/**
 * Unread counts and read-only state come from the strands the account holds.
 * Only the seeded programme has any; the second participation is deliberately
 * bare, so the screen has to cope with a programme that has nothing behind it.
 */
function accountPrograms(): S["AccountProgram"][] {
  return db.session.participations.map((p) => {
    const mine = p.programId === PROGRAM_ID;
    const unread = mine
      ? db.strandSummaries.reduce((n, s) => n + s.unreadCount, 0)
      : 0;
    return {
      participationId: p.id,
      programId: p.programId,
      programName: p.programName,
      organisationName: p.organisationName ?? "",
      orgSlug: p.orgSlug,
      programSlug: p.programSlug,
      role: p.role,
      status: p.status,
      isCoordinator: p.isCoordinator ?? false,
      muted: db.mutedParticipations.has(p.id),
      unreadCount: unread,
      readOnly: mine ? db.program.state === "closed" : false,
    };
  });
}

const accountSettings = (): S["AccountSettings"] => ({
  account: db.session.account,
  notifications: db.notifications,
  programs: accountPrograms(),
});

/** The strand member record is where skills and headline already live. */
const memberFor = (participationId: string) =>
  db.strands
    .flatMap((s) => s.members)
    .find((m) => m.participationId === participationId);

const skillsFor = (entry: S["RosterEntry"]) =>
  memberFor(entry.id)?.skills ?? [];
const headlineFor = (entry: S["RosterEntry"]) =>
  memberFor(entry.id)?.headline ?? null;

/**
 * An answer thin enough that there is nothing to match on. Guided completion
 * exists for exactly these, so the profile screen names them rather than
 * showing a bare percentage.
 */
const THIN_TEXT_LENGTH = 40;

function isThin(field: S["FormField"], record: S["AnswerRecord"] | undefined) {
  if (!record) return true;
  const value = record.value;
  if (typeof value === "string") {
    return field.type === "long_text"
      ? value.trim().length < THIN_TEXT_LENGTH
      : value.trim().length === 0;
  }
  if (Array.isArray(value)) return value.length === 0;
  return value === null || value === undefined;
}

function myProfile(): S["ProfileView"] {
  const participation = db.session.participations[0];
  const version =
    publishedVersion(participation.role) ??
    db.formVersions.find((v) => v.role === participation.role)!;
  const fields = version.sections.flatMap((s) => s.fields);
  const answered = fields.filter((f) => !isThin(f, db.myAnswers[f.id]));
  const entry = db.roster.find((r) => r.id === participation.id);

  return {
    participationId: participation.id,
    name: db.session.account.name,
    role: participation.role,
    photoUrl: null,
    headline: entry ? headlineFor(entry) : null,
    timezone: entry?.timezone ?? null,
    completeness:
      fields.length === 0
        ? 1
        : Number((answered.length / fields.length).toFixed(3)),
    formVersion: version,
    answers: db.myAnswers,
    thinFieldIds: fields
      .filter((f) => isThin(f, db.myAnswers[f.id]))
      .map((f) => f.id),
  };
}

/**
 * The current account's answers, grouped and labelled, with `admin` questions
 * dropped. Those are collected for the coordinator and a profile screen is the
 * easiest place to leak them by accident.
 */
function shareableSections(): S["PublicProfileSection"][] {
  const participation = db.session.participations[0];
  const version =
    publishedVersion(participation.role) ??
    db.formVersions.find((v) => v.role === participation.role)!;

  const readable = (field: S["FormField"], record: S["AnswerRecord"]) => {
    const label = (id: string) =>
      field.options?.find((o) => o.id === id)?.label ?? id;
    const value = record.value;
    if (Array.isArray(value)) return value.map(label).join(", ");
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (typeof value === "string" && field.options) return label(value);
    return String(value);
  };

  return version.sections
    .map((section) => ({
      title: section.title,
      entries: section.fields
        .filter((f) => !f.admin)
        .flatMap((f) => {
          const record = db.myAnswers[f.id];
          if (!record) return [];
          return [{ label: f.label, value: readable(f, record) }];
        }),
    }))
    .filter((section) => section.entries.length > 0);
}

const SEGMENTS: S["BroadcastSegment"][] = [
  "everyone",
  "mentors",
  "mentees",
  "unmatched",
  "quiet_strands",
  "incomplete_profiles",
];

/** Sizes are counted now, from the same data the monitor reads. */
function segmentSize(segment: S["BroadcastSegment"]) {
  switch (segment) {
    case "everyone":
      return db.roster.length;
    case "mentors":
      return db.roster.filter((r) => r.role === "mentor").length;
    case "mentees":
      return db.roster.filter((r) => r.role === "mentee").length;
    case "unmatched":
      return db.unmatched.length;
    case "quiet_strands":
      return db.strandSummaries
        .map(toMonitorEntry)
        .filter(
          (e) =>
            e.state === "active" &&
            (e.health === "quiet" || e.health === "not_started"),
        )
        // Both sides of a quiet strand hear about it.
        .reduce((n, e) => n + e.members.length, 0);
    case "incomplete_profiles":
      return db.roster.filter((r) => r.profileCompleteness < 0.6).length;
  }
}

/** Questions on the live form carrying a given flag, for both roles. */
function publishedFields(
  predicate: (field: S["FormField"]) => boolean,
): S["CriteriaField"][] {
  const out: S["CriteriaField"][] = [];
  for (const role of ["mentee", "mentor"] as const) {
    const version = publishedVersion(role);
    if (!version) continue;
    for (const section of version.sections) {
      for (const field of section.fields) {
        if (!predicate(field)) continue;
        out.push({
          fieldId: field.id,
          label: field.label,
          role,
          type: field.type,
        });
      }
    }
  }
  return out;
}

function badRecipe(recipe: S["MatchingRecipeSave"]): string | null {
  if (!recipe?.name?.trim()) return "The recipe needs a name.";
  if (!Array.isArray(recipe.weights)) return "Send the whole recipe.";
  const floor = recipe.fairness?.coverageFloor;
  if (typeof floor !== "number" || floor < 0 || floor > 1) {
    return "The coverage floor is a share between 0 and 100 percent.";
  }
  if (recipe.weights.some((w) => w.weight < 0 || w.weight > 100)) {
    return "Weights run from 0 to 100.";
  }
  if (recipe.weights.every((w) => w.weight === 0)) {
    return "Every weight is zero, so nothing would score. Give at least one question some weight.";
  }
  return null;
}

/** The live form for a role: the newest published version, not merely a published one. */
const publishedVersion = (role: S["Role"]) =>
  db.formVersions
    .filter((v) => v.role === role && v.publishedAt !== null)
    .sort((a, b) => b.version - a.version)[0] ?? null;

/**
 * What would make a published form unusable to an applicant. Checked before
 * publishing rather than after, because the version that goes live is the one
 * strangers answer on a phone from a WhatsApp link.
 */
function unpublishable(draft: S["FormVersion"]): string | null {
  const fields = draft.sections.flatMap((s) => s.fields);
  if (fields.length === 0) {
    return "This form has no questions in it yet.";
  }
  const untitled = fields.find((f) => !f.label.trim());
  if (untitled) {
    return "Every question needs a label before this can go live.";
  }
  const emptySelect = fields.find(
    (f) =>
      (f.type === "single_select" || f.type === "multi_select") &&
      (f.options ?? []).length === 0,
  );
  if (emptySelect) {
    return `"${emptySelect.label}" is a choice question with nothing to choose from.`;
  }
  const untitledSection = draft.sections.find((s) => !s.title.trim());
  if (untitledSection) {
    return "Every section needs a title before this can go live.";
  }
  return null;
}

const DAY = 86_400_000;
/** 8.3 puts the quiet threshold at fourteen days. One definition, used here
 *  and on the participant's card, so the two cannot disagree. */
const QUIET_AFTER_DAYS = 14;

/**
 * Health is derived on every read, never stored. A quiet strand is one that has
 * not been written in — not one somebody flagged as quiet and forgot about.
 */
function healthOf(
  summary: S["StrandSummary"],
  daysSinceActivity: number | null,
  milestonesCompleted: number,
  milestonesTotal: number,
): S["StrandHealth"] {
  if (summary.state === "ended") return "ended";
  // Never begun is its own state: that pair needs an introduction, and a pair
  // who stopped after eight sessions needs a different conversation entirely.
  if (summary.lastMessage === null) return "not_started";
  if (daysSinceActivity !== null && daysSinceActivity >= QUIET_AFTER_DAYS) {
    return "quiet";
  }
  // Talking, but the arc has moved on without them.
  if (milestonesTotal > 0 && milestonesCompleted === 0) return "slow";
  return "on_track";
}

function toMonitorEntry(summary: S["StrandSummary"]): S["StrandMonitorEntry"] {
  const metrics = db.strandMetrics[summary.id] ?? {
    sessionsLogged: 0,
    milestonesCompleted: 0,
  };
  const milestonesTotal = db.milestones.length;
  const daysSinceActivity = summary.lastActivityAt
    ? Math.floor((Date.now() - new Date(summary.lastActivityAt).getTime()) / DAY)
    : null;

  // From the full strand, not the summary. A summary's members are "everyone
  // except the current account", which is right for a participant reading their
  // own strand and wrong here: a coordinator is not a party to most of these
  // and needs both names to know which pairing a row is.
  const full = db.strands.find((s) => s.id === summary.id);

  return {
    id: summary.id,
    state: summary.state,
    originMode: summary.originMode,
    members: full?.members ?? summary.members,
    daysSinceActivity,
    sessionsLogged: metrics.sessionsLogged,
    milestonesCompleted: metrics.milestonesCompleted,
    milestonesTotal,
    health: healthOf(
      summary,
      daysSinceActivity,
      metrics.milestonesCompleted,
      milestonesTotal,
    ),
  };
}

/** Week order, ties broken by position, so the arc always reads forwards. */
const orderedMilestones = () =>
  [...db.milestones].sort(
    (a, b) => a.weekOffset - b.weekOffset || a.position - b.position,
  );

/** Codes written as {like.this} that are not in the allowed list. */
function unknownCodes(text: string) {
  const allowed = new Set(db.mergeCodes.map((c) => c.code));
  const used = [...text.matchAll(/\{([^}]+)\}/g)].map((m) => m[1].trim());
  return [...new Set(used.filter((c) => !allowed.has(c)))];
}

const DECISION_STATUS: Record<string, S["ApplicationStatus"] | undefined> = {
  approve: "approved",
  waitlist: "waitlisted",
  reject: "rejected",
};

/** One way in this slice. Nothing un-decides an application. */
const DECIDED = new Set<S["ApplicationStatus"]>([
  "approved",
  "waitlisted",
  "rejected",
]);

/**
 * Completeness is answered over askable, for the version actually answered.
 * Computed rather than stored so it cannot disagree with the answers beside it.
 */
function completenessOf(application: S["Application"]) {
  const version = db.formVersions.find(
    (v) => v.id === application.formVersionId,
  );
  const askable = version
    ? version.sections.flatMap((s) => s.fields).length
    : Object.keys(application.answers).length;
  if (askable === 0) return 1;
  return Number(
    (Object.keys(application.answers).length / askable).toFixed(3),
  );
}

function flagsOf(application: S["Application"]): S["ApplicationFlag"][] {
  const flags: S["ApplicationFlag"][] = [];
  if (completenessOf(application) < 0.6) flags.push("incomplete");
  if (
    db.applications.some(
      (a) => a.id !== application.id && a.email === application.email,
    )
  ) {
    flags.push("duplicate_email");
  }
  if (db.roster.some((r) => r.account.email === application.email)) {
    flags.push("reapplied");
  }
  return flags;
}

const toSummary = (a: S["Application"]): S["ApplicationSummary"] => ({
  id: a.id,
  programId: a.programId,
  role: a.role,
  name: a.name,
  email: a.email,
  status: a.status,
  submittedAt: a.submittedAt,
  decidedAt: a.decidedAt ?? null,
  decidedBy: a.decidedBy ?? null,
  completeness: completenessOf(a),
  flags: flagsOf(a),
});

/**
 * Approving is the only decision that changes anything beyond the application:
 * it puts a person on the roster, which is the whole point of the queue.
 */
function decide(
  application: S["Application"],
  status: S["ApplicationStatus"],
) {
  application.status = status;
  application.decidedAt = new Date().toISOString();
  application.decidedBy = db.session.account.name;

  if (status !== "approved") return;
  if (db.roster.some((r) => r.account.email === application.email)) return;

  db.roster.push({
    id: nextId(4),
    account: {
      id: nextId(3),
      name: application.name,
      email: application.email,
      emailVerified: true,
      photoUrl: null,
    },
    role: application.role,
    status: "approved",
    matched: false,
    capacity: application.role === "mentor" ? 2 : null,
    load: application.role === "mentor" ? 0 : null,
    profileCompleteness: completenessOf(application),
    timezone: null,
    joinedAt: new Date().toISOString(),
  });
}

/** Runs advance one step per read, so polling has something to observe. */
const RUN_STEPS = [0.15, 0.45, 0.8, 1];

function advanceRun(run: S["RunDetail"]) {
  if (run.state !== "queued" && run.state !== "running") return;
  const i = RUN_STEPS.indexOf(run.progress);
  const next = RUN_STEPS[i + 1] ?? 1;
  run.progress = next;
  run.state = next < 1 ? "running" : "drafted";

  if (run.state === "drafted") {
    const template = db.runs.find((r) => r.fairnessSummary !== null);
    if (template) {
      run.fairnessSummary = template.fairnessSummary;
      run.pairs = template.pairs;
      run.draftedCount = template.pairs.length;
      run.unmatchedCount = template.unmatchedCount;
      run.coverageRate = template.coverageRate;
    }
  }
}

export const handlers = [
  http.get(url("/orgs/:orgSlug/programs/:programSlug"), ({ params }) => {
    if (params.orgSlug !== ORG_SLUG || params.programSlug !== PROGRAM_SLUG) {
      return notFound("program");
    }
    return HttpResponse.json(db.program);
  }),

  http.get(
    url("/orgs/:orgSlug/programs/:programSlug/form-schema"),
    ({ params, request }) => {
      if (params.orgSlug !== ORG_SLUG || params.programSlug !== PROGRAM_SLUG) {
        return notFound("program");
      }
      const role = new URL(request.url).searchParams.get("role");
      // The newest published version, not merely a published one. `find` here
      // returned whichever was seeded first, so publishing a new version left
      // applicants answering the old questions.
      const found =
        role === "mentee" || role === "mentor" ? publishedVersion(role) : null;
      return found
        ? HttpResponse.json(found)
        : problem(
            404,
            "no_published_form",
            "This programme has no published form for that role yet.",
          );
    },
  ),

  http.post(
    url("/orgs/:orgSlug/programs/:programSlug/waitlist"),
    async ({ params, request }) => {
      if (params.orgSlug !== ORG_SLUG || params.programSlug !== PROGRAM_SLUG) {
        return notFound("program");
      }
      const body = (await request.json()) as { email?: string; role?: S["Role"] };
      if (!body?.email?.includes("@")) {
        return problem(400, "invalid_email", "Enter a valid email address.");
      }
      db.waitlist.push({ email: body.email, role: body.role });
      return new HttpResponse(null, { status: 202 });
    },
  ),

  http.get(
    url("/orgs/:orgSlug/programs/:programSlug/application-draft"),
    ({ params, request }) => {
      if (params.orgSlug !== ORG_SLUG || params.programSlug !== PROGRAM_SLUG) {
        return notFound("program");
      }
      const draftId = new URL(request.url).searchParams.get("draftId");
      const found = db.drafts.find((d) => d.draftId === draftId);
      return found ? HttpResponse.json(found) : notFound("draft");
    },
  ),

  http.put(
    url("/orgs/:orgSlug/programs/:programSlug/application-draft"),
    async ({ params, request }) => {
      if (params.orgSlug !== ORG_SLUG || params.programSlug !== PROGRAM_SLUG) {
        return notFound("program");
      }
      if (db.program.state === "closed" || db.program.state === "full") {
        return problem(409, "applications_closed", "Applications have closed for this programme.");
      }
      const body = (await request.json()) as S["ApplicationDraftSave"];
      const now = new Date().toISOString();
      const answers: S["ApplicationDraft"]["answers"] = {};
      for (const [fieldId, answer] of Object.entries(body.answers ?? {})) {
        answers[fieldId] = { ...answer, answeredAt: now };
      }

      const existing = db.drafts.find((d) => d.draftId === body.draftId);
      if (existing) {
        existing.answers = answers;
        existing.savedAt = now;
        return HttpResponse.json(existing);
      }

      const created: S["ApplicationDraft"] = {
        draftId: nextId(13),
        role: body.role,
        formVersionId: body.formVersionId,
        answers,
        savedAt: now,
      };
      db.drafts.push(created);
      return HttpResponse.json(created);
    },
  ),

  http.post(
    url("/orgs/:orgSlug/programs/:programSlug/applications"),
    async ({ params, request }) => {
      if (params.orgSlug !== ORG_SLUG || params.programSlug !== PROGRAM_SLUG) {
        return notFound("program");
      }
      const body = (await request.json()) as S["ApplicationCreate"];
      if (!body?.email || !body?.name || !body?.role) {
        return problem(400, "invalid_body", "Name, email and role are required.");
      }
      if (db.program.state === "closed") {
        return problem(409, "applications_closed", "Applications have closed for this programme.");
      }
      if (db.applications.some((a) => a.email === body.email)) {
        return problem(409, "already_applied", "An application already exists for this email address.");
      }
      const version = db.formVersions.find((v) => v.id === body.formVersionId);
      if (!version || version.role !== body.role) {
        return problem(
          409,
          "stale_form_version",
          "The form has changed since you started. Reload to see the current questions.",
        );
      }

      // The client asserts provenance; the server owns the clock.
      const now = new Date().toISOString();
      const answers: S["Application"]["answers"] = {};
      for (const [fieldId, answer] of Object.entries(body.answers ?? {})) {
        answers[fieldId] = { ...answer, answeredAt: now };
      }

      const created: S["Application"] = {
        id: nextId(5),
        programId: PROGRAM_ID,
        programName: db.program.name,
        role: body.role,
        name: body.name,
        email: body.email,
        status: "submitted",
        submittedAt: new Date().toISOString(),
        editableUntil: db.program.applicationsCloseAt,
        matchingOpensAt: db.program.matchingOpensAt,
        formVersionId: version.id,
        answers,
      };
      db.applications.push(created);
      return HttpResponse.json(created, { status: 201 });
    },
  ),

  http.get(url("/applications/:applicationId"), ({ params }) => {
    const found = db.applications.find((a) => a.id === params.applicationId);
    return found ? HttpResponse.json(found) : notFound("application");
  }),

  http.post(url("/auth/magic-link"), async ({ request }) => {
    const body = (await request.json()) as S["MagicLinkRequest"];
    if (!body?.email?.includes("@")) {
      return problem(400, "invalid_email", "Enter a valid email address.");
    }
    // Issued only for known accounts, but the response never reveals which.
    const known = db.roster.some((r) => r.account.email === body.email);
    if (known) db.magicLinkTokens.add(`token-for-${body.email}`);
    return new HttpResponse(null, { status: 202 });
  }),

  http.post(url("/auth/verify"), async ({ request }) => {
    const body = (await request.json()) as S["VerifyRequest"];
    if (!body?.token) {
      return problem(400, "invalid_body", "A token is required.");
    }
    if (!db.magicLinkTokens.has(body.token)) {
      return problem(410, "token_spent", "That link has expired or was already used.");
    }
    db.magicLinkTokens.delete(body.token);
    db.signedIn = true;
    return HttpResponse.json(db.session, {
      status: 200,
      headers: {
        "Set-Cookie": "braid_session=mock; HttpOnly; SameSite=Lax; Path=/",
      },
    });
  }),

  http.post(url("/auth/signout"), () => {
    db.signedIn = false;
    return new HttpResponse(null, {
      status: 204,
      headers: {
        "Set-Cookie":
          "braid_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0",
      },
    });
  }),

  http.get(url("/auth/session"), () => {
    return db.signedIn ? HttpResponse.json(db.session) : unauthorized();
  }),

  http.get(url("/programs/:programId/home"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("program");
    return HttpResponse.json(db.home);
  }),

  http.get(url("/programs/:programId/roster"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const q = new URL(request.url).searchParams;
    const role = q.get("role");
    const status = q.get("status");
    const matched = q.get("matched");
    const page = Number(q.get("page") ?? 1);
    const pageSize = Number(q.get("pageSize") ?? 25);

    const filtered = db.roster.filter(
      (r) =>
        (!role || r.role === role) &&
        (!status || r.status === status) &&
        (matched === null || r.matched === (matched === "true")),
    );

    const body: S["RosterPage"] = {
      items: filtered.slice((page - 1) * pageSize, page * pageSize),
      page,
      pageSize,
      total: filtered.length,
    };
    return HttpResponse.json(body);
  }),

  http.get(url("/programs/:programId/dashboard"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const monitor = db.strandSummaries.map(toMonitorEntry);
    const active = monitor.filter((m) => m.state === "active");
    // Kept apart on purpose. A pair who stopped needs a nudge; a pair who never
    // began needs an introduction, and calling both "quiet" hides that.
    const quiet = active.filter((m) => m.health === "quiet");
    const neverStarted = active.filter((m) => m.health === "not_started");

    const waiting = db.applications.filter((a) => a.status === "submitted").length;
    const overCapacity = db.roster.filter(
      (r) =>
        r.role === "mentor" &&
        r.capacity !== null &&
        r.capacity !== undefined &&
        (r.load ?? 0) > r.capacity,
    ).length;
    const incomplete = db.roster.filter(
      (r) => r.status === "approved" && r.profileCompleteness < 0.6,
    ).length;

    /**
     * Ordered by what it costs to leave alone, not by count. An application
     * nobody reads stops a person joining at all; an incomplete profile only
     * makes a match worse.
     */
    const attention: S["AttentionItem"][] = [];

    if (waiting > 0) {
      attention.push({
        kind: "applications_waiting",
        count: waiting,
        title: `${waiting} ${waiting === 1 ? "application is" : "applications are"} waiting to be read`,
        body: "Nobody joins the roster until these are decided.",
        actionLabel: "Read them",
        href: "/applications",
      });
    }
    if (db.unmatched.length > 0) {
      attention.push({
        kind: "unmatched_people",
        count: db.unmatched.length,
        title: `${db.unmatched.length} ${db.unmatched.length === 1 ? "person has" : "people have"} no strand`,
        body: "Each one has a reason, and the reasons need different things.",
        actionLabel: "Open the queue",
        href: "/unmatched",
      });
    }
    if (neverStarted.length > 0) {
      attention.push({
        kind: "strands_never_started",
        count: neverStarted.length,
        title: `${neverStarted.length} ${neverStarted.length === 1 ? "strand has" : "strands have"} never started`,
        body: "Matched, but nobody has written anything yet. The first message is the one that decides whether the rest happen.",
        actionLabel: "See which",
        href: "/strands?health=not_started",
      });
    }
    if (quiet.length > 0) {
      attention.push({
        kind: "quiet_strands",
        count: quiet.length,
        title: `${quiet.length} ${quiet.length === 1 ? "strand has" : "strands have"} gone quiet`,
        body: "A fortnight without a message. A nudge is usually enough.",
        actionLabel: "See which",
        href: "/strands?health=quiet",
      });
    }
    if (overCapacity > 0) {
      attention.push({
        kind: "mentors_over_capacity",
        count: overCapacity,
        title: `${overCapacity} ${overCapacity === 1 ? "mentor is" : "mentors are"} over the capacity they set`,
        body: "They agreed to fewer mentees than they now hold.",
        actionLabel: "Open the roster",
        href: "/roster",
      });
    }
    if (incomplete > 0) {
      attention.push({
        kind: "incomplete_profiles",
        count: incomplete,
        title: `${incomplete} ${incomplete === 1 ? "profile is" : "profiles are"} too thin to match well`,
        body: "Matching works on what people tell us. These need a nudge, not a decision.",
        actionLabel: "Open the roster",
        href: "/roster",
      });
    }

    const body: S["DashboardSummary"] = {
      mentorCount: db.roster.filter((r) => r.role === "mentor").length,
      menteeCount: db.roster.filter((r) => r.role === "mentee").length,
      recruitmentGoal: 20,
      matchedCount: db.roster.filter((r) => r.role === "mentee" && r.matched).length,
      unmatchedCount: db.unmatched.length,
      activeStrands: active.length,
      quietStrands: quiet.length,
      sessionsLoggedThisWeek: Object.values(db.strandMetrics).reduce(
        (n, m) => n + (m.sessionsLogged > 0 ? 1 : 0),
        0,
      ),
      upcomingMilestone: db.home.upcomingMilestone ?? null,
      attention,
    };
    return HttpResponse.json(body);
  }),

  http.get(url("/programs/:programId/strand-monitor"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const q = new URL(request.url).searchParams;
    const health = q.get("health");
    const page = Number(q.get("page") ?? 1);
    const pageSize = Number(q.get("pageSize") ?? 25);

    const all = db.strandSummaries.map(toMonitorEntry);
    const filtered = all.filter((e) => !health || e.health === health);

    const body: S["StrandMonitorPage"] = {
      items: filtered.slice((page - 1) * pageSize, page * pageSize),
      page,
      pageSize,
      total: filtered.length,
      healthCounts: {
        on_track: all.filter((e) => e.health === "on_track").length,
        slow: all.filter((e) => e.health === "slow").length,
        quiet: all.filter((e) => e.health === "quiet").length,
        not_started: all.filter((e) => e.health === "not_started").length,
        ended: all.filter((e) => e.health === "ended").length,
      },
    };
    return HttpResponse.json(body);
  }),

  http.post(url("/strands/:strandId/nudge"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;

    const summary = db.strandSummaries.find((s) => s.id === params.strandId);
    if (!summary) return notFound("strand");
    if (summary.state === "ended") {
      return problem(409, "strand_ended", "This strand has ended. There is nobody to nudge.");
    }

    const result: S["NudgeResult"] = { sentTo: summary.members.length + 1 };
    return HttpResponse.json(result, { status: 202 });
  }),

  http.put(url("/strands/:strandId/state"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;

    const full = db.strands.find((s) => s.id === params.strandId);
    const summary = db.strandSummaries.find((s) => s.id === params.strandId);
    if (!full || !summary) return notFound("strand");

    const body = (await request.json()) as S["StrandStateChange"];
    const next = body?.state;
    if (next !== "active" && next !== "paused" && next !== "ended") {
      return problem(400, "invalid_state", "Choose active, paused or ended.");
    }
    if (full.state === "ended") {
      return problem(409, "already_ended", "This strand has already ended.");
    }

    full.state = next;
    summary.state = next;
    const endedAt = next === "ended" ? new Date().toISOString() : null;
    full.endedAt = endedAt;
    summary.endedAt = endedAt;

    return HttpResponse.json(full);
  }),

  http.get(url("/account/settings"), () => {
    const denied = requireSession();
    if (denied) return denied;
    return HttpResponse.json(accountSettings());
  }),

  http.put(url("/account/settings"), async ({ request }) => {
    const denied = requireSession();
    if (denied) return denied;

    const body = (await request.json()) as S["AccountSettingsSave"];
    if (body?.name !== undefined) {
      if (!body.name.trim()) {
        return problem(400, "invalid_name", "Your name cannot be empty.");
      }
      db.session.account.name = body.name.trim();
    }
    if (body?.notifications) {
      db.notifications = body.notifications;
    }
    return HttpResponse.json(accountSettings());
  }),

  http.get(url("/account/programs"), () => {
    const denied = requireSession();
    if (denied) return denied;
    return HttpResponse.json(accountPrograms());
  }),

  http.put(url("/participations/:participationId/mute"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;

    const id = String(params.participationId);
    if (!db.session.participations.some((p) => p.id === id)) {
      return notFound("programme");
    }

    const body = (await request.json()) as S["MuteChange"];
    if (body?.muted) db.mutedParticipations.add(id);
    else db.mutedParticipations.delete(id);

    const updated = accountPrograms().find((p) => p.participationId === id);
    return updated ? HttpResponse.json(updated) : notFound("programme");
  }),

  http.post(url("/participations/:participationId/leave"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;

    const id = String(params.participationId);
    const participation = db.session.participations.find((p) => p.id === id);
    if (!participation) return notFound("programme");

    if (participation.isCoordinator) {
      return problem(
        409,
        "coordinator_cannot_leave",
        "You coordinate this programme. Hand it over to somebody else first.",
      );
    }

    db.session.participations = db.session.participations.filter(
      (p) => p.id !== id,
    );
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(url("/invites/:token"), ({ params }) => {
    const invite = db.invites.find((i) => i.token === params.token);
    return invite ? HttpResponse.json(invite) : notFound("invitation");
  }),

  http.post(url("/invites/:token"), async ({ params, request }) => {
    const invite = db.invites.find((i) => i.token === params.token);
    if (!invite) return notFound("invitation");

    if (invite.state !== "pending") {
      return problem(
        410,
        "invite_spent",
        invite.state === "expired"
          ? "That invitation has expired."
          : "That invitation has already been answered.",
      );
    }

    const body = (await request.json()) as S["InviteResponse"];
    if (!body?.accept) {
      invite.state = "declined";
      return new HttpResponse(null, { status: 204 });
    }

    if (!invite.hasAccount && !body.name?.trim()) {
      return problem(400, "name_required", "Tell us what to call you.");
    }

    invite.state = "accepted";
    db.signedIn = true;
    if (!invite.hasAccount && body.name) {
      db.session.account.name = body.name.trim();
    }

    // The invitation becomes a participation, which is what makes the
    // programme reachable the moment they land in it.
    if (!db.session.participations.some((p) => p.programSlug === invite.programSlug)) {
      db.session.participations.push({
        id: nextId(4),
        programId: nextId(2),
        programName: invite.programName,
        organisationName: invite.organisationName,
        orgSlug: invite.orgSlug,
        programSlug: invite.programSlug,
        role: invite.role,
        status: "approved",
        isCoordinator: false,
      });
    }

    const accepted: S["InviteAccepted"] = {
      session: db.session,
      orgSlug: invite.orgSlug,
      programSlug: invite.programSlug,
    };
    return HttpResponse.json(accepted, {
      headers: {
        "Set-Cookie": "braid_session=mock; HttpOnly; SameSite=Lax; Path=/",
      },
    });
  }),

  http.post(url("/invites/:token/reissue"), ({ params }) => {
    const invite = db.invites.find((i) => i.token === params.token);
    if (!invite) return notFound("invitation");
    return new HttpResponse(null, { status: 202 });
  }),

  http.get(url("/programs/:programId/me"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");
    return HttpResponse.json(myProfile());
  }),

  http.put(url("/programs/:programId/me"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const body = (await request.json()) as S["ProfileSave"];
    if (!body?.answers || typeof body.answers !== "object") {
      return problem(400, "invalid_body", "Send the answers being saved.");
    }

    // Merged, not replaced: a per-section save must not blank the sections
    // that were never on screen.
    const now = new Date().toISOString();
    for (const [fieldId, answer] of Object.entries(body.answers)) {
      db.myAnswers[fieldId] = { ...answer, answeredAt: now };
    }

    return HttpResponse.json(myProfile());
  }),

  http.get(url("/programs/:programId/directory"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const q = new URL(request.url).searchParams;
    const term = (q.get("q") ?? "").trim().toLowerCase();
    const skill = q.get("skill");
    const page = Number(q.get("page") ?? 1);
    const pageSize = Number(q.get("pageSize") ?? 25);

    // The opposite role: the seeded account is a mentor, so it browses mentees.
    const myRole = db.session.participations[0]?.role ?? "mentor";
    const wanted = myRole === "mentor" ? "mentee" : "mentor";

    const entries: S["DirectoryEntry"][] = db.roster
      .filter((r) => r.role === wanted && r.status === "approved")
      .map((r) => {
        const skills = skillsFor(r);
        const full =
          r.capacity !== null &&
          r.capacity !== undefined &&
          (r.load ?? 0) >= r.capacity;
        return {
          participationId: r.id,
          name: r.account.name,
          photoUrl: null,
          headline: headlineFor(r),
          role: r.role,
          timezone: r.timezone,
          skills,
          available: !full,
          unavailableReason: full
            ? "Already mentoring as many people as they agreed to"
            : null,
        };
      });

    const filtered = entries.filter((e) => {
      if (skill && !e.skills.includes(skill)) return false;
      if (!term) return true;
      return (
        e.name.toLowerCase().includes(term) ||
        (e.headline ?? "").toLowerCase().includes(term) ||
        e.skills.some((s) => s.toLowerCase().includes(term))
      );
    });

    const body: S["DirectoryPage"] = {
      items: filtered.slice((page - 1) * pageSize, page * pageSize),
      page,
      pageSize,
      total: filtered.length,
      selfMatchingEnabled: db.selfMatchingEnabled,
      skills: [...new Set(entries.flatMap((e) => e.skills))].sort(),
    };
    return HttpResponse.json(body);
  }),

  http.get(url("/participations/:participationId/profile"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;

    const entry = db.roster.find((r) => r.id === params.participationId);
    if (!entry) return notFound("participant");

    const full =
      entry.capacity !== null &&
      entry.capacity !== undefined &&
      (entry.load ?? 0) >= entry.capacity;

    const body: S["PublicProfile"] = {
      participationId: entry.id,
      name: entry.account.name,
      role: entry.role,
      photoUrl: null,
      headline: headlineFor(entry),
      timezone: entry.timezone,
      skills: skillsFor(entry),
      available: !full,
      capacity: entry.capacity ?? null,
      load: entry.load ?? null,
      // Only the current account has stored answers in this mock, so a public
      // profile shows the shareable shape without inventing words for someone.
      sections:
        entry.id === db.session.participations[0]?.id
          ? shareableSections()
          : [],
    };
    return HttpResponse.json(body);
  }),

  http.get(url("/programs/:programId/resources"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");
    return HttpResponse.json(db.resources);
  }),

  http.get(url("/programs/:programId/report"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const q = new URL(request.url).searchParams;
    const from = q.get("from");
    const to = q.get("to");

    // The range narrows the series rather than regenerating them, which is
    // what a real query would do and keeps the totals honest against it.
    const within = (date: string) =>
      (!from || date >= from) && (!to || date <= to);

    const body: S["ProgramReport"] = {
      ...db.report,
      from: from ?? db.report.from,
      to: to ?? db.report.to,
      coverageOverTime: db.report.coverageOverTime.filter((p) =>
        within(p.date),
      ),
    };
    return HttpResponse.json(body);
  }),

  http.get(url("/orgs/:orgSlug/audit"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.orgSlug !== ORG_SLUG) return notFound("organisation");

    const q = new URL(request.url).searchParams;
    const actor = q.get("actor");
    const action = q.get("action");
    const from = q.get("from");
    const to = q.get("to");
    const page = Number(q.get("page") ?? 1);
    const pageSize = Number(q.get("pageSize") ?? 50);

    const filtered = db.auditEvents.filter((e) => {
      if (actor && e.actorName !== actor) return false;
      if (action && e.action !== action) return false;
      const day = e.at.slice(0, 10);
      if (from && day < from) return false;
      if (to && day > to) return false;
      return true;
    });

    const ordered = [...filtered].sort((a, b) => b.at.localeCompare(a.at));

    const body: S["AuditPage"] = {
      items: ordered.slice((page - 1) * pageSize, page * pageSize),
      page,
      pageSize,
      total: ordered.length,
      // Every actor in the whole log, not just this page, or the filter would
      // lose the option that produced the current view.
      actors: [...new Set(db.auditEvents.map((e) => e.actorName))].sort(),
    };
    return HttpResponse.json(body);
  }),

  http.get(url("/programs/:programId/criteria"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const body: S["CriteriaEditorState"] = {
      recipe: db.recipe,
      matchingFields: publishedFields((f) => f.matching),
      equityFields: publishedFields((f) => f.equity),
    };
    return HttpResponse.json(body);
  }),

  http.put(url("/programs/:programId/criteria"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const body = (await request.json()) as S["MatchingRecipeSave"];
    const complaint = badRecipe(body);
    if (complaint) return problem(400, "invalid_recipe", complaint);

    db.recipe = {
      ...db.recipe,
      name: body.name.trim(),
      version: db.recipe.version + 1,
      hardConstraints: body.hardConstraints,
      weights: body.weights,
      fairness: body.fairness,
      updatedAt: new Date().toISOString(),
      updatedBy: db.session.account.name,
    };
    return HttpResponse.json(db.recipe);
  }),

  http.post(url("/programs/:programId/criteria/test-run"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const body = (await request.json()) as S["MatchingRecipeSave"];
    const complaint = badRecipe(body);
    if (complaint) return problem(400, "invalid_recipe", complaint);

    /**
     * The fairness summary and nothing else. No pairs leave this endpoint, per
     * 5.5 — tuning weights while watching individual matches is how a cohort
     * gets optimised for one person.
     *
     * The mock moves coverage with the recipe so the screen has something
     * honest to show: more hard constraints shrink the pool, and a heavier
     * priority weight lifts the low band at the top band's expense.
     */
    const template = db.runs.find((r) => r.fairnessSummary !== null);
    const base = template?.fairnessSummary;
    if (!base) return notFound("fairness summary");

    const constraints = body.hardConstraints.filter((c) => c.enabled).length;
    const priority =
      body.fairness.priorityWeights.reduce((n, w) => n + w.weight, 0) /
      Math.max(body.fairness.priorityWeights.length * 100, 1);

    const matched = Math.max(
      0,
      Math.min(
        base.totalMentees,
        Math.round(base.totalMentees * (1 - constraints * 0.06)),
      ),
    );

    const shift = (band: S["PriorityBandStat"]): S["PriorityBandStat"] => {
      const pull = band.band === "high" ? priority * 0.12 : -priority * 0.05;
      return {
        ...band,
        meanScore: Number(Math.min(1, band.meanScore + pull).toFixed(3)),
        medianScore: Number(Math.min(1, band.medianScore + pull).toFixed(3)),
      };
    };

    const summary: S["FairnessSummary"] = {
      ...base,
      matchedCount: matched,
      unmatchedCount: base.totalMentees - matched,
      coverageRate: Number((matched / base.totalMentees).toFixed(4)),
      priorityBands: base.priorityBands.map(shift),
    };
    return HttpResponse.json(summary);
  }),

  http.get(url("/programs/:programId/broadcasts"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const body: S["BroadcastListing"] = {
      items: [...db.broadcasts].sort((a, b) =>
        b.createdAt.localeCompare(a.createdAt),
      ),
      segments: SEGMENTS.map((segment) => ({
        segment,
        count: segmentSize(segment),
      })),
      mergeCodes: db.mergeCodes,
    };
    return HttpResponse.json(body);
  }),

  http.post(url("/programs/:programId/broadcasts"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const body = (await request.json()) as S["BroadcastCreate"];
    if (!body?.subject?.trim() || !body?.body?.trim()) {
      return problem(400, "invalid_body", "A message needs a subject and a body.");
    }

    const unknown = unknownCodes(`${body.subject} ${body.body}`);
    if (unknown.length > 0) {
      return problem(
        400,
        "unknown_merge_code",
        `There is no such code as {${unknown[0]}}. Use one from the list.`,
      );
    }

    const count = segmentSize(body.segment);
    if (count === 0) {
      // Refused rather than sent to nobody: a send that reached zero people
      // still appears in the history as a send, and the coordinator would
      // believe the message went out.
      return problem(
        400,
        "empty_segment",
        "Nobody is in that group right now, so there is nobody to write to.",
      );
    }

    const created: S["Broadcast"] = {
      id: nextId(14),
      segment: body.segment,
      subject: body.subject,
      body: body.body,
      recipientCount: count,
      state: body.scheduledFor ? "scheduled" : "sent",
      createdAt: new Date().toISOString(),
      createdBy: db.session.account.name,
      scheduledFor: body.scheduledFor ?? null,
      deliveredCount: body.scheduledFor ? 0 : count,
      failedCount: 0,
    };
    db.broadcasts.push(created);
    return HttpResponse.json(created, { status: 202 });
  }),

  http.get(url("/programs/:programId/forms"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const role = new URL(request.url).searchParams.get("role");
    if (role !== "mentee" && role !== "mentor") {
      return problem(400, "invalid_role", "Ask for the mentee or the mentor form.");
    }

    const forRole = db.formVersions.filter((v) => v.role === role);
    const body: S["FormEditorState"] = {
      role,
      draft: forRole.find((v) => v.publishedAt === null) ?? null,
      published: publishedVersion(role),
      history: [...forRole]
        .sort((a, b) => b.version - a.version)
        .map((v) => ({
          id: v.id,
          version: v.version,
          publishedAt: v.publishedAt ?? null,
          questionCount: v.sections.flatMap((s) => s.fields).length,
          applicationCount: db.applications.filter(
            (a) => a.formVersionId === v.id,
          ).length,
        })),
    };
    return HttpResponse.json(body);
  }),

  http.put(url("/programs/:programId/forms/:role/draft"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const role = params.role;
    if (role !== "mentee" && role !== "mentor") return notFound("form");

    const body = (await request.json()) as S["FormDraftSave"];
    if (!Array.isArray(body?.sections)) {
      return problem(400, "invalid_body", "Send the whole form.");
    }

    let draft = db.formVersions.find(
      (v) => v.role === role && v.publishedAt === null,
    );

    if (!draft) {
      // Started from the published version rather than edited in place. This is
      // the whole guarantee of the screen: opening a live form and typing must
      // not change what an applicant is answering this minute.
      const live = publishedVersion(role);
      draft = {
        id: nextId(12),
        programId: PROGRAM_ID,
        role,
        version: (live?.version ?? 0) + 1,
        publishedAt: null,
        sections: [],
      };
      db.formVersions.push(draft);
    }

    draft.sections = body.sections;
    return HttpResponse.json(draft);
  }),

  http.post(url("/programs/:programId/forms/:role/publish"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const role = params.role;
    if (role !== "mentee" && role !== "mentor") return notFound("form");

    const draft = db.formVersions.find(
      (v) => v.role === role && v.publishedAt === null,
    );
    if (!draft) {
      return problem(409, "nothing_to_publish", "There is no draft to publish.");
    }

    const complaint = unpublishable(draft);
    if (complaint) return problem(409, "draft_incomplete", complaint);

    // The previous published version stays exactly as it is. Applications
    // already answered against it keep pointing at it.
    draft.publishedAt = new Date().toISOString();
    return HttpResponse.json(draft);
  }),

  http.get(url("/programs/:programId/milestones"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");
    return HttpResponse.json(orderedMilestones());
  }),

  http.put(url("/programs/:programId/milestones"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const body = (await request.json()) as S["ProgramMilestonesSave"];
    if (!Array.isArray(body?.items)) {
      return problem(400, "invalid_body", "Send the whole arc.");
    }
    if (body.items.some((m) => !m.title?.trim())) {
      return problem(400, "missing_title", "Every milestone needs a title.");
    }

    db.milestones = body.items.map((item, i) => ({
      // A milestone that arrives without an id is new. Minting here keeps the
      // client from having to invent one it cannot guarantee is unique.
      id: item.id ?? nextId(13),
      title: item.title.trim(),
      description: item.description ?? null,
      weekOffset: item.weekOffset,
      strandPrompt: item.strandPrompt ?? null,
      reminderDaysBefore: item.reminderDaysBefore ?? null,
      position: i + 1,
    }));

    return HttpResponse.json(orderedMilestones());
  }),

  http.get(url("/programs/:programId/templates"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const body: S["TemplateSet"] = {
      items: db.templates,
      mergeCodes: db.mergeCodes,
    };
    return HttpResponse.json(body);
  }),

  http.put(url("/programs/:programId/templates/:kind"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const template = db.templates.find((t) => t.kind === params.kind);
    if (!template) return notFound("template");

    const body = (await request.json()) as S["MessageTemplateSave"];
    if (!body?.subject?.trim() || !body?.body?.trim()) {
      return problem(400, "invalid_body", "A template needs a subject and a body.");
    }

    // Rejected here rather than at send time: an unknown code would otherwise
    // reach a participant as a literal brace in an email.
    const unknown = unknownCodes(`${body.subject} ${body.body}`);
    if (unknown.length > 0) {
      return problem(
        400,
        "unknown_merge_code",
        `There is no such code as {${unknown[0]}}. Use one from the list.`,
      );
    }

    template.subject = body.subject;
    template.body = body.body;
    template.isDefault = false;
    template.updatedAt = new Date().toISOString();
    template.updatedBy = db.session.account.name;

    return HttpResponse.json(template);
  }),

  http.delete(url("/programs/:programId/templates/:kind"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const index = db.templates.findIndex((t) => t.kind === params.kind);
    if (index === -1) return notFound("template");

    const original = db.defaultTemplates.find((t) => t.kind === params.kind);
    if (!original) return notFound("template");

    db.templates[index] = { ...original };
    return HttpResponse.json(db.templates[index]);
  }),

  http.get(url("/programs/:programId/applications"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const q = new URL(request.url).searchParams;
    const status = q.get("status");
    const role = q.get("role");
    const page = Number(q.get("page") ?? 1);
    const pageSize = Number(q.get("pageSize") ?? 25);

    const all = db.applications.filter((a) => a.programId === PROGRAM_ID);
    const filtered = all.filter(
      (a) => (!status || a.status === status) && (!role || a.role === role),
    );

    // Newest first: the queue is read top down and today's intake is the work.
    const ordered = [...filtered].sort((a, b) =>
      b.submittedAt.localeCompare(a.submittedAt),
    );

    const body: S["ApplicationPage"] = {
      items: ordered
        .slice((page - 1) * pageSize, page * pageSize)
        .map(toSummary),
      page,
      pageSize,
      total: ordered.length,
      // Counts describe the whole queue, not the filtered view, so the tabs
      // do not change their own numbers when one is selected.
      counts: {
        submitted: all.filter((a) => a.status === "submitted").length,
        under_review: all.filter((a) => a.status === "under_review").length,
        approved: all.filter((a) => a.status === "approved").length,
        waitlisted: all.filter((a) => a.status === "waitlisted").length,
        rejected: all.filter((a) => a.status === "rejected").length,
      },
    };
    return HttpResponse.json(body);
  }),

  http.post(url("/applications/:applicationId/decision"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;

    const application = db.applications.find(
      (a) => a.id === params.applicationId,
    );
    if (!application) return notFound("application");

    const body = (await request.json()) as S["ApplicationDecision"];
    const outcome = DECISION_STATUS[body?.decision];
    if (!outcome) {
      return problem(400, "invalid_decision", "Choose approve, waitlist or reject.");
    }
    if (DECIDED.has(application.status)) {
      return problem(
        409,
        "already_decided",
        `This application was already ${application.status}.`,
      );
    }

    decide(application, outcome);
    return HttpResponse.json(application);
  }),

  http.post(
    url("/programs/:programId/applications/decisions"),
    async ({ params, request }) => {
      const denied = requireSession();
      if (denied) return denied;
      if (params.programId !== PROGRAM_ID) return notFound("programme");

      const body = (await request.json()) as S["BulkDecision"];
      const outcome = DECISION_STATUS[body?.decision];
      if (!outcome || !Array.isArray(body?.applicationIds)) {
        return problem(400, "invalid_body", "Choose a decision and at least one application.");
      }

      const skipped: S["SkippedDecision"][] = [];
      let decided = 0;

      for (const id of body.applicationIds) {
        const application = db.applications.find((a) => a.id === id);
        if (!application) {
          skipped.push({ applicationId: id, reason: "No such application." });
          continue;
        }
        if (DECIDED.has(application.status)) {
          skipped.push({
            applicationId: id,
            reason: `Already ${application.status}.`,
          });
          continue;
        }
        decide(application, outcome);
        decided += 1;
      }

      const result: S["BulkDecisionResult"] = { decided, skipped };
      return HttpResponse.json(result);
    },
  ),

  http.get(url("/form-versions/:formVersionId"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    const found = db.formVersions.find((v) => v.id === params.formVersionId);
    return found ? HttpResponse.json(found) : notFound("form version");
  }),

  http.get(url("/programs/:programId/unmatched"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const q = new URL(request.url).searchParams;
    const reason = q.get("reason");
    const page = Number(q.get("page") ?? 1);
    const pageSize = Number(q.get("pageSize") ?? 25);

    const filtered = db.unmatched.filter((u) => !reason || u.reason === reason);

    const body: S["UnmatchedPage"] = {
      items: filtered.slice((page - 1) * pageSize, page * pageSize),
      page,
      pageSize,
      total: filtered.length,
      availableMentors: db.roster
        .filter(
          (r) =>
            r.role === "mentor" &&
            r.capacity !== null &&
            r.capacity !== undefined &&
            (r.load ?? 0) < r.capacity,
        )
        .map((r) => ({
          participationId: r.id,
          name: r.account.name,
          load: r.load ?? 0,
          capacity: r.capacity ?? 0,
          skills: [],
          timezone: r.timezone,
        })),
    };
    return HttpResponse.json(body);
  }),

  http.post(url("/programs/:programId/strands"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const body = (await request.json()) as S["StrandCreate"];
    const mentee = db.roster.find(
      (r) => r.id === body?.menteeParticipationId && r.role === "mentee",
    );
    const mentor = db.roster.find(
      (r) => r.id === body?.mentorParticipationId && r.role === "mentor",
    );
    if (!mentee || !mentor) return notFound("participant");

    if (mentor.capacity !== null && (mentor.load ?? 0) >= (mentor.capacity ?? 0)) {
      return problem(
        409,
        "mentor_full",
        `${mentor.account.name} is already at the capacity they set.`,
      );
    }
    if (mentee.matched) {
      return problem(
        409,
        "already_matched",
        `${mentee.account.name} already holds a strand.`,
      );
    }

    const now = new Date().toISOString();
    const created: S["Strand"] = {
      id: nextId(8),
      programId: PROGRAM_ID,
      state: "active",
      // Manual, per architecture 1: reports have to be able to tell a
      // coordinator's hand-pick from the algorithm's.
      originMode: "manual",
      createdAt: now,
      endedAt: null,
      // Honest about its own provenance. No score produced this pair, so it
      // does not get a sentence that sounds like one did.
      matchRationale: `Paired by ${db.session.account.name} from the unmatched queue.`,
      members: [
        {
          participationId: mentee.id,
          name: mentee.account.name,
          role: "mentee",
          photoUrl: null,
          headline: null,
          skills: [],
          timezone: mentee.timezone ?? null,
        },
        {
          participationId: mentor.id,
          name: mentor.account.name,
          role: "mentor",
          photoUrl: null,
          headline: null,
          skills: [],
          timezone: mentor.timezone ?? null,
        },
      ],
    };

    db.strands.push(created);
    mentee.matched = true;
    mentor.load = (mentor.load ?? 0) + 1;
    // Both leave the queue: the mentee now holds a strand, and the mentor is
    // no longer sitting at zero.
    db.unmatched = db.unmatched.filter(
      (u) => u.participationId !== mentee.id && u.participationId !== mentor.id,
    );

    return HttpResponse.json(created, { status: 201 });
  }),

  http.get(url("/programs/:programId/runs"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const q = new URL(request.url).searchParams;
    const page = Number(q.get("page") ?? 1);
    const pageSize = Number(q.get("pageSize") ?? 25);

    const ordered = [...db.runs].sort((a, b) =>
      b.createdAt.localeCompare(a.createdAt),
    );
    // The list view carries no pairs or fairness summary.
    const items: S["Run"][] = ordered.map((r) => ({
      id: r.id,
      programId: r.programId,
      state: r.state,
      progress: r.progress,
      recipeVersion: r.recipeVersion,
      createdAt: r.createdAt,
      createdBy: r.createdBy,
      publishedAt: r.publishedAt,
      publishedBy: r.publishedBy,
      draftedCount: r.draftedCount,
      publishedCount: r.publishedCount,
      coverageRate: r.coverageRate,
    }));

    const body: S["RunPage"] = {
      items: items.slice((page - 1) * pageSize, page * pageSize),
      page,
      pageSize,
      total: items.length,
    };
    return HttpResponse.json(body);
  }),

  http.post(url("/programs/:programId/runs"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    if (db.runs.some((r) => r.state === "queued" || r.state === "running")) {
      return problem(409, "run_in_progress", "A matching run is already in progress.");
    }

    const created: S["RunDetail"] = {
      id: nextId(6),
      programId: PROGRAM_ID,
      state: "queued",
      progress: RUN_STEPS[0],
      recipeVersion: 4,
      createdAt: new Date().toISOString(),
      createdBy: db.session.account.name,
      publishedAt: null,
      publishedBy: null,
      draftedCount: 0,
      publishedCount: 0,
      coverageRate: null,
      fairnessSummary: null,
      pairs: [],
      unmatchedCount: 0,
    };
    db.runs.push(created);
    return HttpResponse.json(created, { status: 202 });
  }),

  http.get(url("/runs/:runId"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    const run = db.runs.find((r) => r.id === params.runId);
    if (!run) return notFound("run");
    advanceRun(run);
    return HttpResponse.json(run);
  }),

  http.post(url("/runs/:runId/publish"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    const run = db.runs.find((r) => r.id === params.runId);
    if (!run) return notFound("run");

    if (run.state !== "drafted") {
      return problem(
        409,
        "not_publishable",
        `A run can only be published from drafted. This one is ${run.state}.`,
      );
    }

    run.state = "published";
    run.publishedAt = new Date().toISOString();
    run.publishedBy = db.session.account.name;
    run.publishedCount = run.pairs.length;
    return HttpResponse.json(run);
  }),

  http.get(url("/programs/:programId/strands"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    if (params.programId !== PROGRAM_ID) return notFound("programme");

    const state = new URL(request.url).searchParams.get("state");
    const items = db.strandSummaries.filter((s) => !state || s.state === state);
    return HttpResponse.json(items);
  }),

  http.get(url("/strands/:strandId"), ({ params }) => {
    const denied = requireSession();
    if (denied) return denied;
    const found = db.strands.find((s) => s.id === params.strandId);
    return found ? HttpResponse.json(found) : notFound("strand");
  }),

  http.get(url("/strands/:strandId/messages"), ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    const id = String(params.strandId);
    const thread = db.messages[id];
    if (!thread) return notFound("strand");

    const q = new URL(request.url).searchParams;
    const limit = Number(q.get("limit") ?? 50);
    const before = q.get("before");
    const since = q.get("since");

    if (before && since) {
      return problem(
        400,
        "conflicting_cursors",
        "Ask for messages before a point or after one, not both.",
      );
    }

    if (since) {
      const at = thread.findIndex((m) => m.id === since);
      // Unknown anchor falls through to the newest page, matching the server:
      // a poller out of sync recovers rather than starving.
      if (at !== -1) {
        const body: S["MessagePage"] = {
          items: thread.slice(at + 1, at + 1 + limit),
          nextCursor: null,
        };
        return HttpResponse.json(body);
      }
    }

    const end = before ? thread.findIndex((m) => m.id === before) : thread.length;
    const start = Math.max(0, end - limit);

    const body: S["MessagePage"] = {
      items: thread.slice(start, end),
      nextCursor: start > 0 ? thread[start].id : null,
    };
    return HttpResponse.json(body);
  }),

  http.post(url("/strands/:strandId/messages"), async ({ params, request }) => {
    const denied = requireSession();
    if (denied) return denied;
    const id = String(params.strandId);
    const thread = db.messages[id];
    if (!thread) return notFound("strand");

    const body = (await request.json()) as S["MessageCreate"];
    if (!body?.body?.trim()) {
      return problem(400, "empty_message", "A message cannot be empty.");
    }

    const sender = db.strands
      .find((s) => s.id === id)
      ?.members.find((m) => m.participationId === db.session.participations[0].id);

    const created: S["Message"] = {
      id: nextId(9),
      strandId: id,
      author: {
        participationId: db.session.participations[0].id,
        name: sender?.name ?? db.session.account.name,
        photoUrl: null,
      },
      body: body.body,
      sentAt: new Date().toISOString(),
      deliveryState: "sent",
      clientToken: body.clientToken ?? null,
    };

    thread.push(created);

    const summary = db.strandSummaries.find((s) => s.id === id);
    if (summary) {
      summary.lastMessage = {
        authorName: created.author.name,
        body: created.body,
        sentAt: created.sentAt,
      };
      summary.lastActivityAt = created.sentAt;
    }

    return HttpResponse.json(created, { status: 201 });
  }),
];
