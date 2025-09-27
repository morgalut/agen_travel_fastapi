# travel_assistant/backend/Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ------------------ System Deps ------------------
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# ------------------ Install Ollama ------------------
RUN curl -fsSL https://ollama.com/download/ollama-linux-amd64.tgz \
  | tar -xz -C /usr/local/bin

# ------------------ Create Non-Root User ------------------
RUN groupadd -g 1000 appuser && useradd -m -u 1000 -g 1000 appuser

# ------------------ Working Dir ------------------
WORKDIR /app

# ------------------ Python Deps ------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------ App Code ------------------
COPY . .

# ------------------ Logging Setup ------------------
RUN mkdir -p /app/logs /tmp/app-logs \
 && chown -R 1000:1000 /app /tmp/app-logs

# ------------------ Switch User ------------------
USER appuser

# ------------------ Ports ------------------
EXPOSE 8000 11434

# ------------------ Default Env ------------------
ENV LOG_DIR=/app/logs \
    HOST=0.0.0.0 \
    PORT=8000 \
    LLM_API_URL=http://localhost:11434/api/generate

# ------------------ Start Both Ollama + FastAPI ------------------
CMD ollama serve & \
    uvicorn main:app --host 0.0.0.0 --port 8000
