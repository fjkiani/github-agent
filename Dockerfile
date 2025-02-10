FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir "numpy>=1.22.5,<2.0.0" && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Default port (will be overridden by Railway's PORT)
ENV PORT=8000

# Use PORT environment variable
CMD ["python", "github_agent_endpoint.py"]
