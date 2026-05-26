FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# psycopg[binary] ships its own libpq; libpq5 kept for safety + Postgres CLI tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq5 postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY pyproject.toml alembic.ini ./
COPY src ./src
COPY migrations ./migrations
COPY scripts ./scripts
COPY config ./config
RUN mkdir -p data/resumes data/tailored_resumes data/cover_letters

EXPOSE 8000

# Run migrations, then the API. DATABASE_URL must be set in the environment.
CMD ["sh", "-c", "alembic -c alembic.ini upgrade head && uvicorn architect_job_agent.presentation.api.app:app --host 0.0.0.0 --port 8000 --app-dir src"]
