# Running Braid

Three parts: Postgres, the FastAPI backend, the Next.js frontend.

## Everything at once

If you would rather not install Python and Node to look around:

```bash
docker compose up --build
docker compose exec api python -m app.seed    # once, for the sample cohort
```

Then open **http://localhost:3000/signin**. Demo mode is on, so "Explore as a
coordinator" works immediately. Sign-in links are written to the api's log
rather than sent — `docker compose logs api` is where to find them.

Deploying a copy where other people can reach it is a different set of
questions, answered in [`DEPLOYING.md`](DEPLOYING.md).

## Quick start

```bash
# 1. Database  (from the repo root)
docker compose up -d db

# 2. Backend   (from api/)
cd api
uv sync                                   # first time only
cp .env.example .env                      # first time only, then edit if needed
uv run alembic upgrade head               # create the tables
uv run python -m app.seed                 # load the sample cohort
DEMO_MODE=true uv run uvicorn app.main:app --port 8000

# 3. Frontend  (from web/, in a second terminal)
cd web
npm install                               # first time only
npm run dev
```

Then open **http://localhost:3000/signin** and click **Explore as a
coordinator** or **Explore as a participant**.

Postgres is published on **5433**, not 5432, so it does not collide with one
you may already be running. `api/.env.example` already points there. Set
`DB_PORT` to move it, and match `DATABASE_URL` in `api/.env` if you do.

## The two modes

`web/.env.local` decides whether the frontend talks to the real backend or to
its own built-in mock.

```bash
# Against the real FastAPI backend
NEXT_PUBLIC_API_URL=http://localhost:8000/v1
NEXT_PUBLIC_API_MOCKING=disabled
NEXT_PUBLIC_DEMO_MODE=true

# Frontend on its own, no backend or database needed at all
NEXT_PUBLIC_API_MOCKING=enabled
```

The mock serves every screen in the app. The real backend currently serves the
ones listed below. Restart `npm run dev` after changing this file.

## What works against the real backend

Sign in as **coordinator** (Amara Okonkwo) or **participant** (Blessing Adewale)
from the sign-in screen.

| Screen | Route |
|---|---|
| Programme landing | `/p/she-code-africa/backend-cohort-4` |
| Application form | `/p/she-code-africa/backend-cohort-4/apply?role=mentee` |
| Sign in, verify, sign out | `/signin` |
| Participant home | `/o/she-code-africa/p/backend-cohort-4` |
| Strands list and detail, sending messages | `…/strands` |
| Profile, directory, resources | `…/me`, `…/directory`, `…/resources` |
| Roster | `/admin/o/she-code-africa/programs/{programId}/roster` |
| **Matching runs — start, watch, publish** | `…/programs/{programId}/runs` |
| **Unmatched queue and pairing by hand** | `…/programs/{programId}/unmatched` |
| Applications review and decisions | `…/programs/{programId}/applications` |
| Form builder — draft and publish | `…/programs/{programId}/form` |
| Matching criteria and test run | `…/programs/{programId}/criteria` |
| Milestones | `…/programs/{programId}/milestones` |
| Templates | `…/programs/{programId}/templates` |
| Coordinator dashboard | `/admin/o/she-code-africa` |
| Strands monitor — health, nudge, pause, end | `…/programs/{programId}/strands` |
| Broadcast | `…/programs/{programId}/comms` |
| Report — coverage, funnel, fairness, demographics | `…/programs/{programId}/reports` |
| Audit log | `/admin/o/she-code-africa/audit` |
| Account settings — name, email preferences, mute, leave | `/settings` |
| My programmes | `/programs` |
| Accepting an invitation | `/invite/invite-pending` |
| Save and resume a part-filled application | `…/apply?role=mentee` |
| Research writing programme (a second org, different form) | `/o/unilag/p/research-writing-2026` |

`programId` is `00000002-0000-4000-8000-000000000001`.

### The thing worth looking at

On the runs page press **Start a run**. It creates a real matching run, polls it
from queued to drafted, and shows the fairness summary above the pair list:
coverage, mentor load, and the mean match quality for each priority band. That
ordering is the point — the distribution before the names.

Then press **Publish** and the strands appear on the participant side.

Now open **Reports**. Two sections change because of what you just did:
coverage over time steps up on today's date, and *match quality by priority
band* fills in — it was empty before, because it reports the figures from a
**published** run rather than recomputing its own. Every other figure on that
page is derived at read time, so nothing there is a counter anybody has to
remember to increment.

Two sections stay empty on purpose, and say why on the page: sessions are a
per-strand total with no dates, and the mid-point check-in is a message rather
than a question with recorded answers. Neither can be put on an axis honestly,
so neither is.

**Who is in the programme** is the part worth reading closely. It counts only
the people who ticked the optional reporting consent — 8 of 22 in the seeded
cohort, not all 22 — and it withholds any group of three or fewer rather than
rounding it, saying how many it withheld.

### The other thing worth looking at

Open **http://localhost:3000/invite/invite-pending** in a window with no
session. It is what an emailed invitation looks like arriving cold: Amara's note
is there, the address it was sent to is named, and accepting asks for a name and
nothing else. Accept it and you land inside the programme already signed in,
never having seen the sign-in screen.

The other two tokens are the states that matter more: `invite-expired` explains
what lapsed and offers to ask for a new one, and `invite-known` is the same
address as an existing account, so it says so rather than letting somebody fear
they are about to create a duplicate.

## Everything is on the real backend

All 60 operations in `openapi.yaml` are implemented. There is no screen left
that needs the mock.

`NEXT_PUBLIC_API_MOCKING=enabled` still works and still serves the whole app —
useful for running the frontend with no database at all.

## Signing in for real

Demo sign-in exists because the seeded people have `example.org` addresses
nobody can receive mail at. The real magic-link path works too — there is just
no mail provider configured, so the link is printed to the API's own log:

```
INFO braid.mail  email not delivered (no provider configured)
  to:      amara.okonkwo@example.org
  | http://localhost:3000/verify/XcQ2...
```

Paste that URL into the browser and you are signed in.

## Resetting

```bash
cd api && uv run python -m app.seed
```

Wipes and reloads the sample cohort, including sessions — so you will be signed
out. Safe to run repeatedly.

## Checks

```bash
cd api && uv run ruff check .     # backend lint
cd web && npx tsc --noEmit        # frontend types, strict
cd web && npm run lint
```
