# Python backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py .
COPY dataset/ ./dataset/
COPY checkpoints/ ./checkpoints/

# Create directory for ChromaDB persistence
RUN mkdir -p /app/chroma_db

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=api_server.py

# Run the Flask server
CMD ["python", "api_server.py"]
