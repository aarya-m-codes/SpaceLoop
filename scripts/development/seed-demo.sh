#!/usr/bin/env bash
set -e

echo "=== Seeding SpaceLoop Demo Data ==="

if [ -f "seed_data.py" ]; then
    python seed_data.py
    echo "Demo database seeded successfully from seed_data.py"
else
    echo "seed_data.py not found, skipping."
fi
