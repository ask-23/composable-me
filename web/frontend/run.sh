#!/bin/bash
# Run the Hydra web frontend (Astro dev server)

cd "$(dirname "$0")" || exit 1

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Run the dev server
echo "Starting Astro dev server on http://localhost:4321"
echo "Make sure the backend is running on http://localhost:8000"
npm run dev
