# ─── TruthLens Backend Dockerfile ───
# Multi-stage: build dependencies → lean runtime image
# Uses gunicorn + uvicorn workers for production

# ─── Stage 1: Builder ───
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for building native extensions (psycopg2, bcrypt, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
# Install huggingface_hub for runtime model download at container startup
RUN pip install --no-cache-dir --prefix=/install "huggingface_hub==0.24.6"
# Install gunicorn separately (not in requirements.txt)
RUN pip install --no-cache-dir --prefix=/install gunicorn==23.0.0


# ─── Stage 2: Runtime ───
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system deps (libpq for psycopg2, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r truthlens && useradd -r -g truthlens -d /app -s /sbin/nologin truthlens

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create scripts directory in case it wasn't included
RUN mkdir -p /app/scripts

# Create directories for models and data
RUN mkdir -p /app/models /app/data && chown -R truthlens:truthlens /app

# Switch to non-root user
USER truthlens

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with gunicorn + uvicorn workers
# Download ML models from Hugging Face Hub at startup (if HF_MODEL_REPO is set),
# then start gunicorn. Script exits 0 on failure so we degrade gracefully.
CMD ["sh", "-c", "python /app/scripts/download_models.py && gunicorn app.main:app -c gunicorn.conf.py"]
