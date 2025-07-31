#!/bin/bash
# Brigade Electronics Heatmap System - Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
PROD_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prod|--production)
            PROD_MODE=true
            COMPOSE_FILE="docker-compose.prod.yml"
            shift
            ;;
        --env)
            ENV_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --prod, --production    Use production configuration"
            echo "  --env FILE             Use specific environment file"
            echo "  --help, -h             Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🐳 Brigade Electronics Heatmap Deployment${NC}"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed. Please install Docker Compose.${NC}"
    exit 1
fi

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  Environment file $ENV_FILE not found.${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${BLUE}📋 Copying .env.example to $ENV_FILE${NC}"
        cp .env.example "$ENV_FILE"
        echo -e "${YELLOW}⚠️  Please edit $ENV_FILE with your configuration before continuing.${NC}"
        echo -e "${YELLOW}   Press Enter to continue after editing the file...${NC}"
        read -r
    fi
fi

# Create data and logs directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p data logs

# Build and deploy
echo -e "${BLUE}🔨 Building and deploying containers...${NC}"
if [ "$PROD_MODE" = true ]; then
    echo -e "${BLUE}🏭 Using production configuration${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
else
    echo -e "${BLUE}🛠️  Using development configuration${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
fi

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 15

# Check service health
echo -e "${BLUE}🏥 Checking service health...${NC}"
if curl -f http://localhost:5000/api/stats > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Heatmap service is healthy!${NC}"
else
    echo -e "${RED}❌ Heatmap service health check failed${NC}"
    echo -e "${YELLOW}📋 Container logs:${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi

# Show deployment status
echo -e "${BLUE}📊 Deployment Status:${NC}"
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📍 Access URLs:${NC}"
echo "   Heatmap Interface: http://localhost:5000"
echo "   API Status:        http://localhost:5000/api/stats"
echo "   API Documentation: http://localhost:5000/api/"
echo ""
echo -e "${BLUE}📋 Management Commands:${NC}"
echo "   View logs:         docker-compose -f $COMPOSE_FILE logs -f"
echo "   Stop services:     docker-compose -f $COMPOSE_FILE down"
echo "   Restart services:  docker-compose -f $COMPOSE_FILE restart"
echo "   Update services:   docker-compose -f $COMPOSE_FILE pull && docker-compose -f $COMPOSE_FILE up -d"
echo ""

# Show initial statistics
echo -e "${BLUE}📈 Initial System Statistics:${NC}"
curl -s http://localhost:5000/api/stats | python3 -m json.tool 2>/dev/null || echo "Statistics not available yet"