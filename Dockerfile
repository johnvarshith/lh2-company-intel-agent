FROM python:3.10-slim

# Install minimal deps for headless Chromium on low-RAM environments
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg libnss3 libxss1 libasound2 libatk-bridge2.0-0 \
    libgtk-3-0 libdrm2 libxkbcommon0 libgbm1 libxcomposite1 \
    libxdamage1 libxrandr2 libpango-1.0-0 libcairo2 libcups2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ONLY chromium (not firefox/webkit) to save space/RAM
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# Render free tier uses port 10000 by default via $PORT env var
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
