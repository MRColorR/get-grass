#!/bin/bash
set -ex

echo "Ready to start"
# Check if the original entry point script exists
if [ -f /app/entrypoint.sh ]; then
  echo "Running the original entry point in the background..."
  /app/entrypoint.sh &
  echo "Original entry point is running."
  # Wait for 10 seconds
  sleep 10
fi

# Run the Python script
echo "Starting the Python script..."
python3 /app/grass-node_main.py
