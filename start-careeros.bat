@echo off
setlocal enabledelayedexpansion
title CareerOS - Local Launcher
cd /d "%~dp0"

echo ============================================================
echo    CareerOS (Pacio) - one-click local launcher
echo    Runs everything on http://localhost:8000
echo ============================================================
echo.

REM --- Prerequisite checks -------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python is not installed or not on PATH.
  echo         Install Python 3.10+ from https://www.python.org/downloads/
  echo         IMPORTANT: tick "Add python.exe to PATH" during install.
  pause & exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js / npm is not installed or not on PATH.
  echo         Install Node 18+ from https://nodejs.org/  ^(LTS^)
  pause & exit /b 1
)

REM --- 1) Build the React UI once (skips if already built) -----------------
if not exist "frontend\build\index.html" (
  echo [1/3] Installing frontend packages and building the UI...
  echo       ^(one-time, can take 2-5 minutes - please wait^)
  pushd frontend
  call npm install || ( echo [ERROR] npm install failed & popd & pause & exit /b 1 )
  call npm run build || ( echo [ERROR] npm run build failed & popd & pause & exit /b 1 )
  popd
) else (
  echo [1/3] Frontend build already exists - skipping build.
)
echo.

REM --- 2) Install backend dependencies ------------------------------------
echo [2/3] Installing backend (Python) dependencies...
pushd backend
python -m pip install --upgrade pip >nul 2>nul
call python -m pip install -r requirements.txt || ( echo [ERROR] pip install failed & popd & pause & exit /b 1 )
echo.

REM --- 3) Launch the server (it also serves the built UI) ------------------
echo [3/3] Starting CareerOS...
echo.
echo    Open your browser at:  http://localhost:8000
echo    Press Ctrl+C in this window to stop the server.
echo.
python -m uvicorn server:app --host 0.0.0.0 --port 8000
popd
endlocal
