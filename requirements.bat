@echo off
setlocal
title System Dependency Installer
color 0b

echo.
echo   [ SYSTEM CONFIGURATION ]
echo   ------------------------
echo.

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    color 0c
    echo   [!] ERROR: Python is not installed.
    echo       Please install it from python.org
    pause
    exit /b 1
)

:: Update & Install
echo   [*] Updating package manager...
python -m pip install --upgrade pip >nul 2>nul

echo   [*] Installing core libraries...
pip install PyQt6 requests urllib3 >nul 2>nul

if %errorlevel% neq 0 (
    color 0c
    echo   [!] ERROR: Failed to install libraries.
    echo       Check your internet connection.
    pause
    exit /b 1
)

echo.
echo   [+] SYSTEM READY.
echo   Closing in 2 seconds...
timeout /t 2 >nul
exit /b 0