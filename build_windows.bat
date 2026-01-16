@echo off
REM ===========================================
REM LAC Translate - Windows Build Script
REM ===========================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==========================================
echo   LAC Translate - Windows Build
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo [X] Virtual environment not found. Create it first with:
    echo     python -m venv .venv
    echo     .venv\Scripts\activate
    echo     pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check PyInstaller
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
echo [*] Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Run PyInstaller
echo.
echo [*] Building application with PyInstaller...
echo    This may take several minutes...
echo.

pyinstaller lac_translate.spec --clean --noconfirm

REM Check if build succeeded
if exist "dist\lac-translate" (
    echo.
    echo ==========================================
    echo [OK] BUILD SUCCESSFUL!
    echo ==========================================
    echo.
    echo Output location: dist\lac-translate\
    echo.
    echo To run the application:
    echo    dist\lac-translate\lac-translate.exe
    echo.
    
    REM Create run script
    echo @echo off > dist\lac-translate\run.bat
    echo cd /d "%%~dp0" >> dist\lac-translate\run.bat
    echo start "" lac-translate.exe %%* >> dist\lac-translate\run.bat
    
    echo [i] You can create a desktop shortcut to lac-translate.exe
) else (
    echo.
    echo [X] BUILD FAILED!
    echo Check the output above for errors.
    pause
    exit /b 1
)

echo.
pause
