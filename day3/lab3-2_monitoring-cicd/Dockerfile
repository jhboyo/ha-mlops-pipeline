# Dockerfile for California Housing Model Serving
# 
# KServe/Knative 환경에서 모델 서빙

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Verify critical packages are installed
RUN python -c "import numpy; import sklearn; import fastapi; import uvicorn; print('All packages installed successfully')"

# Copy application code
COPY src/ ./src/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    MODEL_NAME="california-housing" \
    MODEL_VERSION="v1.0" \
    PORT=8080

# Expose port
EXPOSE 8080

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the server using the dedicated entry point
CMD ["python", "src/main.py"]
