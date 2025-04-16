FROM node:18-alpine AS base

# Basis-Arbeitsverzeichnis
FROM base AS deps
WORKDIR /app

# Abhängigkeiten installieren
COPY package.json package-lock.json* ./
RUN npm ci

# Builder-Stufe
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js build
RUN npm run build

# Produktions-Stufe
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

# Erstelle einen nicht-Root-Benutzer
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Kopiere die build-Artefakte
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
