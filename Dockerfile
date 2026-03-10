FROM ghcr.io/astral-sh/uv:0.9.12-bookworm AS uv

# -----------------------------------
# STAGE 1: prod stage
# Only install main dependencies
# -----------------------------------
FROM python:3.13-slim-bookworm AS prod
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl gnupg2 ca-certificates apt-transport-https lsb-release \
    unixodbc-dev \
    && mkdir -p /etc/apt/keyrings \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get purge -y gnupg2 \
    && apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# OpenSSL configuration for older SQL Server versions
ENV OPENSSL_CONF=/etc/ssl/openssl.cnf
COPY openssl.cnf /etc/ssl/openssl.cnf

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/usr/local
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_NO_MANAGED_PYTHON=1

WORKDIR /app/src

COPY pyproject.toml uv.lock ./
RUN --mount=from=uv,source=/usr/local/bin/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

COPY . .

RUN --mount=from=uv,source=/usr/local/bin/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

CMD ["/usr/local/bin/python", "-m", "ivanpham_chatbot_assistant"]

# -----------------------------------
# STAGE 3: development build
# Includes dev dependencies
# -----------------------------------
FROM prod AS dev

RUN --mount=from=uv,source=/usr/local/bin/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --all-groups
