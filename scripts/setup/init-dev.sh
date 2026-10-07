#!/usr/bin/env bash
set -e

echo "=== Initializing SpaceLoop Development Environment ==="

if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed. Aborting."
    exit 1
fi

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Python is required but not installed. Aborting."
    exit 1
fi

echo "Installing frontend dependencies..."
npm install

echo "Installing backend dependencies..."
pip install -r requirements.txt

echo "Setup completed successfully! Run 'npm run dev' to start the frontend."
