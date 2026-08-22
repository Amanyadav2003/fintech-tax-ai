@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ==========================================
echo   TaxMate AI - Ultimate Starter
echo ==========================================
echo.
echo MANUAL COMMAND TIP:
echo To run backend manually in PowerShell, use semicolon not ampersand:
echo   cd backend; python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
echo.
echo What would you like to do?
echo [1] Start All Services (Local - Python/Node)
echo [2] Start with Docker
echo [3] Stop All Services
echo [4] View Logs
echo [5] Reset Database (DELETE ALL DATA!)
echo [6] Exit
echo.

set /p CHOICE="Enter choice (1-6): "

if "%CHOICE%"=="1" goto START_LOCAL
if "%CHOICE%"=="2" goto START_DOCKER
if "%CHOICE%"=="3" goto STOP_ALL
if "%CHOICE%"=="4" goto VIEW_LOGS
if "%CHOICE%"=="5" goto RESET_DB
if "%CHOICE%"=="6" exit /b 0

echo Invalid choice
goto :EOF

REM ======================================
REM START LOCAL (Python + Node)
REM ======================================
:START_LOCAL
echo.
echo [INFO] Starting TaxMate AI locally...

REM Check structure
if not exist "backend\app\main.py" (
  echo [ERROR] backend\app\main.py not found
  pause
  exit /b 1
)
if not exist "frontend\package.json" (
  echo [ERROR] frontend\package.json not found
  pause
  exit /b 1
)
echo [OK] Project structure validated

REM Check Python
where python >nul 2>nul || (
  echo [ERROR] Python not found. Install Python 3.11+
  pause
  exit /b 1
)
python -c "import fastapi, uvicorn, sqlalchemy" >nul 2>nul || (
  echo [INFO] Installing backend dependencies...
  cd backend
  pip install -q -r requirements.txt
  cd ..
)
echo [OK] Python/Backend ready

REM Check Node
where npm >nul 2>nul || (
  echo [ERROR] Node.js not found. Install Node.js 16+
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo [INFO] Installing frontend dependencies...
  cd frontend && call npm install --silent && cd ..
)
echo [OK] Node/Frontend ready

REM Find free ports
set BACKEND_PORT=5000
set FRONTEND_PORT=3001

:CHECK_BACKEND
netstat -aon | findstr :%BACKEND_PORT% | findstr LISTENING >nul
if not errorlevel 1 (
  set /a BACKEND_PORT+=1
  if %BACKEND_PORT% gtr 5100 (
    echo [ERROR] No available backend port
    pause
    exit /b 1
  )
  goto CHECK_BACKEND
)

:CHECK_FRONTEND
netstat -aon | findstr :%FRONTEND_PORT% | findstr LISTENING >nul
if not errorlevel 1 (
  set /a FRONTEND_PORT+=1
  if %FRONTEND_PORT% gtr 3100 (
    echo [ERROR] No available frontend port
    pause
    exit /b 1
  )
  goto CHECK_FRONTEND
)

echo [OK] Backend: %BACKEND_PORT%, Frontend: %FRONTEND_PORT%

REM Check PostgreSQL
netstat -aon | findstr :5432 | findstr LISTENING >nul
if errorlevel 1 (
  echo [WARN] PostgreSQL not detected on :5432
  echo [WARN] Start PostgreSQL or services may fail
)

REM Start services
echo [START] Backend...
start "TAXMATE_BACKEND" cmd /k "cd /d "%CD%\backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"
timeout /t 3 >nul

echo [START] Frontend...
start "TAXMATE_FRONTEND" cmd /k "cd /d "%CD%\frontend" && npm start"
timeout /t 5 >nul

echo [INFO] Opening browser...
start "" http://127.0.0.1:%FRONTEND_PORT%

echo.
echo ==========================================
echo   ALL SERVICES STARTED
echo ==========================================
echo Frontend: http://127.0.0.1:%FRONTEND_PORT%
echo Backend:  http://127.0.0.1:%BACKEND_PORT%
echo API Docs: http://127.0.0.1:%BACKEND_PORT%/docs
echo.
echo Close the service windows to stop them.
echo.
pause
exit /b 0

REM ======================================
REM START DOCKER
REM ======================================
:START_DOCKER
echo.
echo [INFO] Starting with Docker...

docker --version >nul 2>nul || (
  echo [ERROR] Docker not installed
  pause
  exit /b 1
)

docker-compose --version >nul 2>nul || (
  echo [ERROR] Docker Compose not installed
  pause
  exit /b 1
)

echo [START] Docker Compose...
docker-compose up -d

if errorlevel 1 (
  echo [ERROR] Docker Compose failed
  pause
  exit /b 1
)

timeout /t 10 >nul

echo.
echo ==========================================
echo   DOCKER SERVICES STARTED
echo ==========================================
echo Frontend: http://localhost:3001
echo Backend:  http://localhost:5000
echo API Docs: http://localhost:5000/docs
echo.
echo To view logs: docker-compose logs -f
echo To stop:     docker-compose down
echo.
pause
exit /b 0

REM ======================================
REM STOP ALL
REM ======================================
:STOP_ALL
echo.
echo [INFO] Stopping all services...

taskkill /FI "WINDOWTITLE eq TAXMATE_BACKEND*" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq TAXMATE_FRONTEND*" /F >nul 2>nul

docker-compose down >nul 2>nul

echo [OK] All services stopped
pause
exit /b 0

REM ======================================
REM VIEW LOGS
REM ======================================
:VIEW_LOGS
echo.
set /p LOG_CHOICE="View [1] Docker Logs or [2] Backend Logs? Enter 1 or 2: "

if "%LOG_CHOICE%"=="1" (
  docker-compose logs -f
) else if "%LOG_CHOICE%"=="2" (
  if exist "backend\logs" (
    type backend\logs\app.log
  ) else (
    echo [ERROR] No backend logs found
  )
) else (
  echo Invalid choice
)
pause
exit /b 0

REM ======================================
REM RESET DATABASE
REM ======================================
:RESET_DB
echo.
echo [WARN] This will DELETE all database data!
set /p CONFIRM="Type 'YES' to confirm: "

if not "%CONFIRM%"=="YES" (
  echo Cancelled.
  pause
  exit /b 0
)

echo [INFO] Resetting database...

if exist "backend\reset_db.py" (
  cd backend
  python reset_db.py
  cd ..
  echo [OK] Database reset complete
) else (
  echo [ERROR] reset_db.py not found
)

pause
exit /b 0
