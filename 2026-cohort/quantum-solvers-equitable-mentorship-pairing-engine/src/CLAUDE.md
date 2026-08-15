# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Rules for working in this repository. Read before any task. These are constraints, not preferences.

## What this is

Braid, a mentoring platform. A monorepo: Next.js frontend in `web/`, FastAPI backend in `api/`, and the OpenAPI contract at the root where both read it.

```
openapi.yaml        the contract — one copy, both sides read it
docker-compose.yml  db, and api + web once they exist
docs/               architecture, design direction, brand reference
design/             design files (.dc.html)
web/                the Next.js app
api/                FastAPI — not built yet, see api/README.md
```

**Paths in this file are relative to `web/`** unless they are one of the root entries above. `npm` commands run from `web/`. `openapi.yaml` and `docs/` are at the root, so `npm run gen:api` reads `../openapi.yaml`.

Reference docs, read the relevant one before building:

- `docs/architecture.md` — core model, sitemap, every page, the four shells (section 7)
- `docs/design-direction.md` — tokens, components, motion, voice. Components cite it by section number (`8.3`, `9`), so a citation in a comment is a real address
- `docs/design-prompt.md` — condensed brand and token reference

`AGENTS.md` is written by `next dev`, not by hand. This is Next.js 16: read `node_modules/next/dist/docs/` before using an API you remember from an older version.

## Commands

All from `web/`:

```bash
npm run dev        # next dev, http://localhost:3000, MSW on
npm run build      # next build
npm run lint       # eslint
npx tsc --noEmit   # the type check; strict, and it catches what lint does not
npm run gen:api    # ../openapi.yaml -> lib/api/types.ts. Run after every contract edit
```

**A production build has no mock backend.** Mocking is gated to `NODE_ENV === "development"`, so `next start` without a real API returns 500 on every page that fetches. That is expected, not a regression — the frontend cannot be usefully deployed until `api/` exists.

There is no test runner and no test files. Verification is `npx tsc --noEmit`, `npm run lint`, and the app itself. `/ui` renders every primitive in every state (dev only, `notFound()` in production) and is the fastest way to see a primitive change.

## Stack

- Next.js App Router, TypeScript strict
- Tailwind v4, theme mapped to CSS custom properties in `styles/tokens.css`
- `react-hook-form` + `zod` for forms
- `@tanstack/react-query` for client mutations and polling only
- MSW for API mocking until the backend exists
- `openapi-typescript` generating `lib/api/types.ts` from `openapi.yaml`

Do not add a dependency without asking first. Do not add a global state library.

## Architecture

**Two API clients, and which one you get is not a preference.** `lib/api/server.ts` (`serverApi`) is for Server Components; it imports `next/headers` to forward the session cookie by hand, and that import is what fails the build if it ever reaches a client bundle. `lib/api/client.ts` (`api`) is for client components. Both resolve `globalThis.fetch` per call rather than at construction, because MSW installs its fetch later and capturing early is module-ordering luck. Never call `fetch` directly in a component.

**MSW runs on both sides.** `instrumentation.ts` starts the Node server for Server Components, route handlers and the build. `app/providers.tsx` starts the browser worker in an effect; `lib/api/ready.ts` holds browser requests on the `apiReady` promise until the worker is listening, so nothing races the first paint. Mocking is on when `NODE_ENV === "development"` and `NEXT_PUBLIC_API_MOCKING !== "disabled"` (`lib/api/msw/enabled.ts`). The fixture DB (`lib/api/msw/fixtures.ts`) is module state on a fixed clock — `NOW` is 2026-08-08 — so it is deterministic per process and mutations survive until the dev server restarts. It starts `signedIn: true`. The seeded programme is `she-code-africa` / `backend-cohort-4`.

**Guards live in layouts, and pages assume they passed.** `lib/auth/guard.ts` wraps the session in React `cache()` so a layout and its pages resolve one session between them. `requireParticipation` resolves org + programme + role for the participant layout, `requireCoordinator` for the admin layout; a false result renders `<Forbidden>` rather than redirecting. Role lives on `Participation`, never on `Account` — the same person is a mentee in one programme and a mentor in another.

**Four route groups because they have four different guards.** `(public)` no session, no chrome — width and header live in the pages because landing/apply and signin/verify differ. `(account)` session only, no org or programme in the URL, which is exactly why it cannot inherit the participant layout. `(participant)` `/o/[org]/p/[program]/…`. `(admin)` `/admin/o/[org]/…`, desktop-first, persistent sidebar, no phone drawer.

**Tokens are enforced by the build, not by discipline.** `styles/tokens.css` resets `--color-*`, `--text-*`, `--spacing-*`, `--radius-*`, `--shadow-*`, `--ease-*` and `--container-*` to `initial` in `@theme`, so Tailwind's stock palette and scale do not exist — `text-gray-500` and `p-13` are not classes. Semantic names are mapped in `@theme inline` so re-theming the layer above re-themes every utility: `bg-page`, `bg-surface`, `text-primary`, `text-muted`, `border-subtle`, `bg-accent`, `text-on-accent`, `outline-focus`. The type scale is deliberately *not* theme entries — it ships as `@utility type-*` (`type-body-m`, `type-heading-l`) so size, leading, weight, tracking, family and case travel together. Strand colour is picked by hashing the partner's participation id onto `data-strand="1|2|3"`, and the `@theme inline` reference is what lets the nearest ancestor resolve it.

**The form pipeline is one generator, four consumers.** `lib/form/conditions.ts` decides which fields are visible; that `visibleIds` set is a required argument everywhere downstream so a hidden field's required rule cannot fire by accident. `zod-schema.ts` builds the validator from the form version, `json-schema.ts` derives the portable JSON Schema from that same validator so the two cannot drift, and `answers.ts` serialises to the wire — dropping invisible fields (a question nobody saw has no answer) and file fields (there is no upload endpoint yet). Nothing about a form is written twice, and nothing is hardcoded per form.

## Hard rules

**Colour.** No hex, rgb, or hsl anywhere except `styles/tokens.css`. Components use semantic token names only (`--text-primary`, `--action-primary-bg`). If a colour you need does not exist, stop and ask. Do not add one.

**Spacing.** Only 4, 8, 12, 16, 24, 32, 48, 64, 96. No arbitrary Tailwind values like `p-[13px]`.

**Type.** Only the thirteen scale tokens from design direction 5.3. Switzer for UI, Gambetta for display, JetBrains Mono for numbers. `data-l` and `data-xl` are numbers only; a word never takes them. Gambetta appears in exactly five places, listed in 5.2. Do not use it anywhere else.

**Shadows.** Two only, both defined as tokens. Cards get a border, never a shadow.

**Motion.** Only the five duration tokens and four easing tokens. Animate `transform` and `opacity` only. Never `height`, `top`, `width`, or `box-shadow`.

**Server vs client.** Default to Server Components. Add `"use client"` only when the component needs state, effects, or event handlers. Do not mark a whole page as client to avoid thinking about it. React Query is for client mutations and polling, not for fetching what a Server Component can fetch.

**Data.** Never call `fetch` directly in a component. All requests go through the typed clients in `lib/api`. Types are generated from `openapi.yaml`; do not hand-write response types. If an endpoint you need is missing, add it to `openapi.yaml` first, run `npm run gen:api`, add an MSW handler, then build.

**Accessibility.** Every interactive element keyboard reachable with a visible focus ring. Never `outline: none` without a replacement. Modals trap focus and return it on close. Every input has a real label; placeholder is never the label. Touch targets 44px minimum. Colour never carries meaning alone.

**States.** Every list has an empty state. Every async action has a loading state. Every fetch has an error state with a retry. A component is not done until all three exist.

**Copy.** Sentence case. Active voice. Name people, not roles. British spelling in prose ("programme" in copy; `program` stays the URL segment and the API field). The verb on a button is the verb in the resulting toast. No "Oops", no exclamation marks in system messages, no emoji.

## Do not

- Invent a value that is not in `tokens.css`
- Add gradients, glassmorphism, or shadowed card grids
- Use `any`, or `@ts-ignore`
- Create a component that is not asked for
- Refactor code you were not asked to touch
- Add comments that restate what the code does. Comments here record *why* a decision went the way it did, usually citing a design-direction section

## Working style

For anything larger than a single component: write a plan first, list the files you will create or change, and wait for approval before writing code.

One task at a time. Do not build ahead.

When a design doc and my instruction conflict, say so rather than picking one silently.

## Build order

Do not skip ahead. Each step is one commit.

1. ✅ `tokens.css`, Tailwind theme mapping, fonts self-hosted and preloaded
2. ✅ `openapi.yaml` for the slice, generated types, typed clients, MSW
3. ✅ Four shells: route groups, layouts, navigation, guards
4. ✅ `ui/` primitives: button, input, table, empty state
5. ✅ Strand card, 1:1 and group variants
6. ✅ Dynamic form renderer
7. ✅ Slice screens: landing, apply, home, strand detail, plus sign in, verify,
   the application confirmation and the strands list — the flow has a door now
8. ✅ Admin slice: roster, matching runs, run review with publish

Match reveal is last. It pays off a product that has to exist first.

**Not built, and why.** Directory, resources, profile, invite, and the other
thirteen admin screens have no endpoints in `openapi.yaml`. Adding them means
contract first, then `npm run gen:api`, then a handler, then the screen. Sign in
has no password path and the run review has no swap, lock, reject or re-run for
the same reason.

**One trap worth knowing.** MSW runs in two places with two copies of the
fixtures, so anything created at runtime exists on one side only. A client
mutation followed by a server-rendered read returns 404 in development and works
in production, which is the worst way for a bug to behave. Keep each flow's
write and read on the same side: submitting an application is a server action
because its confirmation is server-rendered, and the run review reads in the
browser because it polls and publishes there.
