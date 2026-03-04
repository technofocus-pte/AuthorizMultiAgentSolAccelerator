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

echo "Installing Azure CLI extensions..."
az extension add --name containerapp --yes 2>/dev/null || echo "⚠️ containerapp extension install skipped"
az extension add --name ml --yes 2>/dev/null || echo "⚠️ ml extension install skipped"

echo "Setting up Backend..."
cd ./backend
pip install --upgrade pip
pip install -r requirements.txt || echo "⚠️ Backend dependency install had errors (non-fatal)"
cd ../

echo "Setting up Frontend..."
cd ./frontend
npm install
cd ../

echo "Setup complete! 🎉"
