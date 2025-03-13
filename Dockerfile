# Multi-stage Dockerfile for Azure DevOps CLI Learning Project Python Chatbot

# ===== Base stage with common dependencies =====
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI for Azure DevOps operations
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Azure DevOps CLI extension
RUN az extension add --name azure-devops

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# ===== Development stage =====
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytest-watch ipython

# Set environment variables for development
ENV ENVIRONMENT=development \
    LOG_LEVEL=DEBUG

# Copy source code
COPY . .

# Command to run the application in development mode
CMD ["python", "-m", "uvicorn", "src.chatbot.api.endpoints.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ===== Production stage =====
FROM base as production

# Install production dependencies only
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for production
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Copy source code
COPY src /app/src

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application in production mode
CMD ["python", "-m", "uvicorn", "src.chatbot.api.endpoints.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 