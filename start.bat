@echo off
title B2C Leads Pro
color 0A

echo.
echo  ============================================
echo   B2C Leads Pro - Starting...
echo  ============================================
echo.

cd /d "%~dp0"

echo [1/3] Pulling latest code from GitHub...
git pull
echo.

echo [2/3] Starting Docker containers...
docker compose up -d
echo.

echo [3/3] Waiting for API to be ready...
timeout /t 5 /nobreak >nul

echo.
echo  ============================================
echo   Opening B2C Leads Pro in your browser...
echo  ============================================
echo.

start http://localhost:8000

echo  Done! App is running at http://localhost:8000
echo  To stop, run:  docker compose down
echo.
pause
