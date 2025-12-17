@echo off
setlocal EnableDelayedExpansion
:: Force UTF-8 for solid block characters
chcp 65001 >nul

:: Window Configuration
title System Dependency Manager
mode con: cols=70 lines=25
color 0B

:: --- CONFIGURATION ---
set "PACKAGES=PyQt6 requests urllib3"
:: ---------------------

:MAIN_MENU
cls
echo.
echo   ==================================================================
echo    SYSTEM DEPENDENCY MANAGER
echo   ==================================================================
echo.
echo    [ STATUS ]
echo    * System:   Online
echo    * Target:   %PACKAGES%
echo.
echo   ------------------------------------------------------------------
echo.
echo    [1]  INSTALL Environment
echo    [2]  UNINSTALL Environment
echo    [3]  EXIT
echo.
echo   ------------------------------------------------------------------
echo.
choice /c 123 /n /m "   Select Option [1-3] > "

if %errorlevel%==1 goto INSTALL_FLOW
if %errorlevel%==2 goto UNINSTALL_FLOW
if %errorlevel%==3 exit /b 0

:INSTALL_FLOW
:: --- Step 0: Initialize ---
call :DRAW_BAR 0 "Initializing diagnostics..."
timeout /t 1 >nul

:: --- Step 1: Cleaning ---
call :DRAW_BAR 10 "Scanning for junk files..."
for /f "delims=" %%I in ('python -c "import site; print(site.getsitepackages()[-1])"') do set "SITEPKG=%%I"
if exist "%SITEPKG%\~*" (
    for /d %%d in ("%SITEPKG%\~*") do rd /s /q "%%d" >nul 2>nul
)

:: --- Step 2: Update Pip ---
call :DRAW_BAR 30 "Updating Package Manager (Pip)..."
python -m pip install --upgrade pip >nul 2>nul

:: --- Step 3: Installing ---
call :DRAW_BAR 60 "Downloading and Installing Packages..."
:: The actual heavy lifting
python -m pip install %PACKAGES% >nul 2>nul

if %errorlevel% neq 0 goto ERROR_HANDLER

:: --- Step 4: Finish ---
call :DRAW_BAR 100 "Installation Complete!"
timeout /t 2 >nul
goto MAIN_MENU

:UNINSTALL_FLOW
cls
color 0C
echo.
echo   ==================================================================
echo    WARNING: UNINSTALL MODE
echo   ==================================================================
echo.
echo    You are about to remove:
echo    %PACKAGES%
echo.
choice /c YN /n /m "   Are you sure? [Y/N] > "

if %errorlevel%==2 (
    color 0B
    goto MAIN_MENU
)

cls
echo.
echo    [*] Uninstalling...
python -m pip uninstall -y %PACKAGES% >nul 2>nul
echo.
echo    [+] Done. Returning to menu...
timeout /t 2 >nul
color 0B
goto MAIN_MENU

:ERROR_HANDLER
color 0C
cls
echo.
echo    ERROR: INSTALLATION FAILED
echo    --------------------------
echo    Please check your internet connection.
pause
color 0B
goto MAIN_MENU

:: --- THE VISUAL ENGINE ---
:DRAW_BAR
:: %1 = Percentage (0, 10, 30, 60, 100)
:: %2 = Status Text
cls
echo.
echo   ==================================================================
echo    INSTALLING PACKAGES
echo   ==================================================================
echo.
echo    Target: %PACKAGES%
echo.
echo    Status: %~2
echo.

:: Render the specific bar state
if "%1"=="0"   echo    [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0%%
if "%1"=="10"  echo    [███░░░░░░░░░░░░░░░░░░░░░░░░░░░]  10%%
if "%1"=="30"  echo    [█████████░░░░░░░░░░░░░░░░░░░░░]  30%%
if "%1"=="60"  echo    [██████████████████░░░░░░░░░░░░]  60%%
if "%1"=="100" echo    [██████████████████████████████] 100%%
echo.
exit /b
