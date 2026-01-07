#!/usr/bin/env python3
"""
VoiceToClipboard - Press a hotkey, speak, release to transcribe to clipboard.

Uses whisper.cpp (GGML) for fast on-device speech recognition.
Works entirely offline with no cloud APIs.
"""

import subprocess
import threading
import tempfile
import time
import os
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from pynput import keyboard
import rumps

# PyObjC imports for floating window
from AppKit import (
    NSWindow, NSTextField, NSColor, NSFont,
    NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
    NSScreen, NSFloatingWindowLevel, NSView, NSMakeRect
)
from PyObjCTools import AppHelper


# ============================================================================
# CONFIGURATION
# ============================================================================

# Hotkey: Hold Left Control + Left Option together to record
RECORD_KEYS = {keyboard.Key.ctrl_l, keyboard.Key.alt_l}  # Both required

# Whisper model options
WHISPER_MODELS = {
    "Large V3 (Best Quality)": {
        "file": "ggml-large-v3.bin",
        "size": "~3GB",
        "speed": "Slower"
    },
    "Medium (Balanced)": {
        "file": "ggml-medium.bin",
        "size": "~1.5GB",
        "speed": "Medium"
    },
    "Base (Fast)": {
        "file": "ggml-base.bin",
        "size": "~142MB",
        "speed": "Fast"
    },
    "Tiny (Fastest)": {
        "file": "ggml-tiny.bin",
        "size": "~75MB",
        "speed": "Fastest"
    },
}

# Audio settings
SAMPLE_RATE = 16000  # Whisper expects 16kHz


# ============================================================================
# FLOATING INDICATOR WINDOW (Text only, no icons)
# ============================================================================

class RecordingIndicator:
    """A floating pill-shaped indicator that shows recording status."""
    
    def __init__(self):
        self.window = None
        self.label = None
        self.content_view = None
        self._setup_window()
    
    def _setup_window(self):
        """Create the floating indicator window."""
        width = 180
        height = 44
        
        # Position at bottom center of screen
        screen = NSScreen.mainScreen()
        visible_frame = screen.visibleFrame()
        screen_frame = screen.frame()
        
        x = screen_frame.origin.x + (screen_frame.size.width - width) / 2
        y = visible_frame.origin.y + 80
        
        # Create window
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )
        
        # Window properties
        self.window.setLevel_(NSFloatingWindowLevel + 1)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setHasShadow_(True)
        self.window.setIgnoresMouseEvents_(True)
        self.window.setCollectionBehavior_(1 << 0)
        
        # Create rounded background view
        self.content_view = RoundedView.alloc().initWithFrame_(
            NSMakeRect(0, 0, width, height)
        )
        self.window.setContentView_(self.content_view)
        
        # Create centered text label (no icons)
        self.label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(0, 10, width, 24)
        )
        self.label.setStringValue_("Listening...")
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)
        self.label.setAlignment_(1)  # Center
        self.label.setTextColor_(NSColor.whiteColor())
        self.label.setFont_(NSFont.systemFontOfSize_(15))
        self.content_view.addSubview_(self.label)
    
    def show(self, text="Listening..."):
        """Show the indicator with given text."""
        def _show():
            self.label.setStringValue_(text)
            self.content_view.setState_("recording")
            self.content_view.setNeedsDisplay_(True)
            self.window.orderFront_(None)
        AppHelper.callAfter(_show)
    
    def hide(self):
        """Hide the indicator."""
        def _hide():
            self.window.orderOut_(None)
        AppHelper.callAfter(_hide)
    
    def update(self, text, state="recording"):
        """Update the indicator text and state."""
        def _update():
            self.label.setStringValue_(text)
            self.content_view.setState_(state)
            self.content_view.setNeedsDisplay_(True)
        AppHelper.callAfter(_update)


class RoundedView(NSView):
    """A view with rounded corners and gradient background."""
    
    _state = "recording"
    
    def setState_(self, state):
        self._state = state
    
    def drawRect_(self, rect):
        from AppKit import NSBezierPath, NSGradient
        
        colors = {
            "recording": (
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.15, 0.15, 0.18, 0.95),
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.95)
            ),
            "processing": (
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.1, 0.15, 0.25, 0.95),
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.05, 0.08, 0.15, 0.95)
            ),
            "success": (
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.1, 0.22, 0.12, 0.95),
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.05, 0.12, 0.06, 0.95)
            ),
            "error": (
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.25, 0.1, 0.1, 0.95),
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.15, 0.05, 0.05, 0.95)
            )
        }
        
        top_color, bottom_color = colors.get(self._state, colors["recording"])
        
        gradient = NSGradient.alloc().initWithStartingColor_endingColor_(
            top_color, bottom_color
        )
        
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            rect, 22, 22
        )
        gradient.drawInBezierPath_angle_(path, 90)
        
        NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.1).setStroke()
        path.setLineWidth_(1.0)
        path.stroke()


# ============================================================================
# MENU BAR APP
# ============================================================================

class VoiceToClipboardApp(rumps.App):
    """Menu bar application for VoiceToClipboard."""
    
    def __init__(self):
        super().__init__("🎙️", quit_button=None)
        
        # Find whisper.cpp
        self.base_dir = Path(__file__).parent.resolve()
        self.whisper_cpp = self._find_whisper()
        self.models_dir = self._find_models_dir()
        
        # Current model selection
        self.current_model = "Large V3 (Best Quality)"
        self.current_model_file = WHISPER_MODELS[self.current_model]["file"]
        
        # Recording state
        self.is_recording = False
        self.audio_data = []
        self.audio_stream = None
        self.indicator = None
        self.keyboard_listener = None
        
        # Build menu
        self._build_menu()
        
        # Start keyboard listener
        self._start_keyboard_listener()
        
        print("=" * 50)
        print("🎙️  VoiceToClipboard")
        print("=" * 50)
        print(f"Model: {self.current_model}")
        print(f"Hotkey: Hold Left Control + Left Option")
        print("=" * 50)
        print("\n✨ Ready! Hold Left Control + Left Option and speak.\n")
    
    def _find_whisper(self) -> Path:
        """Find whisper-cli executable."""
        locations = [
            self.base_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli",
        ]
        for loc in locations:
            if loc.exists():
                return loc
        
        result = subprocess.run(["which", "whisper-cli"], capture_output=True, text=True)
        if result.returncode == 0:
            return Path(result.stdout.strip())
        
        raise FileNotFoundError("whisper-cli not found! Run setup.sh first.")
    
    def _find_models_dir(self) -> Path:
        """Find Whisper models directory."""
        locations = [
            self.base_dir / "whisper.cpp" / "models",
            self.whisper_cpp.parent.parent.parent / "models",
        ]
        for loc in locations:
            if loc.exists():
                return loc
        return self.base_dir / "models"
    
    def _build_menu(self):
        """Build the menu bar menu."""
        # Status
        self.status_item = rumps.MenuItem("Status: Ready")
        self.status_item.set_callback(None)
        
        # Model selection submenu
        self.model_menu = rumps.MenuItem("Whisper Model")
        for model_name, model_info in WHISPER_MODELS.items():
            item = rumps.MenuItem(
                f"{model_name}",
                callback=self._select_model
            )
            # Check if model file exists
            model_path = self.models_dir / model_info["file"]
            if not model_path.exists():
                item.title = f"{model_name} (not downloaded)"
            if model_name == self.current_model:
                item.state = 1  # Checkmark
            self.model_menu.add(item)
        
        # How to use
        self.menu = [
            self.status_item,
            None,  # Separator
            self.model_menu,
            None,  # Separator
            rumps.MenuItem("How to Use", callback=self._show_help),
            rumps.MenuItem("About", callback=self._show_about),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self._quit_app),
        ]
    
    def _select_model(self, sender):
        """Handle model selection."""
        # Extract model name (remove " (not downloaded)" if present)
        model_name = sender.title.replace(" (not downloaded)", "")
        
        if model_name not in WHISPER_MODELS:
            return
        
        model_info = WHISPER_MODELS[model_name]
        model_path = self.models_dir / model_info["file"]
        
        if not model_path.exists():
            rumps.notification(
                "Model Not Found",
                f"{model_name}",
                f"Download with: cd whisper.cpp && ./models/download-ggml-model.sh {model_info['file'].replace('ggml-', '').replace('.bin', '')}",
                sound=True
            )
            return
        
        # Update selection
        self.current_model = model_name
        self.current_model_file = model_info["file"]
        
        # Update checkmarks
        for item in self.model_menu.values():
            if isinstance(item, rumps.MenuItem):
                clean_name = item.title.replace(" (not downloaded)", "")
                item.state = 1 if clean_name == model_name else 0
        
        rumps.notification(
            "Model Changed",
            model_name,
            f"Size: {model_info['size']} | Speed: {model_info['speed']}",
            sound=False
        )
        print(f"📦 Switched to: {model_name}")
    
    def _show_help(self, _):
        """Show how to use dialog."""
        rumps.alert(
            title="How to Use VoiceToClipboard",
            message="""1. Hold Left Control + Left Option together

2. Speak clearly into your microphone

3. Release either key when done

4. Your speech is transcribed and copied to clipboard

5. Press Cmd+V anywhere to paste!

Tips:
• Speak in complete sentences for best results
• The indicator at the bottom shows status
• Change models in the menu for speed/quality tradeoff""",
            ok="Got it!"
        )
    
    def _show_about(self, _):
        """Show about dialog."""
        rumps.alert(
            title="About VoiceToClipboard",
            message="""VoiceToClipboard v1.0

Speak → Transcribe → Paste Anywhere

Powered by:
• whisper.cpp - Fast speech recognition
• GGML - Efficient ML on Apple Silicon
• Metal - GPU acceleration

All processing happens locally on your Mac.
No cloud. No API keys. No data leaves your device.

GitHub: github.com/ggerganov/whisper.cpp""",
            ok="Close"
        )
    
    def _quit_app(self, _):
        """Quit the application."""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        rumps.quit_application()
    
    def _start_keyboard_listener(self):
        """Start the global keyboard listener."""
        pressed_keys = set()
        
        def on_press(key):
            if key in RECORD_KEYS:
                pressed_keys.add(key)
                # Start recording when both keys are pressed
                if pressed_keys == RECORD_KEYS and not self.is_recording:
                    self._start_recording()
        
        def on_release(key):
            if key in RECORD_KEYS:
                pressed_keys.discard(key)
                # Stop recording when either key is released
                if self.is_recording:
                    self._stop_recording()
        
        self.keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start()
    
    def _start_recording(self):
        """Start recording audio."""
        self.is_recording = True
        self.audio_data = []
        
        # Update menu bar icon
        self.title = "🔴"
        
        # Show indicator
        if self.indicator:
            self.indicator.show("Listening...")
        
        # Start audio stream
        try:
            self.audio_stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype=np.float32,
                callback=self._audio_callback
            )
            self.audio_stream.start()
            print("🎤 Recording...")
        except sd.PortAudioError as e:
            print(f"❌ Microphone Error: {e}")
            print("\n⚠️  Please grant Microphone permission:")
            print("   System Settings → Privacy & Security → Microphone")
            print("   Enable Terminal (or the app you're running from)")
            print("   Then restart the app.\n")
            self.is_recording = False
            self.title = "🎙️"
            if self.indicator:
                self.indicator.update("Microphone permission needed", "error")
                time.sleep(2)
                self.indicator.hide()
        except Exception as e:
            print(f"❌ Error starting recording: {e}")
            self.is_recording = False
            self.title = "🎙️"
            if self.indicator:
                self.indicator.hide()
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Audio stream callback."""
        if self.is_recording:
            self.audio_data.append(indata.copy())
    
    def _stop_recording(self):
        """Stop recording and transcribe."""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # Stop audio stream
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
        
        # Update UI
        self.title = "⏳"
        if self.indicator:
            self.indicator.update("Transcribing...", "processing")
        
        print("⏹️  Processing...")
        
        # Process in background
        threading.Thread(target=self._process_audio, daemon=True).start()
    
    def _process_audio(self):
        """Process recorded audio and copy to clipboard."""
        try:
            if not self.audio_data:
                self._reset_ui()
                return
            
            audio = np.concatenate(self.audio_data)
            duration = len(audio) / SAMPLE_RATE
            
            if duration < 0.3:
                print("⚠️  Too short")
                self._reset_ui()
                return
            
            # Save to temp WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_wav = f.name
                audio_int16 = (audio * 32767).astype(np.int16)
                wavfile.write(temp_wav, SAMPLE_RATE, audio_int16)
            
            try:
                # Get model path
                model_path = self.models_dir / self.current_model_file
                
                # Transcribe
                start = time.time()
                result = subprocess.run(
                    [
                        str(self.whisper_cpp),
                        "-m", str(model_path),
                        "-f", temp_wav,
                        "--no-timestamps",
                        "-nt",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                elapsed = time.time() - start
                
                if result.returncode != 0:
                    print(f"❌ Error: {result.stderr}")
                    if self.indicator:
                        self.indicator.update("Error", "error")
                        time.sleep(1)
                    self._reset_ui()
                    return
                
                transcript = " ".join(result.stdout.strip().split())
                
                if not transcript:
                    print("🔇 No speech detected")
                    if self.indicator:
                        self.indicator.update("No speech", "error")
                        time.sleep(1)
                    self._reset_ui()
                    return
                
                # Copy to clipboard
                process = subprocess.Popen(
                    ['pbcopy'],
                    stdin=subprocess.PIPE,
                    env={'LANG': 'en_US.UTF-8'}
                )
                process.communicate(transcript.encode('utf-8'))
                
                print(f"✅ Copied ({elapsed:.1f}s): {transcript[:60]}...")
                
                # Show success
                if self.indicator:
                    self.indicator.update("Copied!", "success")
                    time.sleep(1)
                
            finally:
                os.unlink(temp_wav)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if self.indicator:
                self.indicator.update("Error", "error")
                time.sleep(1)
        
        self._reset_ui()
    
    def _reset_ui(self):
        """Reset UI to ready state."""
        def _do_reset():
            self.title = "🎙️"
            if self.indicator:
                self.indicator.hide()
        AppHelper.callAfter(_do_reset)


# ============================================================================
# MAIN
# ============================================================================

def main():
    try:
        app = VoiceToClipboardApp()
        
        # Create floating indicator
        app.indicator = RecordingIndicator()
        
        # Run the app
        app.run()
        
    except FileNotFoundError as e:
        print(f"❌ Setup required: {e}")
        print("\nRun ./setup.sh to install whisper.cpp and download models.")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
