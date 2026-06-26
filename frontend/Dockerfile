# ── Stage 1: dependencies ─────────────────────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production && npm cache clean --force

# ── Stage 2: builder ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install all deps (including devDeps for build)
COPY package.json package-lock.json* ./
RUN npm ci && npm cache clean --force

COPY . .

# Build args for public env vars
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/ws
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

RUN npm run build

# ── Stage 3: runner ───────────────────────────────────────────────────────────
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built output
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget -qO- http://localhost:3000 || exit 1

CMD ["node", "server.js"]
