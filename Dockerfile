# ────────────────────────────────────────────────────────────────
#  SoliTrader ‒ Bot image
#  • runs as a non-root user (appuser)
#  • /app/uploads, /app/logs, /app/temp are writable
# ────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── basic Python settings ───────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PYTHONMALLOC=malloc

# ── system packages ─────────────────────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc g++ build-essential python3-dev \
        libpq-dev libffi-dev curl \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

# ── working directory ───────────────────────────────────────────
WORKDIR /app

# ── create non-root user early so we can chown later  ───────────
RUN groupadd -r appuser && useradd -r -g appuser appuser

# ── Python requirements (done as root) ──────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# ── project source code ─────────────────────────────────────────
COPY . .

# ── runtime directories + permissions ───────────────────────────
RUN mkdir -p /app/uploads /app/logs /app/temp && \
    chown -R appuser:appuser /app

# ── switch to non-root user for the rest of the image ───────────
USER appuser

# ── network / health-check / entrypoint ─────────────────────────
EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=2 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "api.main"]

