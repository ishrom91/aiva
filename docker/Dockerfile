# Multi-stage build for Aiva AI Bot

# Builder stage
FROM python:3.11-slim as builder

WORKDIR /install

COPY requirements.txt .

RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy source code
COPY ./src ./src
COPY pyproject.toml .
COPY alembic.ini .

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port 8000"]