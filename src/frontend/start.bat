@echo off
echo ============================================
echo   Automatizacion Inteligente PQR - Startup
echo ============================================
echo.

echo [1/3] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [2/3] Checking Node.js environment...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 16+
    pause
    exit /b 1
)

echo.
echo Starting Backend (FastAPI) on port 8000...
start "Backend - PQR API" cmd /k "cd ..\backend && python -m uvicorn app.api.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo.
echo Starting Frontend (React) on port 5173...
start "Frontend - PQR UI" cmd /k "cd ..\frontend && npm run dev"

echo.
echo ============================================
echo   Both services are starting!
echo   
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   Docs:     http://localhost:8000/docs
echo ============================================
echo.
echo Demo Users:
echo   admin@pqr.com / admin123
echo   laura@pqr.com / super456
echo   carlos@pqr.com / agente789
echo   maria@pqr.com / user000
echo.
pause
