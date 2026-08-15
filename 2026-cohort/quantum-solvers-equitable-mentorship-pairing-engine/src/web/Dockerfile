# The frontend, built once and served from the standalone output.
#
# The one thing worth knowing about this file: `NEXT_PUBLIC_*` is not read at
# runtime. Next inlines it into the client bundle during `next build`, so the
# API's address has to be a build argument. Passing it only as a runtime
# environment variable produces an image that builds cleanly, starts cleanly,
# and then has every browser request go to localhost:8000 — which on a deployed
# host is the visitor's own machine. Set NEXT_PUBLIC_API_URL as a *build* var on
# whatever platform builds this.

FROM node:22-slim AS deps
WORKDIR /app
# Dependencies first, so a source change does not invalidate the install layer.
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# The contract lives at the repo root, one level above this build context, so
# the type generation that reads it has already been run and committed. Nothing
# here reaches outside web/.
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_DEMO_MODE=false
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_DEMO_MODE=$NEXT_PUBLIC_DEMO_MODE \
    NEXT_PUBLIC_API_MOCKING=disabled \
    NEXT_TELEMETRY_DISABLED=1

RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    # Without this the standalone server binds 127.0.0.1 inside the container
    # and the platform's health check never reaches it.
    HOSTNAME=0.0.0.0

# Not root. The image has no reason to write anywhere but /tmp.
RUN groupadd --system --gid 1001 nodejs \
    && useradd --system --uid 1001 --gid nodejs nextjs

# `standalone` carries the server and its traced dependencies; static and public
# are not traced and have to be copied alongside it.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
