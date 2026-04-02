@echo off
setlocal
title Sistema PQR - Iniciando servicios...
color 0A
echo.
echo ====================================
echo   SISTEMA PQR - AUTOMATIZACION IA
echo ====================================
echo.

set "SRC_ROOT=%~dp0"
set "BACKEND_DIR=%SRC_ROOT%backend"
set "FRONTEND_DIR=%SRC_ROOT%frontend"
set "PYTHON_EXE=python"

if not exist "%BACKEND_DIR%\app\api\main.py" (
	echo ERROR: No se encontro el backend en %BACKEND_DIR%
	pause
	exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
	echo ERROR: No se encontro el frontend en %FRONTEND_DIR%
	pause
	exit /b 1
)

if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
	set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"
)

echo [1/3] Preparando base de datos JSON...
cd /d "%BACKEND_DIR%"
"%PYTHON_EXE%" -m app.logic.seed_json_db
if errorlevel 1 (
	echo WARNING: No se pudo seedear la base de datos. Se iniciaran servicios igualmente.
)

echo [2/3] Iniciando Backend (FastAPI)...
start "Backend-PQR" cmd /k "cd /d ""%BACKEND_DIR%"" && set DB_MODE=json && ""%PYTHON_EXE%"" -m uvicorn app.api.main:app --reload --port 8000"

timeout /t 4 /nobreak >nul

echo [3/3] Iniciando Frontend (React)...
if not exist "%FRONTEND_DIR%\node_modules" (
	echo Instalando dependencias de frontend...
	cd /d "%FRONTEND_DIR%"
	call npm install
)
start "Frontend-PQR" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo ====================================
echo   Servicios iniciados!
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:5173
echo ====================================
pause