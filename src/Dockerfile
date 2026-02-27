# Multi-stage Dockerfile for SSH Monitor
# Build targets: local, production

# ============================================
# Base stage - shared dependencies
# ============================================
FROM python:3.12-slim as base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For psycopg2
    libpq-dev \
    gcc \
    # For SSH key generation
    openssh-client \
    # For healthchecks and debugging
    curl \
    iputils-ping \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Local development stage
# ============================================
FROM base as local

# Install Node.js for Tailwind CSS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements/base.txt requirements/local.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/local.txt

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Default command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ============================================
# Production stage
# ============================================
FROM base as production

# Copy requirements and install Python dependencies
COPY requirements/base.txt requirements/production.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy project files
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Create logs directory
RUN mkdir -p logs

# Collect static files
RUN python manage.py collectstatic --noinput --settings=ssh_monitor.settings.production || true

# Expose port
EXPOSE 8000

# Production command with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "ssh_monitor.wsgi:application"]
