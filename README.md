# 🎙️ VoiceToClipboard

**Speak → Transcribe → Paste Anywhere**

A macOS utility that lets you dictate text using your voice and instantly paste it anywhere. Hold a hotkey, speak, release — your words are copied to clipboard, ready to paste.

Powered by [whisper.cpp](https://github.com/ggerganov/whisper.cpp) and [GGML](https://github.com/ggml-org/ggml) for fast, private, on-device speech recognition.

<p align="center">
  <img src="screenshots/demo.gif" alt="VoiceToClipboard Demo" width="600">
</p>

---

## ⚡ TL;DR - Get Started in 3 Minutes

```bash
# 1. Clone and setup
git clone https://github.com/enesbasbug/Local-Voice-Dictation-.git
cd Local-Voice-Dictation-
./setup.sh

# 2. Grant permissions when prompted (Microphone, Input Monitoring, Accessibility)

# 3. Run it
python3 VoiceToClipboard.py

# 4. Use it: Hold Left Control + Left Option → Speak → Release → Cmd+V to paste!
```

**First time?** Read the full instructions below for prerequisites and troubleshooting.

---

## ✨ Features

- **🎹 Hold-to-Record** — Hold Left Control + Left Option, speak, release to transcribe
- **📋 Instant Clipboard** — Transcription automatically copied, ready for Cmd+V
- **🎙️ Menu Bar Icon** — Shows app status, access settings anytime
- **🔄 Model Selection** — Choose from Tiny (fast) to Large V3 (accurate)
- **💊 Visual Indicator** — Floating pill shows recording/processing status
- **🔒 100% Private** — All processing on-device, no internet required
- **⚡ Fast** — GPU-accelerated with Metal on Apple Silicon

## 🖥️ Requirements

- **macOS** 12.0 or later
- **Apple Silicon** Mac (M1/M2/M3/M4) recommended
- **Python** 3.10+
- **Xcode Command Line Tools** (for building whisper.cpp)
- ~5GB disk space (models + build files)

## 📋 Prerequisites

**Before starting**, make sure you have these installed:

### 1. Check Python Version

```bash
python3 --version
```

Should show `3.10` or higher. If not, install Python from [python.org](https://www.python.org/downloads/macos/).

### 2. Install Xcode Command Line Tools

```bash
xcode-select --install
```

Click "Install" in the popup. This is **required** to build whisper.cpp.

To verify:
```bash
xcode-select -p
# Should output: /Library/Developer/CommandLineTools
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/enesbasbug/Local-Voice-Dictation-.git
cd Local-Voice-Dictation-
```

### 2. Run Setup

```bash
chmod +x setup.sh
./setup.sh
```

⏱️ **This takes 5-10 minutes** and will:
- Install Python dependencies (`rumps`, `sounddevice`, `pynput`, etc.)
- Clone and build `whisper.cpp` with Metal support
- Download the Whisper Large V3 model (~3GB download)

You'll see lots of compilation output — this is normal! ✅

If you see:
```
✅ Setup Complete!
```

You're ready to continue to Step 3.

### 3. Grant Permissions (Important!)

⚠️ **Run the app from Terminal.app** (not Cursor, iTerm, or other terminals).

The app needs **3 permissions** to work:

#### Option A: Use Start.command (Easiest)
Double-click `Start.command` in Finder. macOS will automatically ask for permissions.

#### Option B: Use Terminal.app
```bash
/Applications/Utilities/Terminal.app # Open Terminal
cd ~/path/to/VoiceToClipboard
python3 VoiceToClipboard.py
```

#### Grant These Permissions:

1. **Microphone** (for recording your voice)
   - System Settings → Privacy & Security → **Microphone**
   - Enable **Terminal**

2. **Input Monitoring** (for detecting the hotkey)
   - System Settings → Privacy & Security → **Input Monitoring**
   - Enable **Terminal**

3. **Accessibility** (for global keyboard shortcuts)
   - System Settings → Privacy & Security → **Accessibility**
   - Enable **Terminal**

After granting permissions, **fully quit Terminal** (Cmd+Q) and restart the app.

### 4. Verify Installation

Run a quick test:

```bash
python3 VoiceToClipboard.py
```

You should see:
```
============================================================
🎙️  VoiceToClipboard
============================================================
Model: Large V3 (Best Quality)
Hotkey: Hold Left Control + Left Option
============================================================

✨ Ready! Hold Left Control + Left Option and speak.
```

**Test it:**
1. Look for the 🎙️ icon in your menu bar (top right)
2. Hold **Left Control + Left Option** → you should see a pill at the bottom saying "Listening..."
3. Say something → release the key
4. Open Notes and press **Cmd+V** to paste

✅ If text appears, you're all set!

## 🎹 Usage

### Quick Reference

**TL;DR**: Hold Left Control + Left Option → Speak → Release → Cmd+V to paste!

| Action | What Happens |
|--------|--------------|
| **Hold Left Control + Left Option** | Start recording (pill appears: "Listening...") |
| **Speak** | Your voice is captured |
| **Release either key** | Audio is transcribed ("Transcribing..." → "Copied!") |
| **Cmd+V** | Paste your transcription anywhere! |

💡 **Tip**: Look for the 🎙️ icon in your menu bar. It changes to 🔴 when recording.

### Example Workflow

1. Open any app (Slack, Notes, Terminal, email)
2. Click where you want to type
3. Hold **Left Control + Left Option** → speak → release
4. Press **Cmd+V** to paste your text

### Switching Models for Speed/Quality

Want faster transcription? Switch to a smaller model:

1. Click **🎙️** in the menu bar
2. Select **Whisper Model** → **Base (Fast)**
3. Try dictating again

The app will show which models you have downloaded vs. which need downloading.

## ⚙️ Configuration

### Change the Hotkey

Edit the top of `VoiceToClipboard.py`:

```python
# Hotkey: Hold Left Control + Left Option together to record
RECORD_KEYS = {keyboard.Key.ctrl_l, keyboard.Key.alt_l}  # Both required
```

You can modify the `RECORD_KEYS` set to use different key combinations. Available keys include:
- `keyboard.Key.ctrl_l` / `keyboard.Key.ctrl_r` — Left/Right Control
- `keyboard.Key.alt_l` / `keyboard.Key.alt_r` — Left/Right Option
- `keyboard.Key.cmd` / `keyboard.Key.cmd_r` — Left/Right Command
- `keyboard.Key.shift` / `keyboard.Key.shift_r` — Left/Right Shift

### Change the Model

**Easy way** (no code editing):
1. Click **🎙️** in menu bar
2. Select **Whisper Model**
3. Choose your model

**Code way** (for default model):
Edit `VoiceToClipboard.py` and find the `WHISPER_MODELS` section to change which model is selected by default.

### Available Models

By default, `setup.sh` downloads **Large V3** (best quality). You can download other models for faster speeds:

| Model | Size | Speed | Quality | Best For | Download Command |
|-------|------|-------|---------|----------|------------------|
| `tiny` | 75MB | ⚡⚡⚡⚡ | ⭐ | Quick tests | `./models/download-ggml-model.sh tiny` |
| `base` | 142MB | ⚡⚡⚡ | ⭐⭐ | Fast dictation | `./models/download-ggml-model.sh base` |
| `medium` | 1.5GB | ⚡⚡ | ⭐⭐⭐ | Balanced | `./models/download-ggml-model.sh medium` |
| `large-v3` | 3GB | ⚡ | ⭐⭐⭐⭐ | Best accuracy | ✅ *Already installed* |

### How to Download Additional Models

```bash
# Navigate to whisper.cpp directory
cd whisper.cpp

# Download the model you want (choose one):
./models/download-ggml-model.sh tiny      # Fastest (75MB)
./models/download-ggml-model.sh base      # Fast (142MB)
./models/download-ggml-model.sh medium    # Balanced (1.5GB)

# Go back to project root
cd ..
```

### How to Switch Models

After downloading, switch models in the app:

1. Click the **🎙️** icon in the menu bar
2. Select **Whisper Model**
3. Choose your model

The menu shows which models are available:
- ✅ **Model Name** — Downloaded and ready
- **Model Name (not downloaded)** — Not available yet

💡 **Tip**: Start with **Base** for quick testing (142MB), use **Large V3** for best accuracy (3GB).

💡 **Speed comparison** on M4 Mac:
- Tiny: ~0.5 seconds (but less accurate)
- Base: ~1 second
- Medium: ~2 seconds
- Large V3: ~3 seconds

## 🏗️ How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        VoiceToClipboard                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   [Hold Hotkey] → [Record Audio] → [Whisper.cpp] → [Clipboard]  │
│         ↓              ↓                ↓              ↓         │
│    pynput         sounddevice       GGML/Metal      pbcopy       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **[whisper.cpp](https://github.com/ggerganov/whisper.cpp)** — C++ port of OpenAI's Whisper model
- **[GGML](https://github.com/ggml-org/ggml)** — Tensor library for efficient ML on consumer hardware
- **Metal** — Apple's GPU framework for hardware acceleration
- **pynput** — Cross-platform keyboard listener
- **sounddevice** — Audio recording
- **PyObjC** — Native macOS floating window

### Why GGML?

GGML enables running large AI models on consumer hardware by:
- **Quantization** — Reduces model size while maintaining quality
- **Metal Support** — Leverages Apple Silicon GPU
- **Efficient Memory** — Optimized for unified memory architecture

On a MacBook with Apple Silicon, this means:
- Fast transcription (2-3 seconds for short clips)
- No internet connection needed
- Complete privacy — audio never leaves your device

## 🔧 Troubleshooting

### Setup Issues

**"Command not found: cmake" or build fails**
- Install Xcode Command Line Tools: `xcode-select --install`
- Restart Terminal after installation

**"Python version too old"**
- Check version: `python3 --version`
- Install Python 3.10+: https://www.python.org/downloads/macos/

**setup.sh fails to download model**
- Check internet connection
- Try manually: `cd whisper.cpp && ./models/download-ggml-model.sh large-v3`

### Permission Issues

**"This process is not trusted!" or hotkey doesn't work**

You're missing **Input Monitoring** permission:
1. Go to: System Settings → Privacy & Security → **Input Monitoring**
2. Click the **+** button
3. Navigate to: Applications → Utilities → **Terminal.app**
4. Enable it
5. **Fully quit Terminal** (Cmd+Q) and restart

**Which app do I grant permissions to?**
- If using `Start.command` → grant to **Terminal.app**
- If using Cursor terminal → grant to **Cursor**
- If using iTerm → grant to **iTerm**

**"Microphone access required"**
- System Settings → Privacy & Security → **Microphone** → Enable **Terminal**

**"Accessibility access required"**
- System Settings → Privacy & Security → **Accessibility** → Enable **Terminal**

### Usage Issues

**App doesn't respond to hotkey**
- Press **Left Control + Left Option** together (both on the left side of keyboard)
- Check Input Monitoring permission (see above)
- Try restarting the app
- Verify the 🎙️ icon appears in menu bar

**No 🎙️ icon in menu bar**
- Check for errors in Terminal output
- Ensure `rumps` is installed: `pip3 install rumps`
- Try: `python3 VoiceToClipboard.py` directly

**Transcription is slow**
- Ensure Metal is enabled (check build output for "Metal")
- Switch to a faster model: Click 🎙️ → Whisper Model → Base (Fast)
- On Intel Macs, expect slower performance

**No audio recorded / No speech detected**
- Check microphone: System Settings → Sound → **Input**
- Speak louder and closer to mic
- Hold the key longer (at least 0.5 seconds)
- Check Input Level meter while speaking

**"Model not found" error**
- Download missing model:
  ```bash
  cd whisper.cpp
  ./models/download-ggml-model.sh large-v3
  ```

## ❓ FAQ

**Q: Do I need an internet connection to use this?**
A: Only during setup to download whisper.cpp and models. After that, everything runs offline.

**Q: Does this work on Intel Macs?**
A: Yes, but it will be slower. Apple Silicon (M1/M2/M3/M4) is highly recommended for best performance.

**Q: Can I use this in other languages (Spanish, French, etc.)?**
A: Yes! Whisper supports 99 languages. It auto-detects the language you're speaking.

**Q: How accurate is it?**
A: Very accurate with the Large V3 model, especially for English. Comparable to commercial services like Siri/Google.

**Q: What's the difference between the models?**
- **Tiny**: Fast but makes more mistakes (75MB)
- **Base**: Good for casual use (142MB)
- **Medium**: Best balance of speed and accuracy (1.5GB)
- **Large V3**: Best accuracy, slower but still fast on Apple Silicon (3GB)

**Q: How do I download more models?**
A: Run this from the VoiceToClipboard directory:
```bash
cd whisper.cpp
./models/download-ggml-model.sh tiny    # or base, medium
cd ..
```
Then switch models by clicking 🎙️ → Whisper Model in the menu bar.

**Q: Can I change the hotkey?**
A: Yes! Edit `RECORD_KEYS` at the top of `VoiceToClipboard.py`. You can change the key combination by modifying the set of keys.

**Q: Is my audio data sent anywhere?**
A: No. Everything runs locally on your Mac. No data leaves your device.

**Q: Can I use this for meetings/calls?**
A: Not directly — it only records your microphone. For system audio, check out the [GGML-Meeting-Recorder](https://github.com/enesbasbug/GGML-Meeting-Recorder) project.

## 📁 Project Structure

```
VoiceToClipboard/
├── VoiceToClipboard.py    # Main application
├── Start.command          # Double-click launcher
├── setup.sh               # Installation script
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── whisper.cpp/           # (Created by setup.sh)
    ├── build/bin/whisper-cli
    └── models/ggml-large-v3.bin
```

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

MIT License — feel free to use, modify, and share.

## 🙏 Acknowledgments

- [Georgi Gerganov](https://github.com/ggerganov) for whisper.cpp and GGML
- [OpenAI](https://openai.com) for the Whisper model
- Apple for Metal and unified memory architecture

---

<p align="center">
  Made with ❤️ for the MacBook ML community
</p>

