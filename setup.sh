#!/bin/bash

# Create necessary directories
mkdir -p data/storage/uploads data/storage/results data/temp

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "Creating Docker containers..."
docker-compose build

echo "Setup complete! Run 'docker-compose up -d' to start the application." 