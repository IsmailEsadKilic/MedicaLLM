# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (ci for reproducible installs)
COPY package.json package-lock.json* ./
RUN npm ci

# O11: Build-time flag — set VITE_USE_HTTPS=true when deploying behind TLS.
# The value is embedded in the compiled JS bundle by Vite.
ARG VITE_USE_HTTPS=false
ENV VITE_USE_HTTPS=$VITE_USE_HTTPS

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: Serve with Nginx ──────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Copy compiled assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx config (SPA routing + API proxy)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
