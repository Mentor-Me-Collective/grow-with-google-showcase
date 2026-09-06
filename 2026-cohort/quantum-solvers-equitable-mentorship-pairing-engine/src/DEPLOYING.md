# Deploying Braid

For putting a copy somewhere other people can reach. If you only want it running
on your own machine, [`RUNNING.md`](RUNNING.md) is shorter and this is not
needed.

Written for Railway because it hosts all three services in one project, but
nothing here is Railway-specific beyond the variable names — Render, Fly and a
plain VPS need the same six decisions.

---

## What you need first

- A **Railway** account. The three services fit in the trial credit.
- A **[Resend](https://resend.com)** API key, if anybody other than you needs to
  sign in. Without one the service still runs and still mints sign-in links — it
  writes them to the log instead of sending them, which is fine for a demo you
  drive yourself and useless for anybody else.
- A **domain**, if you want the sign-in cookie to work without special handling.
  Optional, and the section on cookies explains what it buys.

---

## The three services

One Postgres, one FastAPI, one Next.js. In Railway: **New Project → Deploy from
GitHub repo**, then add each service with its own root directory.

| Service | Root directory | Notes |
|---|---|---|
| `db` | — | Railway's Postgres plugin, not from this repo |
| `api` | `/api` | Builds `api/Dockerfile`. Migrations run at start |
| `web` | `/web` | Builds `web/Dockerfile` |

---

## 1. Database

Add Railway's Postgres plugin. It gives you a `DATABASE_URL` that starts
`postgresql://`, and **that will not work.**

This project installs psycopg 3. SQLAlchemy reads `postgresql://` as psycopg
*2*, which is not installed, and the service dies at boot with
`ModuleNotFoundError: No module named 'psycopg2'`. The scheme has to name the
driver:

```
postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
```

On Railway, set it on the **api** service using references rather than
copy-pasting a password that will later rotate:

```
DATABASE_URL=postgresql+psycopg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/${{Postgres.PGDATABASE}}
```

You do not need to run migrations by hand. The api container runs
`alembic upgrade head` before it starts serving, so the schema is created on
first boot and updated on every deploy after.

---

## 2. The api service

```bash
DATABASE_URL=postgresql+psycopg://…      # from above
WEB_ORIGIN=https://your-web-service.up.railway.app
ENVIRONMENT=production                   # makes the session cookie Secure
SESSION_COOKIE_SAMESITE=lax              # see "Cookies" below before changing
RESEND_API_KEY=re_…                      # omit and links go to the log
MAIL_FROM=Braid <hello@yourdomain.com>   # must be a domain verified with Resend
DEMO_MODE=true                           # see "Letting people in" below
```

`WEB_ORIGIN` must name the frontend's origin **exactly** — scheme, host, no
trailing slash. The frontend sends credentials, and browsers reject a wildcard
origin on credentialed requests, so a near-miss here shows up as every API call
failing CORS with the app otherwise looking healthy.

---

## 3. The web service

Two of these are **build** variables, not runtime ones. Railway calls them build
arguments; set them where the service's build is configured, not only in
Variables.

```bash
NEXT_PUBLIC_API_URL=https://your-api-service.up.railway.app/v1   # BUILD
NEXT_PUBLIC_DEMO_MODE=true                                       # BUILD
```

Next inlines anything prefixed `NEXT_PUBLIC_` into the client bundle during
`next build`. Passed only at runtime, you get an image that builds cleanly,
starts cleanly, and then sends every browser request to `localhost:8000` — which
on a deployed site is *the visitor's own machine*. Nothing errors on your side.
It simply does not work, for everyone except you, and only in production.

There is one optional runtime variable:

```bash
API_URL_INTERNAL=http://api.railway.internal:8000/v1             # runtime
```

Server Components fetch from inside the container, where the public URL costs a
round trip out to the internet and back. Setting this points them at Railway's
private network instead. Leave it unset to start — everything works without it,
just a little slower.

---

## Cookies, and the one decision worth making early

The session is a cookie, and cookies care about *sites*, not origins.

Deployed on `web-production.up.railway.app` and `api-production.up.railway.app`,
those are both `up.railway.app` — the same site — so `SameSite=lax` works and
you can ignore this section.

Put the two on genuinely different domains — a custom domain for the frontend
and a Railway subdomain for the API, say — and they become cross-site. A `lax`
cookie is then silently dropped on every API call. The app loads, sign-in
appears to succeed, and the next request is anonymous. It is a convincing bug
and it only ever appears in production.

Two ways out:

- **Best:** use subdomains of one domain you own — `braid.example.com` and
  `api.braid.example.com`. Same site, `lax` keeps working, and you never think
  about this again.
- **Otherwise:** set `SESSION_COOKIE_SAMESITE=none` on the api. Browsers then
  require `Secure`, which the app forces on automatically. This is a weaker
  posture and stricter browser settings can still block it.

---

## Letting people in

There are two doors, and you probably want both.

**Demo mode.** `DEMO_MODE=true` opens "Explore as a coordinator" and "Explore as
a participant" on the sign-in screen, which sign in as seeded accounts with no
email involved. It is the fastest way to let somebody see the product — and
everybody who clicks it shares one identity and edits the same data, so it is
for looking, not for testing a flow. The endpoint 404s when the variable is off.

**Real sign-in.** Somebody applies to a programme, which creates their account,
and from then on they sign in with a link sent to their address. This needs
`RESEND_API_KEY` set *and* a verified domain in `MAIL_FROM`: Resend's shared
sender `onboarding@resend.dev` only delivers to the address that owns the Resend
account, so it will look like working email until the first other person tries.

**Never set `DEMO_MODE=true` on a deployment holding real people's data.** It is
a way into a seeded account, not a way into a real cohort — but the line between
those is the seed, not the code.

---

## Sample data

The database starts empty, so the landing page has no programme to show. Load
the sample cohort once, from the api service's shell:

```bash
python -m app.seed
```

Safe to repeat — it resets the demo data rather than duplicating it.

---

## After it is up

Worth checking in this order, because each one fails differently:

1. `https://your-api…/health` returns `{"status":"ok"}` — the api is alive and
   its migrations ran.
2. The landing page lists a programme — the **server** can reach the api.
3. Sign in with demo mode — the **browser** can reach the api, and CORS is right.
4. Reload after signing in and you are still signed in — the cookie survived,
   which is the SameSite question above.
5. Request a real sign-in link and check it arrives — mail is configured.

If step 3 works and step 4 does not, it is the cookie. If step 2 works and step 3
does not, it is `NEXT_PUBLIC_API_URL` being set at runtime instead of at build.

---

## Two things to know before it gets busy

**Connections.** Pool size multiplied by instance count has to stay under
Postgres's `max_connections`, which is commonly 100. The default pool is 5 with
10 overflow, so each instance can hold 15 and roughly six instances is the
ceiling. This fails as connection refusals under exactly the load you scaled up
to handle. Pin the pool size before scaling out, or put PgBouncer in front.

**Matching runs happen in the web process.** They are not on a queue, so a
deploy in the middle of one takes it with it. Runs stuck for more than ten
minutes are swept to `discarded` on the next read, which is recoverable but not
free — avoid deploying while a coordinator is running a match.
