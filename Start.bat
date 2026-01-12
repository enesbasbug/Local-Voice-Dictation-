@echo off
REM VoiceToClipboard Launcher (Windows)
REM Double-click this file or run: Start.bat

cd /d "%~dp0"

echo 🎙️ Starting VoiceToClipboard...
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Virtual environment not found!
    echo Please run setup_windows.bat first.
    echo.
    pause
    exit /b 1
)

REM Check if main script exists
if not exist "VoiceToClipboard.py" (
    echo ❌ VoiceToClipboard.py not found!
    echo Make sure you're in the correct directory.
    echo.
    pause
    exit /b 1
)

REM Run the application
echo ✨ Launching application...
echo    (The app will run in the background. Look for the microphone icon in your system tray.)
echo.
echo Press Ctrl+C to stop the application.
echo.

.venv\Scripts\python.exe VoiceToClipboard.py

REM If we get here, the app exited (either error or user closed it)
if errorlevel 1 (
    echo.
    echo ❌ Application exited with an error.
    echo.
    echo Common issues:
    echo   - Missing dependencies: Run setup_windows.bat again
    echo   - whisper-cli.exe not found: Make sure setup completed successfully
    echo   - Missing model file: Check whisper.cpp\models\ directory
    echo.
)

pause
