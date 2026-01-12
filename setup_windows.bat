@echo off
REM VoiceToClipboard Windows Setup Script
REM Installs whisper.cpp and downloads the Whisper model

REM Ensure window stays open - add pause at start for testing
REM Remove this line if you want it to run silently
REM pause

setlocal enabledelayedexpansion

REM Keep window open on errors
set "EXIT_CODE=0"

echo ==============================================
echo    VoiceToClipboard Windows Setup
echo ==============================================
echo.
echo If this window closes immediately, there's an error.
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    set "EXIT_CODE=1"
    goto :end
)
for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo    Found Python %PYTHON_VERSION%

REM Check Git
echo [2/6] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not found!
    echo Please install Git from https://git-scm.com/download/win
    set "EXIT_CODE=1"
    goto :end
)
echo    Git is installed

REM Check CMake
echo [3/6] Checking CMake...
cmake --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: CMake not found!
    echo Please install CMake from https://cmake.org/download/
    echo Or via winget: winget install Kitware.CMake
    set "EXIT_CODE=1"
    goto :end
)
echo    CMake is installed

REM Check for Visual Studio Build Tools
echo [4/6] Checking Visual Studio Build Tools...
where cl >nul 2>&1
if errorlevel 1 (
    echo    Visual Studio Build Tools not in PATH, searching...
    
    REM Try to find and set up Visual Studio Build Tools automatically
    set "VS_FOUND=0"
    
    REM Check common Visual Studio 2022 paths
    if !VS_FOUND!==0 (
        if exist "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" (
            echo    Found Visual Studio 2022 Build Tools, setting up environment...
            call "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
            set "VS_FOUND=1"
        )
    )
    
    REM Check for Community/Professional/Enterprise editions
    if !VS_FOUND!==0 (
        if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" (
            echo    Found Visual Studio 2022 Community, setting up environment...
            call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
            set "VS_FOUND=1"
        )
    )
    
    if !VS_FOUND!==0 (
        if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat" (
            echo    Found Visual Studio 2022 Professional, setting up environment...
            call "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat"
            set "VS_FOUND=1"
        )
    )
    
    if !VS_FOUND!==0 (
        if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat" (
            echo    Found Visual Studio 2022 Enterprise, setting up environment...
            call "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat"
            set "VS_FOUND=1"
        )
    )
    
    REM Check Visual Studio 2019
    if !VS_FOUND!==0 (
        if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" (
            echo    Found Visual Studio 2019 Build Tools, setting up environment...
            call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
            set "VS_FOUND=1"
        )
    )
    
    if !VS_FOUND!==0 (
        echo.
        echo ERROR: Visual Studio Build Tools not found!
        echo.
        echo You need Visual Studio Build Tools with C++ workload.
        echo Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
        echo.
        echo Make sure to select "Desktop development with C++" during installation.
        echo.
        set "EXIT_CODE=1"
        goto :end
    )
    
    REM Verify cl.exe is now available
    where cl >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Failed to set up Visual Studio Build Tools environment.
        set "EXIT_CODE=1"
        goto :end
    )
    echo    Visual Studio Build Tools environment configured
) else (
    echo    Visual Studio Build Tools found in PATH
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
REM Use Visual Studio generator (MSBuild) instead of nmake
REM Let CMake auto-detect the Windows SDK version
cmake .. -G "Visual Studio 16 2019" -A x64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_SYSTEM_VERSION=10.0
if errorlevel 1 (
    echo.
    echo ERROR: CMake configuration failed!
    echo.
    echo This usually means:
    echo   - Visual Studio Build Tools are not installed
    echo   - Or C++ workload is missing from Visual Studio
    echo   - Or Windows SDK is missing
    echo.
    echo Please install Visual Studio Build Tools from:
    echo   https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    echo Make sure to select "Desktop development with C++" during installation.
    echo   This includes the Windows SDK automatically.
    echo.
    set "EXIT_CODE=1"
    goto :end
)

echo    Building whisper.cpp (this may take a few minutes)...
REM Build using MSBuild with Release configuration
cmake --build . --config Release -- /m
if errorlevel 1 (
    echo ERROR: Build failed!
    set "EXIT_CODE=1"
    goto :end
)

cd "%SCRIPT_DIR%"

REM Download Whisper model
REM ============================================
REM MODEL SELECTION - Uncomment the model you want:
REM ============================================
REM Base (Fast, ~142MB) - DEFAULT - Good balance of speed and quality
set "MODEL_NAME=base"
set "MODEL_FILE=whisper.cpp\models\ggml-base.bin"
set "MODEL_SIZE=~142MB"

REM Tiny (Fastest, ~75MB) - Fastest but lower quality
REM set "MODEL_NAME=tiny"
REM set "MODEL_FILE=whisper.cpp\models\ggml-tiny.bin"
REM set "MODEL_SIZE=~75MB"

REM Medium (Balanced, ~1.5GB) - Better quality, slower
REM set "MODEL_NAME=medium"
REM set "MODEL_FILE=whisper.cpp\models\ggml-medium.bin"
REM set "MODEL_SIZE=~1.5GB"

REM Large V3 (Best Quality, ~3GB) - Best quality but slowest
REM set "MODEL_NAME=large-v3"
REM set "MODEL_FILE=whisper.cpp\models\ggml-large-v3.bin"
REM set "MODEL_SIZE=~3GB"
REM ============================================

if not exist "%MODEL_FILE%" (
    echo.
    echo Downloading Whisper %MODEL_NAME% model (%MODEL_SIZE%)...
    echo This may take a while depending on your connection.
    cd whisper.cpp\models
    powershell -Command "& {Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-%MODEL_NAME%.bin' -OutFile 'ggml-%MODEL_NAME%.bin'}"
    cd "%SCRIPT_DIR%"
) else (
    echo    Whisper model already downloaded
)

:end
if %EXIT_CODE%==0 (
    echo.
    echo ==============================================
    echo    Setup Complete!
    echo ==============================================
    echo.
    echo To start VoiceToClipboard:
    echo    Start.bat
    echo    Or: .venv\Scripts\python VoiceToClipboard.py
    echo.
    echo Hotkey: Hold Left Control + Left Alt, speak, release
    echo Then press Ctrl+V to paste!
    echo.
) else (
    echo.
    echo ==============================================
    echo    Setup Failed!
    echo ==============================================
    echo.
    echo Please check the error messages above.
    echo.
)

echo.
pause
exit /b %EXIT_CODE%
