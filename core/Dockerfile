# Python backend Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy project configuration first for better caching
COPY pyproject.toml .

# Install Python dependencies using uv
RUN uv pip install --system -e .

# Copy application code
COPY src/ ./src/
COPY pytest.ini .

# Create directories for data and models (mounted as volumes)
RUN mkdir -p /app/data /app/models/chroma_db /app/models/checkpoints

# Expose Flask port (3100)
EXPOSE 3100

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV FLASK_APP=src/server.py

# Run the Flask server
CMD ["python3", "src/server.py"]
