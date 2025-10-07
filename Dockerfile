FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.8.23 /uv /uvx /bin/

# Create a non-root user
RUN useradd -m appuser

# Workdir
WORKDIR /app/web

# Copy dependency files first
COPY pyproject.toml* uv.lock* ./

RUN uv sync --frozen --no-cache

# Copy application code
COPY src .

# Ensure uploads dir exists and is writable
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# Switch to non-root
USER appuser

# Expose and default command using Uvicorn
EXPOSE 80

# Run the application.
CMD ["/app/web/.venv/bin/fastapi", "run", "app/app.py", "--port", "80", "--host", "0.0.0.0"]
