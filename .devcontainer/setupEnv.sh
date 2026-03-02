#!/bin/sh

echo "Pull latest code for the current branch"
git fetch
git pull

set -e

# Ensure azd is available (fallback if Dev Container Feature failed)
if ! command -v azd >/dev/null 2>&1 || ! azd version >/dev/null 2>&1; then
  echo "Installing Azure Developer CLI (azd)..."
  curl -fsSL https://aka.ms/install-azd.sh | bash
  echo "azd installed: $(azd version)"
else
  echo "azd already available: $(azd version)"
fi

echo "Setting up Backend..."
cd ./backend
pip install -r requirements.txt
cd ../

echo "Setting up Frontend..."
cd ./frontend
npm install
cd ../

echo "Setup complete! 🎉"
