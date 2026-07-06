FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /counter_app
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

COPY pyproject.toml uv.lock /counter_app/
RUN uv sync --no-install-project

COPY . .

EXPOSE 5000
CMD uv run quart run --host 0.0.0.0
