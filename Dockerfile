# Dockerfile
FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome dependencies for Playwright
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install playwright && \
    playwright install chromium

# Copy application files
COPY . .


ENV YTDLP_CONFIG_PATH=/app/config/yt-dlp.conf
RUN mkdir -p /app/config && \
    echo "ffmpeg-location /usr/bin/ffmpeg\nno-check-certificate" > /app/config/yt-dlp.conf



# Runtime configuration
VOLUME ["/app/data"]
CMD ["python", "edbot_command.py"]
