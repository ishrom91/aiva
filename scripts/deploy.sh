#!/bin/bash

# Deployment script for Aiva AI Bot

set -e  # Exit immediately if a command exits with a non-zero status

echo "Starting deployment of Aiva AI Bot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# Load environment variables
export $(cat .env | xargs)

# Pull latest changes
git pull origin main

# Build and deploy with Docker Compose
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Check if services are running
if docker-compose -f docker/docker-compose.yml ps | grep -q "Up"; then
    echo "Deployment successful!"
else
    echo "Some services failed to start. Checking logs..."
    docker-compose -f docker/docker-compose.yml logs
    exit 1
fi

echo "Deployment completed successfully!"