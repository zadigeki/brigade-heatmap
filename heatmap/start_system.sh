#!/bin/bash

echo "Brigade Electronics Monitoring System"
echo "====================================="
echo ""
echo "Starting the monitoring system..."
echo "Web interface will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the system"
echo ""

python3 run_system.py --host 0.0.0.0 --port 5000 --gps-interval 30