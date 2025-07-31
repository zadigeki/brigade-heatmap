# Brigade Electronics Alarm Heatmap System - Docker Container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Copy entrypoint script and make executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create necessary directories
RUN mkdir -p logs data

# Set permissions
RUN chmod +x *.py

# Create non-root user for security
RUN useradd -m -u 1000 heatmap && \
    chown -R heatmap:heatmap /app
USER heatmap

# Expose port for web server
EXPOSE 5000

# Environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=web_server.py
ENV FLASK_ENV=production
ENV BRIGADE_API_URL=http://127.0.0.1:12056
ENV BRIGADE_USERNAME=admin
ENV BRIGADE_PASSWORD=admin
ENV DATABASE_PATH=/app/data/devices.db

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/stats || exit 1

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command - runs web server
CMD ["python", "web_server.py", "--host", "0.0.0.0", "--port", "5000"]