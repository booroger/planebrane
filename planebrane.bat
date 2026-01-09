@echo off
REM ============================================
REM  PlaneBrane - Startup Script
REM  Runs both backend and frontend servers
REM ============================================

setlocal EnableDelayedExpansion

echo.
echo ========================================
echo   PlaneBrane - Starting Application
echo ========================================
echo.

REM Store the project root directory
set PROJECT_ROOT=%~dp0

REM ----------------------------------------
REM  Start Backend Server
REM ----------------------------------------
echo [1/2] Starting Backend Server (FastAPI on port 8000)...

REM Check if .venv exists and activate it
if exist "%PROJECT_ROOT%.venv\Scripts\activate.bat" (
    echo      Using virtual environment...
    cd /d "%PROJECT_ROOT%"
    start "PlaneBrane Backend" cmd /k "call .venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
) else (
    echo      No virtual environment found, using system Python...
    cd /d "%PROJECT_ROOT%"
    start "PlaneBrane Backend" cmd /k "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
)

echo      Backend starting at: http://localhost:8000
echo.

REM Give the backend a moment to start
timeout /t 3 /nobreak > nul

REM ----------------------------------------
REM  Start Frontend Server
REM ----------------------------------------
echo [2/2] Starting Frontend Server (Vite on port 5173)...

cd /d "%PROJECT_ROOT%frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo      Installing dependencies first...
    call npm install
)

REM Start frontend with --open flag to automatically open browser
start "PlaneBrane Frontend" cmd /k "npm run dev -- --open"

echo      Frontend starting at: http://localhost:5173
echo.

echo ========================================
echo   PlaneBrane is starting up!
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo.
echo   Browser will open automatically when ready.
echo   Close the terminal windows to stop the servers.
echo ========================================
echo.

endlocal
