@echo off
title UIT Voice Assistant
echo.
echo ╔══════════════════════════════════════════════╗
echo ║        🎓 UIT Voice Assistant v1.0           ║
echo ║    AI-Powered College Information System     ║
echo ╚══════════════════════════════════════════════╝
echo.

:: Load .env file if it exists
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (.env) do (
        set "%%a=%%b"
    )
    echo [OK] Loaded environment from .env
)

:: Run the assistant
python main.py %*

pause
