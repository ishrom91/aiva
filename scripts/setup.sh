#!/bin/bash

# Setup script for Aiva AI Bot deployment

set -e

echo "Updating system packages..."
sudo apt update

echo "Installing Docker and Docker Compose..."
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker

echo "Adding current user to docker group..."
sudo usermod -aG docker $USER

echo "Installing Yandex Cloud CLI (optional)..."
curl https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

echo "Setup completed!"