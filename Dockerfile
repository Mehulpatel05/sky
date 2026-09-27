FROM python:3.10-slim

# Install system dependencies (FFmpeg, OpenCV dependencies, git, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Pre-render motion graphic asset datasets
RUN python -m src.asset_builder

# Start Telegram Bot application
CMD ["python", "main.py"]
