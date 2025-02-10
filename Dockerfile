FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in two steps to handle conflicts
COPY requirements.txt .
RUN pip install --no-cache-dir numpy>=1.22.5,<2.0.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8001

# Use PORT environment variable from Railway
CMD uvicorn github_agent_endpoint:app --host 0.0.0.0 --port ${PORT:-8000}
