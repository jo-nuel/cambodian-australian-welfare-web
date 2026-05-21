FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies (separate layer so it's cached between deploys)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Copy source code
COPY . .

# Collect static files at build time
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Migrate then start Gunicorn on Railway's assigned public port.
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn a_core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
