@echo off
echo ==========================================
echo    Multilinear Narrative System Startup
echo ==========================================
echo.

echo [1/2] Starting Backend (FastAPI on Port 8095)...
start cmd /k "python -m foundation_platform.api.api"

echo [2/2] Starting Frontend (Vue on Port 5173)...
cd editor-web
start cmd /k "npm run dev"

echo.
echo Startup instructions dispatched!
echo Close this window when you're done, but keep the two new CMD windows open.
pause
