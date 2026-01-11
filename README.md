# VoiceToClipboard

**Speak → Transcribe → Paste Anywhere**

A cross-platform utility that lets you dictate text using your voice and instantly paste it anywhere. Hold a hotkey, speak, release — your words are copied to clipboard, ready to paste.

Powered by [whisper.cpp](https://github.com/ggerganov/whisper.cpp) for fast, private, on-device speech recognition.

**Platforms:** macOS | Windows

---

## Quick Start

### macOS

```bash
git clone https://github.com/enesbasbug/Local-Voice-Dictation-.git
cd Local-Voice-Dictation-
./setup.sh

# Run:
.venv/bin/python VoiceToClipboard.py
# Or double-click Start.command

# Use: Hold Left Control + Left Option → Speak → Release → Cmd+V
```

### Windows

```cmd
git clone https://github.com/enesbasbug/Local-Voice-Dictation-.git
cd Local-Voice-Dictation-
setup_windows.bat

# Run:
.venv\Scripts\python VoiceToClipboard.py

# Use: Hold Left Ctrl + Left Alt → Speak → Release → Ctrl+V
```

---

## Features

- **Hold-to-Record** — Hold Left Ctrl + Left Alt, speak, release to transcribe
- **Instant Clipboard** — Transcription automatically copied, ready for paste
- **System Tray / Menu Bar** — Access settings from tray icon
- **Model Selection** — Choose from Tiny (fast) to Large V3 (accurate)
- **Visual Indicator** — Floating pill shows recording/processing status
- **100% Private** — All processing on-device, no internet required
- **GPU Accelerated** — Uses Metal on macOS, CUDA on Windows (if available)

---

## Requirements

### macOS
- macOS 12.0 or later
- Apple Silicon (M1/M2/M3/M4) recommended
- Python 3.10+
- Xcode Command Line Tools

### Windows
- Windows 10/11
- Python 3.10+
- Git
- CMake
- Visual Studio Build Tools (with C++ workload)

---

## Installation

### macOS Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/enesbasbug/Local-Voice-Dictation-.git
   cd Local-Voice-Dictation-
   ```

2. **Run setup:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Grant permissions** (System Settings → Privacy & Security):
   - Microphone → Enable Terminal
   - Input Monitoring → Enable Terminal
   - Accessibility → Enable Terminal

4. **Run the app:**
   ```bash
   .venv/bin/python VoiceToClipboard.py
   ```

### Windows Setup

1. **Prerequisites:**
   - Install [Python 3.10+](https://www.python.org/downloads/) (check "Add to PATH")
   - Install [Git](https://git-scm.com/download/win)
   - Install [CMake](https://cmake.org/download/)
   - Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
     - Select "Desktop development with C++"

2. **Clone and setup:**
   ```cmd
   git clone https://github.com/enesbasbug/Local-Voice-Dictation-.git
   cd Local-Voice-Dictation-
   setup_windows.bat
   ```

3. **Run the app:**
   ```cmd
   .venv\Scripts\python VoiceToClipboard.py
   ```

---

## Usage

| Action | macOS | Windows |
|--------|-------|---------|
| **Start Recording** | Hold Left Control + Left Option | Hold Left Ctrl + Left Alt |
| **Speak** | Talk into microphone | Talk into microphone |
| **Stop & Transcribe** | Release either key | Release either key |
| **Paste** | Cmd+V | Ctrl+V |

Look for the microphone icon in your menu bar (macOS) or system tray (Windows).

---

## Configuration

### Change the Hotkey

Edit `VoiceToClipboard.py`:

```python
RECORD_KEYS = {keyboard.Key.ctrl_l, keyboard.Key.alt_l}  # Both required
```

### Switch Models

Click the tray/menu bar icon → Whisper Model → Choose model

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| Tiny | 75MB | ⚡⚡⚡⚡ | ⭐ |
| Base | 142MB | ⚡⚡⚡ | ⭐⭐ |
| Medium | 1.5GB | ⚡⚡ | ⭐⭐⭐ |
| Large V3 | 3GB | ⚡ | ⭐⭐⭐⭐ |

### Download Additional Models

**macOS:**
```bash
cd whisper.cpp
./models/download-ggml-model.sh base  # or tiny, medium
```

**Windows:**
```cmd
cd whisper.cpp\models
powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin' -OutFile 'ggml-base.bin'"
```

---

## How It Works

```
[Hold Hotkey] → [Record Audio] → [Whisper.cpp] → [Clipboard]
     ↓              ↓                ↓              ↓
  pynput       sounddevice       GGML/GPU      pyperclip
```

All processing happens locally on your device:
- Fast transcription (2-3 seconds)
- No internet needed
- Complete privacy

---

## Technology Stack

| Component | macOS | Windows |
|-----------|-------|---------|
| System Tray/Menu | rumps | pystray |
| Floating Indicator | PyObjC/AppKit | tkinter |
| Keyboard Listener | pynput | pynput |
| Audio Recording | sounddevice | sounddevice |
| Clipboard | pyperclip | pyperclip |
| Speech Recognition | whisper.cpp | whisper.cpp |
| GPU Acceleration | Metal | CUDA (optional) |

---

## Troubleshooting

### macOS

**Hotkey doesn't work**
- Check Input Monitoring permission
- Use **left** Control and **left** Option keys

**No menu bar icon**
- Use `.venv/bin/python VoiceToClipboard.py`

### Windows

**"whisper-cli.exe not found"**
- Run `setup_windows.bat` again
- Make sure Visual Studio Build Tools is installed

**Build errors**
- Run from "Developer Command Prompt for VS 2022"
- Ensure C++ workload is installed

**Hotkey doesn't work**
- Run as Administrator
- Check if another app is using the hotkey

---

## Project Structure

```
VoiceToClipboard/
├── VoiceToClipboard.py   # Main app (cross-platform)
├── setup.sh              # macOS setup script
├── setup_windows.bat     # Windows setup script
├── Start.command         # macOS launcher
├── requirements.txt      # Python dependencies
├── screenshots/demo.gif
└── whisper.cpp/          # (Created by setup)
```

---

## License

MIT License

## Acknowledgments

- [Georgi Gerganov](https://github.com/ggerganov) for whisper.cpp
- [OpenAI](https://openai.com) for the Whisper model
