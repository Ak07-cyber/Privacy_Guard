@echo off
REM ===============================================================================
REM                    PassiveGuard EXE Build Script (Windows)
REM ===============================================================================
REM This script builds a single executable file that contains:
REM - FastAPI backend server
REM - XGBoost ML model  
REM - Demo HTML frontend
REM - All Python dependencies
REM
REM Usage:
REM   build.bat           - Build for Windows
REM   build.bat --clean   - Clean build (remove previous builds)
REM ===============================================================================

setlocal enabledelayedexpansion

echo.
echo ========================================================================
echo                   PassiveGuard - Build Executable
echo ========================================================================
echo.

REM Directories
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%\.."
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "STANDALONE_DIR=%SCRIPT_DIR%"
set "BUILD_DIR=%STANDALONE_DIR%\build"
set "DIST_DIR=%STANDALONE_DIR%\dist"

REM Parse arguments
set CLEAN=0
if "%1"=="--clean" set CLEAN=1

REM Clean if requested
if %CLEAN%==1 (
    echo [CLEAN] Removing previous builds...
    if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
    if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
    echo [CLEAN] Done!
)

REM Check Python
echo [CHECK] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo    Python: %%i

REM Create virtual environment
set "VENV_DIR=%STANDALONE_DIR%\venv"
if not exist "%VENV_DIR%" (
    echo [SETUP] Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activate virtual environment
echo [SETUP] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Install dependencies
echo [SETUP] Installing build dependencies...
pip install --upgrade pip --quiet
pip install -r "%STANDALONE_DIR%\requirements.txt" --quiet

REM Check ML model
if not exist "%BACKEND_DIR%\models\bot_detector.joblib" (
    echo [MODEL] Training ML model...
    cd "%BACKEND_DIR%"
    pip install -r requirements.txt --quiet
    python -m ml_training.train_model
    cd "%STANDALONE_DIR%"
)

if not exist "%BACKEND_DIR%\models\bot_detector.joblib" (
    echo [ERROR] ML model not found!
    exit /b 1
)
echo    Model: Found

REM Verify demo HTML
if not exist "%PROJECT_ROOT%\demo\index.html" (
    echo [ERROR] Demo HTML not found!
    exit /b 1
)
echo    Demo HTML: Found

REM Build with PyInstaller
echo.
echo [BUILD] Building executable with PyInstaller...
echo         This may take several minutes...
echo.

cd "%STANDALONE_DIR%"
pyinstaller passiveguard.spec --noconfirm --clean

REM Check result
if exist "%DIST_DIR%\PassiveGuard.exe" (
    echo.
    echo ========================================================================
    echo                       BUILD SUCCESSFUL!
    echo ========================================================================
    echo.
    echo    Output: %DIST_DIR%\PassiveGuard.exe
    echo.
    echo To run PassiveGuard:
    echo    %DIST_DIR%\PassiveGuard.exe
    echo    or double-click PassiveGuard.exe in File Explorer
    echo.
) else (
    echo [ERROR] Build failed - executable not found!
    exit /b 1
)

REM Deactivate
call deactivate

echo Done!
