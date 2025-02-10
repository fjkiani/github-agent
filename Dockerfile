
# Default port (will be overridden by Railway's PORT)
ENV PORT=8000

# Add healthcheck with much longer start period for Railway
HEALTHCHECK --interval=15s --timeout=10s --start-period=90s --retries=10 \
    CMD curl -f http://localhost:8000/health || exit 1


# Create a startup script
RUN echo '#!/bin/bash\n\
PORT="${PORT:-8000}"\n\
echo "Starting server on port: $PORT"\n\
exec uvicorn github_agent_endpoint:app --host 0.0.0.0 --port "$PORT" --log-level debug --timeout-keep-alive 75' > /app/start.sh && \
    chmod +x /app/start.sh
# Use the startup script
CMD ["/app/start.sh"]