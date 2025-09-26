# Dockerfile (backend)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps (curl optional)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Create user
RUN groupadd -g 1000 appuser && useradd -m -u 1000 -g 1000 appuser

WORKDIR /app

# Install deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY backend/ ./

# Prepare common writable dirs; some clouds mount rootfs read-only for the code layer,
# so we create a tmp logs dir as a fallback and chown /app in case we can write.
RUN mkdir -p /app/logs /tmp/app-logs \
 && chown -R 1000:1000 /app /tmp/app-logs

# Drop privileges
USER appuser

# Expose port (cloud platforms ignore EXPOSE but nice for docs)
EXPOSE 8000

# Default env – you can override in cloud
ENV LOG_DIR=/app/logs \
    HOST=0.0.0.0 \
    PORT=8000

# Start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
