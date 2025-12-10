# syntax=docker/dockerfile:1
FROM python:3.11-slim AS runtime

WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copy project code
COPY backend ./backend
COPY frontend ./frontend

# Runtime environment
ENV APP_ENV=production \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# Start with gunicorn using exported WSGI app
CMD ["gunicorn", "-w", "3", "-k", "gthread", "--threads", "4", "-b", "0.0.0.0:5000", "backend.wsgi:app"]


