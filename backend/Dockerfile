# Multi-stage build for Python backend
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies system-wide (accessible to all users)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Create non-root user first
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser && \
    apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder to system location
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app ./app

# Create directories for data and config with proper permissions
RUN mkdir -p /data /app/config && \
    chown -R appuser:appuser /app /data

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
