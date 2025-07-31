#!/bin/bash
# Brigade Electronics Heatmap System - Build and Test Script

set -e

echo "🐳 Building Brigade Electronics Heatmap Docker Container..."

# Build the Docker image
echo "Building Docker image..."
docker build -t brigade-heatmap:latest .

echo "✅ Docker image built successfully!"

# Test the image
echo "🧪 Testing Docker container..."

# Start container in background for testing
echo "Starting test container..."
docker run -d --name heatmap-test \
    -p 5001:5000 \
    -e BRIGADE_API_URL=http://host.docker.internal:12056 \
    -e BRIGADE_USERNAME=admin \
    -e BRIGADE_PASSWORD=admin \
    brigade-heatmap:latest

# Wait for container to start
echo "Waiting for container to start..."
sleep 10

# Test health endpoint
echo "Testing health endpoint..."
if curl -f http://localhost:5001/api/stats > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    docker logs heatmap-test
    docker stop heatmap-test && docker rm heatmap-test
    exit 1
fi

# Test heatmap page
echo "Testing heatmap page..."
if curl -f http://localhost:5001/ > /dev/null 2>&1; then
    echo "✅ Heatmap page accessible!"
else
    echo "❌ Heatmap page test failed!"
    docker logs heatmap-test  
    docker stop heatmap-test && docker rm heatmap-test
    exit 1
fi

# Show container logs
echo "📋 Container logs:"
docker logs heatmap-test

# Cleanup test container
echo "🧹 Cleaning up test container..."
docker stop heatmap-test && docker rm heatmap-test

echo ""
echo "🎉 Docker container build and test completed successfully!"
echo ""
echo "To run the system:"
echo "  docker-compose up -d"
echo ""
echo "To access the heatmap:"
echo "  http://localhost:5000"
echo ""