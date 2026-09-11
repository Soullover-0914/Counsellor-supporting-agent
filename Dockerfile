# Agent 66 — public production image (frontend + API, same origin)

FROM node:22-bookworm AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    sqlcipher \
    libsqlcipher-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

ENV CFLAGS="-I/usr/include/sqlcipher" \
    LDFLAGS="-L/usr/lib/x86_64-linux-gnu -lsqlcipher" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FRONTEND_DIST=/app/frontend/dist \
    DATABASE_PATH=/var/data/counselling_agent_encrypted.db

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY --from=frontend /frontend/dist /app/frontend/dist

RUN mkdir -p /var/data

WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
