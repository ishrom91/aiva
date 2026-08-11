#!/bin/bash

# Deployment script for Aiva AI Bot

set -e

cd ~/aiva

echo "Pulling latest code..."
git pull

echo "Building and starting services..."
docker compose -f docker/docker-compose.yml up -d --build

echo "Checking service status..."
docker compose ps