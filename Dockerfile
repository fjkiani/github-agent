FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage cache
COPY requirements.txt .

# Install Python dependencies in a separate layer
RUN pip install --no-cache-dir "numpy>=1.22.5,<2.0.0"
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Default port (will be overridden by Railway's PORT)
ENV PORT=8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use PORT environment variable
CMD ["python", "github_agent_endpoint.py"]
