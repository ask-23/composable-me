# =============================================================================
# Hydra Multi-Agent Job Application Assistant - Docker Image
# =============================================================================
# This is a multi-stage build that creates a single container with:
# - Python backend (Litestar API on port 8000)
# - Node.js frontend (Astro SSR on port 4321)
# - CrewAI runtime for multi-agent workflows
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build the frontend
# -----------------------------------------------------------------------------
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY web/frontend/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY web/frontend/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Production image
# -----------------------------------------------------------------------------
FROM python:3.12-slim

# Install Node.js for running the Astro SSR server
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (backend + runtime)
COPY requirements.txt ./requirements.txt
COPY web/backend/requirements.txt ./backend-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r backend-requirements.txt

# Copy application code
COPY runtime/ ./runtime/
COPY web/backend/ ./web/backend/
COPY agents/ ./agents/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./web/frontend/dist
COPY --from=frontend-builder /app/frontend/node_modules ./web/frontend/node_modules
COPY web/frontend/package.json ./web/frontend/package.json

# Create data directory for SQLite database
RUN mkdir -p /app/web/backend/data

# Environment variables
ENV PYTHONPATH=/app
ENV NODE_ENV=production
ENV BACKEND_URL=http://localhost:8000

# Expose ports
EXPOSE 4321 8000

# Copy startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:4321/ && curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
