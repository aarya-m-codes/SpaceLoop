#!/usr/bin/env bash
set -e

echo "=== SpaceLoop Security Audit & Scanner ==="

echo "1. Checking NPM dependencies..."
npm audit || true

echo "2. Checking Python dependencies with Bandit (if installed)..."
if command -v bandit &> /dev/null; then
    bandit -r backend/ -ll || true
fi

echo "Security scan complete."
