# ─── TruthLens Frontend Dockerfile ───
# Multi-stage: Node build → Nginx serve
# VITE_API_URL is set at build time via ARG

# ─── Stage 1: Build ───
FROM node:22-alpine AS builder

WORKDIR /build

# Copy package files first for layer caching
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copy source and build
COPY . .

# Build-time variable for API URL (baked into JS bundle)
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build


# ─── Stage 2: Serve with Nginx ───
FROM nginx:1.27-alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /build/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
