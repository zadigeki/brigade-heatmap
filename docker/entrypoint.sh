#!/bin/bash
# Brigade Electronics Heatmap System - Docker Entrypoint

set -e

# Create data directory if it doesn't exist
mkdir -p /app/data /app/logs

# Initialize database schema if database doesn't exist
if [ ! -f "/app/data/devices.db" ]; then
    echo "Initializing database schema..."
    python -c "
from database import DatabaseManager
import os
os.environ['DATABASE_PATH'] = '/app/data/devices.db'
db = DatabaseManager()
print('Database initialized successfully')
"
fi

# Execute the main command
exec "$@"