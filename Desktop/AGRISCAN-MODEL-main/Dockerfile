FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Dockerfile in AGRISCAN-MODEL-main/

# Set working directory


# Copy backend files
COPY backend/ .

# Copy frontend build
COPY frontend/dist/ frontend/dist/


# Install Python dependencies
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "testing:app", "--host", "0.0.0.0", "--port", "8000"]
