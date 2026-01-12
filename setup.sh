#!/bin/bash
#
# VoiceToClipboard Setup Script
# Installs whisper.cpp and downloads the Whisper model
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "🎙️  VoiceToClipboard Setup"
echo "=============================================="
echo ""

# Check Python version
echo "🔍 Checking prerequisites..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    echo "❌ Python 3.9+ required, found: $PYTHON_VERSION"
    echo "   Install from: https://www.python.org/downloads/macos/"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION"

# Check for Xcode Command Line Tools
if ! xcode-select -p &> /dev/null; then
    echo "❌ Xcode Command Line Tools not found"
    echo ""
    echo "Installing now..."
    xcode-select --install
    echo ""
    echo "⏳ Please:"
    echo "   1. Click 'Install' in the popup"
    echo "   2. Wait for installation to complete"
    echo "   3. Run this script again: ./setup.sh"
    exit 1
fi
echo "✅ Xcode Command Line Tools"
echo ""

# Create and use a project virtual environment
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PY="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment (.venv)..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
fi
# Ensure venv bin is first on PATH so tools like cmake (if installed via pip) are found
export PATH="$VENV_DIR/bin:$PATH"

# Ensure CMake is available
if ! command -v cmake >/dev/null 2>&1; then
    echo "❌ CMake not found"
    if command -v brew >/dev/null 2>&1; then
        echo ""
        echo "📦 Installing CMake via Homebrew..."
        brew update && brew install cmake
        echo "✅ CMake installed"
    else
        echo ""
        echo "ℹ️  Homebrew not found. Attempting Python-based CMake..."
        "$VENV_PY" -m pip install --upgrade --quiet cmake || true
        if ! command -v cmake >/dev/null 2>&1; then
            echo "❌ CMake still not available in PATH"
            echo "   Please install Homebrew and CMake manually, then re-run:"
            echo "   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "   brew install cmake"
            exit 1
        fi
        echo "✅ CMake installed via pip"
    fi
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
echo "   (rumps, sounddevice, pynput, numpy, scipy...)"
"$VENV_PIP" install -r requirements.txt --quiet
echo "✅ Python packages installed"

# Clone and build whisper.cpp
if [ ! -d "whisper.cpp" ]; then
    echo ""
    echo "📥 Cloning whisper.cpp from GitHub..."
    git clone https://github.com/ggerganov/whisper.cpp.git
    echo "✅ Cloned whisper.cpp"
else
    echo ""
    echo "✅ whisper.cpp already cloned"
fi

cd whisper.cpp

echo ""
echo "🔨 Building whisper.cpp with Metal support..."
echo "   (This may take 2-5 minutes, lots of output is normal)"
echo ""
mkdir -p build
cd build
cmake .. -DWHISPER_METAL=ON 2>&1 | grep -E "Metal|Build files|Configuring done" || true
echo ""
cmake --build . --config Release -j$(sysctl -n hw.ncpu) 2>&1 | grep -E "\[100%\]|Built target" || cmake --build . --config Release -j$(sysctl -n hw.ncpu)
echo ""
echo "✅ whisper.cpp built successfully"

cd "$SCRIPT_DIR"

# Download Whisper model
MODEL_DIR="whisper.cpp/models"

# ============================================
# MODEL SELECTION - Uncomment the model you want:
# ============================================
# Base (Fast, ~142MB) - DEFAULT - Good balance of speed and quality
MODEL_NAME="base"
MODEL_SIZE="~142MB"

# Tiny (Fastest, ~75MB) - Fastest but lower quality
# MODEL_NAME="tiny"
# MODEL_SIZE="~75MB"

# Medium (Balanced, ~1.5GB) - Better quality, slower
# MODEL_NAME="medium"
# MODEL_SIZE="~1.5GB"

# Large V3 (Best Quality, ~3GB) - Best quality but slowest
# MODEL_NAME="large-v3"
# MODEL_SIZE="~3GB"
# ============================================

MODEL_FILE="$MODEL_DIR/ggml-$MODEL_NAME.bin"

if [ ! -f "$MODEL_FILE" ]; then
    echo ""
    echo "📥 Downloading Whisper $MODEL_NAME model ($MODEL_SIZE)..."
    echo "   This may take a while depending on your connection"
    cd whisper.cpp
    ./models/download-ggml-model.sh $MODEL_NAME
    cd "$SCRIPT_DIR"
else
    echo "✅ Whisper model already downloaded"
fi

# Make the main script executable
chmod +x VoiceToClipboard.py

echo ""
echo "=============================================="
echo "✅ Setup Complete!"
echo "=============================================="
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Start the app:"
echo "   python3 VoiceToClipboard.py"
echo ""
echo "   Or double-click: Start.command"
echo ""
echo "2. Grant permissions when prompted:"
echo "   • Microphone (for recording)"
echo "   • Input Monitoring (for hotkey detection)"
echo "   • Accessibility (for global shortcuts)"
echo ""
echo "   ⚠️  If hotkey doesn't work, add Terminal to:"
echo "   System Settings → Privacy → Input Monitoring"
echo ""
echo "3. Look for the 🎙️ icon in your menu bar"
echo ""
echo "4. Hold Left Control + Left Option → Speak → Release → Cmd+V"
echo ""
echo "=============================================="
echo ""
