FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=2.3.2
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies. Default to prod (--only main)
# override with POETRY_INSTALL_ARGS=""
ARG POETRY_INSTALL_ARGS="--only main"
RUN poetry install --no-interaction --no-ansi ${POETRY_INSTALL_ARGS}

# Copy project
COPY . .

EXPOSE 8501
