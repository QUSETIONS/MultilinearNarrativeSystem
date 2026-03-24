#!/bin/bash
echo "=========================================="
echo "   Multilinear Narrative System Startup"
echo "=========================================="
echo ""

echo "[1/2] Starting Backend (FastAPI on Port 8095)..."
python -m foundation_platform.api.api &
BACKEND_PID=$!

echo "[2/2] Starting Frontend (Vue on Port 5173)..."
cd editor-web
npm run dev

# If frontend exits, kill backend
kill $BACKEND_PID
