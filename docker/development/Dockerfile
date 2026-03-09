FROM python:3.12-slim

# Install system dependencies and WeasyPrint requirements
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    libpangocairo-1.0-0 \
    curl \
    && apt-get clean

# Install PostgreSQL client for pg_isready
RUN apt-get update && apt-get install -y postgresql-client && apt-get install -y gettext

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy Docker scripts
COPY docker/development/entrypoint.sh /entrypoint.sh
COPY docker/development/wait_for_db.sh /wait_for_db.sh
RUN chmod +x /entrypoint.sh /wait_for_db.sh

EXPOSE 8000

CMD ["/entrypoint.sh"]
