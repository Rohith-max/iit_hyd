#!/usr/bin/env bash
# Build script for Render.com deployment
# Builds frontend, copies to backend/static, installs Python deps, trains models
set -o errexit

echo "=== Installing Python dependencies ==="
cd backend
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Building frontend ==="
cd ../frontend
npm install
npm run build

echo "=== Copying frontend build to backend/static ==="
rm -rf ../backend/static
cp -r dist ../backend/static

echo "=== Creating data and models directories ==="
mkdir -p ../backend/data ../backend/models

echo "=== Build complete ==="
