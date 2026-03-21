FROM python:3.14-slim@sha256:fb83750094b46fd6b8adaa80f66e2302ecbe45d513f6cece637a841e1025b4ca AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv@sha256:031ddbc79275e351a43cbb66f64d8cd314cc78c3878898f4ab4f147b092e8e2d /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install production dependencies into /app/.venv
RUN uv sync --no-dev --frozen


FROM python:3.14-slim@sha256:fb83750094b46fd6b8adaa80f66e2302ecbe45d513f6cece637a841e1025b4ca AS runtime

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy the virtual environment and source from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Make the venv the active Python environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

USER appuser

ENTRYPOINT ["python", "-m", "annuaire_mcp.main"]
