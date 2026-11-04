@echo off
setlocal

rem ============================================================
rem  Backend launcher - double-click to start the backend.
rem  Default absolute paths are set below; if they are missing,
rem  the script falls back to auto-detection.
rem  Edit the two paths to match your machine if needed.
rem ============================================================

rem ---- Default paths (absolute). Edit these to match your setup. ----
set "BACKEND_DIR=D:\child-learning\backend"
set "PYTHON=D:\child-learning\.venv\Scripts\python.exe"

rem ---- Backend fallback: locate by this script's own location ----
if not exist "%BACKEND_DIR%\app\main.py" set "BACKEND_DIR=%~dp0..\backend"
if not exist "%BACKEND_DIR%\app\main.py" set "BACKEND_DIR=%~dp0backend"

rem ---- Python fallback: virtualenv derived from backend, then PATH ----
if not exist "%PYTHON%" set "PYTHON=%BACKEND_DIR%\..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"

rem ---- Validate backend ----
if not exist "%BACKEND_DIR%\app\main.py" (
    echo [ERROR] Cannot find backend\app\main.py
    echo Edit BACKEND_DIR at the top of this script, or place this
    echo script next to the "backend" folder and try again.
    echo.
    pause
    exit /b 1
)

rem ---- Validate python ----
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found: %PYTHON%
    echo Edit PYTHON at the top of this script, or install Python 3.12
    echo and add it to PATH, then try again.
    echo.
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"

echo ============================================================
echo Starting backend : %BACKEND_DIR%
echo Python            : %PYTHON%
echo Open http://localhost:8000/ in your browser.
echo Press Ctrl+C to stop.
echo ============================================================
echo.

"%PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo.
echo Backend stopped.
pause
