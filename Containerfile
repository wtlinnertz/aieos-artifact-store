# AIEOS artifact-store container image.
# Multi-stage: builder installs deps, runtime is a slim image with just what
# the health server + ingest/query CLI need.

ARG PYTHON_VERSION=3.11

FROM docker.io/library/python:${PYTHON_VERSION}-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM docker.io/library/python:${PYTHON_VERSION}-slim AS runtime
ARG VERSION=unknown
LABEL org.opencontainers.image.title="aieos-artifact-store"
LABEL org.opencontainers.image.source="https://github.com/wtlinnertz/aieos-artifact-store"
LABEL org.opencontainers.image.version="${VERSION}"

# Non-root
RUN useradd --create-home --uid 10001 aieos
USER aieos
WORKDIR /home/aieos/app

# Bring in the installed user-site from the builder.
COPY --from=builder /root/.local /home/aieos/.local
ENV PATH=/home/aieos/.local/bin:$PATH

COPY --chown=aieos:aieos src/ ./src/
COPY --chown=aieos:aieos pytest.ini VERSION README.md ./

EXPOSE 8080

# Default entrypoint: health server. Other commands (ingest, query) are
# invocable via `python -m src.ingest` / `python -m src.query` as one-shot
# CronJob workloads.
CMD ["python", "-m", "src.server"]
