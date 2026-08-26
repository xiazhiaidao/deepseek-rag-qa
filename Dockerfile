FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_ENDPOINT=https://hf-mirror.com \
    HF_HUB_DISABLE_XET=1 \
    DATA_DIR=/app/data

WORKDIR /app

# Install system dependencies required by some Python packages (optional but safe)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app ./app
COPY web ./web
COPY scripts ./scripts
COPY data/knowledge ./data/knowledge

# Create runtime data directories
RUN mkdir -p /app/data/uploads /app/data/vector_index /app/data/models

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]