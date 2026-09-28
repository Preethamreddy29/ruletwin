FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY apps/api/src ./apps/api/src
RUN python -m pip wheel --wheel-dir /wheels .

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/ruletwin/.local/bin:${PATH}"
RUN groupadd --gid 10001 ruletwin \
    && useradd --uid 10001 --gid ruletwin --create-home --shell /usr/sbin/nologin ruletwin
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY alembic.ini ./
COPY apps/api/migrations ./apps/api/migrations
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "ruletwin.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
