# Braid

An equitable mentorship pairing engine. Built for Mentor Me Collective's Grow
with Google programme, 2026 cohort, against UN SDG Goal 5.

```
openapi.yaml        the API contract — one copy, both sides read it
docker-compose.yml  local stack
docs/               architecture, design direction, brand reference
web/                Next.js frontend  ✅ complete
api/                FastAPI backend   ⏳ next
```

---

## The problem

Most mentoring platforms solve a **discovery** problem — two people never met,
and software introduces them. Braid solves an **allocation** problem: in a
cohort with two hundred mentees and twenty-five available mentors, nobody
struggles to find a mentor. There are not enough, and something has to decide
who gets one.

That decision is currently made by whoever applied first, whoever wrote the most
polished application, or a coordinator working a spreadsheet at midnight. Each
quietly favours the applicant with the most access already.

Braid is a constrained assignment system with an explicit fairness objective:
**it decides how a scarce resource is distributed, and it shows its working.**

---

## Running it

Full runbook: [RUNNING.md](RUNNING.md).

**Frontend on its own** — no backend or database needed. MSW intercepts every
request and serves deterministic fixtures on a fixed clock.

```bash
cd web
npm install
npm run dev          # http://localhost:3000
```

**The database**, once you start on the API:

```bash
docker compose up db
```

### Where to look

Seeded organisation `she-code-africa`, programme `backend-cohort-4`.

| Route | What it shows |
|---|---|
| `/p/she-code-africa/backend-cohort-4` | Programme landing |
| `/p/she-code-africa/backend-cohort-4/apply?role=mentee` | Dynamic application form |
| `/o/she-code-africa/p/backend-cohort-4` | Participant home |
| `/admin/o/she-code-africa` | Coordinator dashboard |
| `/admin/o/she-code-africa/runs/00000006-0000-4000-8000-000000000003` | Run review, fairness summary first |
| `/ui` | Every UI primitive in every state |

The app starts signed in as a coordinator who is also a mentor: role lives on the
participation, never on the account.

---

## How it is put together

**Contract first.** Every endpoint exists in `openapi.yaml` before any screen is
written, and `web/lib/api/types.ts` is generated from it. No response type is
hand-written. 48 endpoints, 144 schemas. The backend implements a specification
that already exists rather than one negotiated afterwards.

**The unknown form schema stops at one boundary.** Coordinators build their own
application forms, so the shape is unknown at compile time. Form definitions are
versioned JSON with stable ids; answers are keyed by id and never by question
text, so renaming a question does not orphan existing answers. An application
keeps the version it was answered against, permanently.

**One form renderer, four consumers** — apply wizard, profile edit, form-builder
preview, application review. A question added in the builder reaches all four
with no further work, and the preview cannot drift from what applicants see.

**Tokens are enforced by the build.** `web/styles/tokens.css` resets Tailwind's
palette and scale to `initial`, so `text-gray-500` and `p-13` are not classes.

**Two orderings carry ethical weight and should not be "improved":** the fairness
summary sits above the pair list on run review, and the criteria test run returns
a fairness summary with no pairs at all. Both stop a coordinator optimising pair
by pair, which is the behaviour that reproduces the access gap.

### Stack

Next.js 16 (App Router), TypeScript strict, Tailwind v4 themed through CSS custom
properties, `react-hook-form` + `zod`, `@tanstack/react-query` for client
mutations and polling only, MSW for mocking, `openapi-typescript` for types.
FastAPI, SQLAlchemy, Alembic and PostgreSQL to come.

No dependency was added for anything the platform provides: charts are
hand-drawn SVG, dialogues are the native `<dialog>` element, PDF export is the
print stylesheet.

---

## Deploying

Three services from this one repository, each built from its own directory. This
works the same on Railway or Render.

| Service | Directory | Notes |
|---|---|---|
| Postgres | — | Managed database; it hands you a connection URL |
| `api` | `api/` | Set `DATABASE_URL` to that connection URL |
| `web` | `web/` | Set `NEXT_PUBLIC_API_URL` to the api service's public URL |

`NEXT_PUBLIC_API_URL` is the only value that differs between local and
production. Nothing in the code changes.

**A production build has no mock backend.** Mocking is gated to
`NODE_ENV === "development"`, so `web` deployed without a running `api` returns
500 on every page that fetches. The frontend cannot go live before the API does.

---

## Status

**Frontend complete** — 32 routes, no placeholder screens, each with empty,
loading and error states.

**Not built yet:** the FastAPI backend and PostgreSQL database, taxonomy and
normalisation of free text to canonical skills, per-pair score attribution,
pair-level run actions (swap, lock, reject), group strands proposed by a run.

`docs/architecture.md` is the fullest description of the system — core model,
every page, the four shells. Code comments cite it by section number.

## Licence

MIT.
