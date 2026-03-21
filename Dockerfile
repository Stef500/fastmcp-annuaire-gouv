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

# Health check for HTTP transport mode (MCP_TRANSPORT=http).
# Not applicable for stdio transport (default).
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen('http://localhost:' + os.getenv('MCP_PORT', '8000') + '/health')" 2>/dev/null || exit 1

ENTRYPOINT ["python", "-m", "annuaire_mcp.main"]
