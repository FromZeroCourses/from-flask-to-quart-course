FROM ubuntu:20.04

# Install packages
RUN apt-get update && apt-get install -y \
    build-essential \
    make \
    gcc \
    git \
    unzip \
    wget \
    python3-dev \
    python3-pip \
    python-is-python3

ENV PIP_DISABLE_PIP_VERSION_CHECK=on

# Install uv
RUN pip3 install uv

# set "counter_app" as the working directory from which CMD, RUN, ADD references
WORKDIR /counter_app

# keep the virtual environment outside the mounted project directory
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# setup uv
COPY pyproject.toml /counter_app/
RUN uv sync --no-install-project

# now copy all the files in this directory to /code
COPY . .

# Listen to port 5000 at runtime
EXPOSE 5000

# Define our command to be run when launching the container
CMD uv run quart run --host 0.0.0.0
