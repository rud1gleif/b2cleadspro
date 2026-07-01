FROM python:3.12-slim

WORKDIR /app

# System deps for Playwright and psycopg2
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

COPY . .

EXPOSE 8000
