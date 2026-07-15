# Multi-stage build: builder stage
FROM python:3.11-slim AS builder

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt


# Runtime stage
FROM python:3.11-slim AS runtime

# Create non-root user for security
RUN groupadd -r aivauser && useradd -r -g aivauser aivauser

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install dependencies
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY src ./src
COPY alembic.ini .

# Change ownership to non-root user
RUN chown -R aivauser:aivauser /app
USER aivauser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips", "*"]