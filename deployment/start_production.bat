@echo off
setlocal

echo ==============================================
echo   Counselling Support Agent
echo   Production Startup
echo ==============================================
echo.

set "BACKEND_ROOT=C:\Users\Chint\Desktop\counselling-support-agent\backend"
set "PYTHON_EXE=%BACKEND_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo ERROR: Virtual environment not found.
    echo Expected:
    echo %PYTHON_EXE%
    echo.
    pause
    exit /b 1
)

cd /d "%BACKEND_ROOT%"

echo Backend directory:
echo %CD%
echo.

echo Python executable:
echo %PYTHON_EXE%
echo.

echo Checking production configuration...
"%PYTHON_EXE%" -c "from app.core.config import settings; assert settings.environment == 'production'; assert settings.auth_secret_key; assert settings.database_encryption_key; print('Production configuration: PASS')"

if errorlevel 1 (
    echo.
    echo ERROR: Production configuration validation failed.
    echo Check the .env file in the project root.
    echo.
    pause
    exit /b 1
)

echo.
echo Starting Counselling Support Agent...
echo API: http://127.0.0.1:8000
echo Swagger UI: http://127.0.0.1:8000/docs
echo.
echo Press CTRL+C to stop the server.
echo.

"%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

endlocal