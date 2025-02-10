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
ENV PYTHONUNBUFFERED=1

# Add healthcheck with much longer start period for Railway
HEALTHCHECK --interval=30s --timeout=30s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Create a startup script with detailed environment debugging
RUN echo '#!/bin/bash\n\
PORT="${PORT:-8000}"\n\
echo "[$(date)] ========== Starting server initialization =========="\n\
echo "[$(date)] Environment variables:"\n\
echo "OPENAI_API_KEY length: ${#OPENAI_API_KEY}"\n\
if [ -n "$OPENAI_API_KEY" ]; then\n\
    echo "OPENAI_API_KEY is set and starts with: ${OPENAI_API_KEY:0:10}..."\n\
else\n\
    echo "WARNING: OPENAI_API_KEY is not set!"\n\
fi\n\
echo "GITHUB_TOKEN length: ${#GITHUB_TOKEN}"\n\
echo "SUPABASE_URL: $SUPABASE_URL"\n\
echo "SUPABASE_SERVICE_KEY length: ${#SUPABASE_SERVICE_KEY}"\n\
echo "BEARER_TOKEN length: ${#BEARER_TOKEN}"\n\
echo "[$(date)] ========== Python environment =========="\n\
python3 -c "import os; print(f\"OPENAI_API_KEY in Python env: {bool(os.getenv(\"OPENAI_API_KEY\"))}\")" || echo "Failed to check OPENAI_API_KEY in Python"\n\
echo "[$(date)] ========== Starting server =========="\n\
exec uvicorn github_agent_endpoint:app --host 0.0.0.0 --port "$PORT" --log-level debug --timeout-keep-alive 75' > /app/start.sh && \
    chmod +x /app/start.sh

# Use the startup script
CMD ["/app/start.sh"]