FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

# The base image ships a yarnpkg apt source with an unverifiable GPG key,
# which breaks `apt-get update`. We don't need Node/Yarn, so drop it.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# System deps needed to fetch/unpack the DuckDB CLI, plus make for the
# project Makefile
RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip make \
    && rm -rf /var/lib/apt/lists/*

# uv - fast Python package manager. Project dependencies (duckdb, pandas,
# requests, python-dotenv) are installed via `uv sync` against
# pyproject.toml/uv.lock - see devcontainer.json's postCreateCommand.
RUN pip install --no-cache-dir uv

# DuckDB CLI binary
RUN curl -fsSL https://github.com/duckdb/duckdb/releases/latest/download/duckdb_cli-linux-amd64.zip -o /tmp/duckdb_cli.zip \
    && unzip /tmp/duckdb_cli.zip -d /usr/local/bin \
    && rm /tmp/duckdb_cli.zip \
    && chmod +x /usr/local/bin/duckdb
