FROM python:3.10-slim

# Manually install ALL Chromium runtime dependencies
# This REPLACES 'playwright install-deps' which fails on Render
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates procps libxss1 libnss3 libnspr4 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 \
    libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libxshmfence1 libx11-xcb1 fonts-liberation xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ONLY install browser binary — NO system deps step
RUN playwright install chromium

COPY . .
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]