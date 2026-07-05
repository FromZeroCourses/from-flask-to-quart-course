FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick libmagickwand-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /quartfeed_app
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

COPY pyproject.toml uv.lock /quartfeed_app/
RUN uv sync --no-install-project

COPY . .

EXPOSE 5000
# --reload restarts the dev server when a source file changes. The project is
# bind-mounted (see docker-compose.yml), so editing files on the host updates
# the running app immediately — no container restart needed.
CMD uv run quart run --host 0.0.0.0 --reload
