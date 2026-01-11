@echo off
REM VoiceToClipboard Windows Setup Script
REM Installs whisper.cpp and downloads the Whisper model

setlocal enabledelayedexpansion

echo ==============================================
echo    VoiceToClipboard Windows Setup
echo ==============================================
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo    Found Python %PYTHON_VERSION%

REM Check Git
echo [2/6] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not found!
    echo Please install Git from https://git-scm.com/download/win
    pause
    exit /b 1
)
echo    Git is installed

REM Check CMake
echo [3/6] Checking CMake...
cmake --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: CMake not found!
    echo Please install CMake from https://cmake.org/download/
    echo Or via winget: winget install Kitware.CMake
    pause
    exit /b 1
)
echo    CMake is installed

REM Check for Visual Studio Build Tools
echo [4/6] Checking Visual Studio Build Tools...
where cl >nul 2>&1
if errorlevel 1 (
    echo WARNING: Visual Studio Build Tools not found in PATH.
    echo.
    echo You need Visual Studio Build Tools with C++ workload.
    echo Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    echo If already installed, try running this script from:
    echo "Developer Command Prompt for VS 2022"
    echo.
    echo Press any key to continue anyway ^(may fail^)...
    pause >nul
)

REM Create virtual environment
echo [5/6] Setting up Python environment...
if not exist ".venv" (
    echo    Creating virtual environment...
    python -m venv .venv
)
echo    Installing Python dependencies...
.venv\Scripts\pip install -r requirements.txt --quiet
echo    Python packages installed

REM Clone and build whisper.cpp
echo [6/6] Building whisper.cpp...
if not exist "whisper.cpp" (
    echo    Cloning whisper.cpp...
    git clone https://github.com/ggerganov/whisper.cpp.git
)

cd whisper.cpp

if not exist "build" mkdir build
cd build

echo    Configuring with CMake...
cmake .. -DCMAKE_BUILD_TYPE=Release >nul 2>&1
if errorlevel 1 (
    echo ERROR: CMake configuration failed!
    echo Make sure Visual Studio Build Tools are installed.
    pause
    exit /b 1
)

echo    Building whisper.cpp (this may take a few minutes)...
cmake --build . --config Release
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

cd "%SCRIPT_DIR%"

REM Download Whisper model
set "MODEL_FILE=whisper.cpp\models\ggml-large-v3.bin"
if not exist "%MODEL_FILE%" (
    echo.
    echo Downloading Whisper Large V3 model (~3GB)...
    echo This may take a while depending on your connection.
    cd whisper.cpp\models
    powershell -Command "& {Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin' -OutFile 'ggml-large-v3.bin'}"
    cd "%SCRIPT_DIR%"
) else (
    echo    Whisper model already downloaded
)

echo.
echo ==============================================
echo    Setup Complete!
echo ==============================================
echo.
echo To start VoiceToClipboard:
echo    .venv\Scripts\python VoiceToClipboard.py
echo.
echo Hotkey: Hold Left Control + Left Alt, speak, release
echo Then press Ctrl+V to paste!
echo.
pause
