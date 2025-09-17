# syntax=docker/dockerfile:1

# Build stage not necessary; use slim Python runtime
FROM python:3.13-slim

# Set envs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=True \
    PORT=8000

# Create a non-root user
RUN useradd -m appuser

# Workdir
WORKDIR /app

# Install system deps if needed (none currently)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential && rm -rf /var/lib/apt/lists/*

# Copy dependency files first
COPY pyproject.toml* poetry.lock* ./

RUN pip install poetry==2.2.0

# Copy application code
COPY . .

RUN poetry install

# Ensure uploads dir exists and is writable
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# Switch to non-root
USER appuser

# Expose and default command using Uvicorn
EXPOSE 8000

# Use app:app as ASGI if running in container runtime directly
# But keep default command to run app.py which starts uvicorn
CMD ["poetry", "run", "python", "app.py"]
