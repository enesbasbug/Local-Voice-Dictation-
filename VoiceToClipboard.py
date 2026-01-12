#!/usr/bin/env python3
"""
VoiceToClipboard - Press a hotkey, speak, release to transcribe to clipboard.

Uses whisper.cpp (GGML) for fast on-device speech recognition.
Works entirely offline with no cloud APIs.

Cross-platform: Works on macOS and Windows.
"""

import subprocess
import threading
import tempfile
import time
import os
import sys
import platform
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from pynput import keyboard
import pyperclip

# ============================================================================
# PLATFORM DETECTION
# ============================================================================

IS_MACOS = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

# Platform-specific imports
if IS_MACOS:
    import rumps
    from AppKit import (
        NSWindow, NSTextField, NSColor, NSFont,
        NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
        NSScreen, NSFloatingWindowLevel, NSView, NSMakeRect
    )
    from PyObjCTools import AppHelper
elif IS_WINDOWS:
    import pystray
    from PIL import Image, ImageDraw
    import tkinter as tk
    from tkinter import messagebox


# ============================================================================
# CONFIGURATION
# ============================================================================

# Hotkey: Hold Left Control + Left Alt together to record
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
# CROSS-PLATFORM UTILITIES
# ============================================================================

def find_whisper_cli(base_dir: Path) -> Path:
    """Find whisper-cli executable (cross-platform)."""
    if IS_WINDOWS:
        # Windows: look for .exe
        locations = [
            base_dir / "whisper.cpp" / "build" / "bin" / "Release" / "whisper-cli.exe",
            base_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli.exe",
            base_dir / "whisper.cpp" / "build" / "Release" / "whisper-cli.exe",
        ]
        for loc in locations:
            if loc.exists():
                return loc
        
        # Try PATH
        result = subprocess.run(["where", "whisper-cli.exe"], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return Path(result.stdout.strip().split('\n')[0])
        
        raise FileNotFoundError("whisper-cli.exe not found! Run setup_windows.bat first.")
    else:
        # macOS/Linux
        locations = [
            base_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli",
        ]
        for loc in locations:
            if loc.exists():
                return loc
        
        result = subprocess.run(["which", "whisper-cli"], capture_output=True, text=True)
        if result.returncode == 0:
            return Path(result.stdout.strip())
        
        raise FileNotFoundError("whisper-cli not found! Run setup.sh first.")


def find_models_dir(base_dir: Path, whisper_cli: Path) -> Path:
    """Find Whisper models directory."""
    locations = [
        base_dir / "whisper.cpp" / "models",
        whisper_cli.parent.parent.parent / "models",
    ]
    for loc in locations:
        if loc.exists():
            return loc
    return base_dir / "models"


def copy_to_clipboard(text: str):
    """Copy text to clipboard (cross-platform)."""
    pyperclip.copy(text)


def show_notification(title: str, message: str, subtitle: str = ""):
    """Show a system notification (cross-platform)."""
    if IS_MACOS:
        rumps.notification(title, subtitle, message)
    elif IS_WINDOWS:
        # Windows notification via toast (if available) or print
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=3, threaded=True)
        except ImportError:
            print(f"📢 {title}: {message}")


# ============================================================================
# FLOATING INDICATOR - MACOS
# ============================================================================

if IS_MACOS:
    class RecordingIndicator:
        """A floating pill-shaped indicator that shows recording status (macOS)."""
        
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
# FLOATING INDICATOR - WINDOWS
# ============================================================================

if IS_WINDOWS:
    class RecordingIndicator:
        """A floating indicator that shows recording status (Windows)."""
        
        def __init__(self):
            self.root = None
            self.label = None
            self._state = "recording"
            self._visible = False
            self._setup_complete = threading.Event()
            
            # Start tkinter in a separate thread
            self._tk_thread = threading.Thread(target=self._setup_window, daemon=True)
            self._tk_thread.start()
            self._setup_complete.wait(timeout=5)
        
        def _setup_window(self):
            """Create the floating indicator window."""
            self.root = tk.Tk()
            self.root.withdraw()  # Hide initially
            
            # Window properties
            self.root.overrideredirect(True)  # No title bar
            self.root.attributes('-topmost', True)  # Always on top
            self.root.attributes('-alpha', 0.9)  # Slight transparency
            
            # Create frame with rounded appearance
            width = 180
            height = 44
            
            # Center on screen
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = screen_height - height - 100
            
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create label
            self.label = tk.Label(
                self.root,
                text="Listening...",
                font=("Segoe UI", 12),
                fg="white",
                bg="#2a2a2e",
                padx=20,
                pady=10
            )
            self.label.pack(fill=tk.BOTH, expand=True)
            
            self._setup_complete.set()
            self.root.mainloop()
        
        def show(self, text="Listening..."):
            """Show the indicator with given text."""
            if self.root:
                try:
                    self.root.after(0, lambda: self._do_show(text))
                except:
                    pass
        
        def _do_show(self, text):
            self.label.config(text=text, bg="#2a2a2e")
            self.root.deiconify()
            self._visible = True
        
        def hide(self):
            """Hide the indicator."""
            if self.root:
                try:
                    self.root.after(0, self._do_hide)
                except:
                    pass
        
        def _do_hide(self):
            self.root.withdraw()
            self._visible = False
        
        def update(self, text, state="recording"):
            """Update the indicator text and state."""
            if self.root:
                try:
                    self.root.after(0, lambda: self._do_update(text, state))
                except:
                    pass
        
        def _do_update(self, text, state):
            colors = {
                "recording": "#2a2a2e",
                "processing": "#1a2a40",
                "success": "#1a3a20",
                "error": "#3a1a1a"
            }
            bg = colors.get(state, "#2a2a2e")
            self.label.config(text=text, bg=bg)


# ============================================================================
# MENU BAR APP - MACOS
# ============================================================================

if IS_MACOS:
    class VoiceToClipboardApp(rumps.App):
        """Menu bar application for VoiceToClipboard (macOS)."""
        
        def __init__(self):
            super().__init__("🎙️", quit_button=None)
            
            # Find whisper.cpp
            self.base_dir = Path(__file__).parent.resolve()
            self.whisper_cpp = find_whisper_cli(self.base_dir)
            self.models_dir = find_models_dir(self.base_dir, self.whisper_cpp)
            
            # Current model selection (defaults to Base for faster performance)
            self.current_model = "Base (Fast)"
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
            print(f"Hotkey: Hold Left Control + Left Alt")
            print("=" * 50)
            print("\n✨ Ready! Hold Left Control + Left Alt and speak.\n")
        
        def _build_menu(self):
            """Build the menu bar menu."""
            self.status_item = rumps.MenuItem("Status: Ready")
            self.status_item.set_callback(None)
            
            self.model_menu = rumps.MenuItem("Whisper Model")
            for model_name, model_info in WHISPER_MODELS.items():
                item = rumps.MenuItem(f"{model_name}", callback=self._select_model)
                model_path = self.models_dir / model_info["file"]
                if not model_path.exists():
                    item.title = f"{model_name} (not downloaded)"
                if model_name == self.current_model:
                    item.state = 1
                self.model_menu.add(item)
            
            self.menu = [
                self.status_item,
                None,
                self.model_menu,
                None,
                rumps.MenuItem("How to Use", callback=self._show_help),
                rumps.MenuItem("About", callback=self._show_about),
                None,
                rumps.MenuItem("Quit", callback=self._quit_app),
            ]
        
        def _select_model(self, sender):
            """Handle model selection."""
            model_name = sender.title.replace(" (not downloaded)", "")
            
            if model_name not in WHISPER_MODELS:
                return
            
            model_info = WHISPER_MODELS[model_name]
            model_path = self.models_dir / model_info["file"]
            
            if not model_path.exists():
                rumps.notification(
                    "Model Not Found",
                    f"{model_name}",
                    f"Download the model first",
                    sound=True
                )
                return
            
            self.current_model = model_name
            self.current_model_file = model_info["file"]
            
            for item in self.model_menu.values():
                if isinstance(item, rumps.MenuItem):
                    clean_name = item.title.replace(" (not downloaded)", "")
                    item.state = 1 if clean_name == model_name else 0
            
            rumps.notification("Model Changed", model_name, f"Size: {model_info['size']}", sound=False)
            print(f"📦 Switched to: {model_name}")
        
        def _show_help(self, _):
            """Show how to use dialog."""
            rumps.alert(
                title="How to Use VoiceToClipboard",
                message="""1. Hold Left Control + Left Alt together

2. Speak clearly into your microphone

3. Release either key when done

4. Your speech is transcribed and copied to clipboard

5. Press Cmd+V anywhere to paste!""",
                ok="Got it!"
            )
        
        def _show_about(self, _):
            """Show about dialog."""
            rumps.alert(
                title="About VoiceToClipboard",
                message="""VoiceToClipboard v1.1

Speak → Transcribe → Paste Anywhere

Powered by whisper.cpp
All processing happens locally on your device.""",
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
                    if pressed_keys == RECORD_KEYS and not self.is_recording:
                        self._start_recording()
            
            def on_release(key):
                if key in RECORD_KEYS:
                    pressed_keys.discard(key)
                    if self.is_recording:
                        self._stop_recording()
            
            self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.keyboard_listener.start()
        
        def _start_recording(self):
            """Start recording audio."""
            self.is_recording = True
            self.audio_data = []
            self.title = "🔴"
            
            if self.indicator:
                self.indicator.show("Listening...")
            
            try:
                self.audio_stream = sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype=np.float32,
                    callback=self._audio_callback
                )
                self.audio_stream.start()
                print("🎤 Recording...")
            except Exception as e:
                print(f"❌ Microphone Error: {e}")
                self.is_recording = False
                self.title = "🎙️"
                if self.indicator:
                    self.indicator.update("Microphone error", "error")
                    time.sleep(2)
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
            
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None
            
            self.title = "⏳"
            if self.indicator:
                self.indicator.update("Transcribing...", "processing")
            
            print("⏹️  Processing...")
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
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_wav = f.name
                    audio_int16 = (audio * 32767).astype(np.int16)
                    wavfile.write(temp_wav, SAMPLE_RATE, audio_int16)
                
                try:
                    model_path = self.models_dir / self.current_model_file
                    
                    start = time.time()
                    result = subprocess.run(
                        [str(self.whisper_cpp), "-m", str(model_path), "-f", temp_wav, "--no-timestamps", "-nt"],
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
                    
                    copy_to_clipboard(transcript)
                    print(f"✅ Copied ({elapsed:.1f}s): {transcript[:60]}...")
                    
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
# SYSTEM TRAY APP - WINDOWS
# ============================================================================

if IS_WINDOWS:
    class VoiceToClipboardApp:
        """System tray application for VoiceToClipboard (Windows)."""
        
        def __init__(self):
            # Find whisper.cpp
            self.base_dir = Path(__file__).parent.resolve()
            self.whisper_cpp = find_whisper_cli(self.base_dir)
            self.models_dir = find_models_dir(self.base_dir, self.whisper_cpp)
            
            # Current model selection (defaults to Base for faster performance)
            self.current_model = "Base (Fast)"
            self.current_model_file = WHISPER_MODELS[self.current_model]["file"]
            
            # Recording state
            self.is_recording = False
            self.audio_data = []
            self.audio_stream = None
            self.indicator = None
            self.keyboard_listener = None
            self.icon = None
            
            # Start keyboard listener
            self._start_keyboard_listener()
            
            print("=" * 50)
            print("🎙️  VoiceToClipboard")
            print("=" * 50)
            print(f"Model: {self.current_model}")
            print(f"Hotkey: Hold Left Control + Left Alt")
            print("=" * 50)
            print("\n✨ Ready! Hold Left Control + Left Alt and speak.\n")
        
        def _create_icon_image(self, color="green"):
            """Create a simple icon for the system tray."""
            size = 64
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            if color == "red":
                fill = (220, 50, 50, 255)
            elif color == "yellow":
                fill = (220, 180, 50, 255)
            else:
                fill = (50, 180, 50, 255)
            
            # Draw a microphone-like circle
            draw.ellipse([8, 8, 56, 56], fill=fill, outline=(255, 255, 255, 255))
            return image
        
        def _build_menu(self):
            """Build the system tray menu."""
            model_items = []
            for model_name, model_info in WHISPER_MODELS.items():
                model_path = self.models_dir / model_info["file"]
                label = model_name if model_path.exists() else f"{model_name} (not downloaded)"
                model_items.append(
                    pystray.MenuItem(
                        label,
                        lambda _, m=model_name: self._select_model(m),
                        checked=lambda item, m=model_name: self.current_model == m
                    )
                )
            
            return pystray.Menu(
                pystray.MenuItem("Status: Ready", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Whisper Model", pystray.Menu(*model_items)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("How to Use", self._show_help),
                pystray.MenuItem("About", self._show_about),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit_app)
            )
        
        def _select_model(self, model_name):
            """Handle model selection."""
            if model_name not in WHISPER_MODELS:
                return
            
            model_info = WHISPER_MODELS[model_name]
            model_path = self.models_dir / model_info["file"]
            
            if not model_path.exists():
                messagebox.showwarning("Model Not Found", f"{model_name} is not downloaded yet.")
                return
            
            self.current_model = model_name
            self.current_model_file = model_info["file"]
            print(f"📦 Switched to: {model_name}")
        
        def _show_help(self, icon=None, item=None):
            """Show how to use dialog."""
            messagebox.showinfo(
                "How to Use VoiceToClipboard",
                "1. Hold Left Control + Left Alt together\n\n"
                "2. Speak clearly into your microphone\n\n"
                "3. Release either key when done\n\n"
                "4. Your speech is transcribed and copied to clipboard\n\n"
                "5. Press Ctrl+V anywhere to paste!"
            )
        
        def _show_about(self, icon=None, item=None):
            """Show about dialog."""
            messagebox.showinfo(
                "About VoiceToClipboard",
                "VoiceToClipboard v1.1\n\n"
                "Speak → Transcribe → Paste Anywhere\n\n"
                "Powered by whisper.cpp\n"
                "All processing happens locally on your device."
            )
        
        def _quit_app(self, icon=None, item=None):
            """Quit the application."""
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            if self.icon:
                self.icon.stop()
            sys.exit(0)
        
        def _start_keyboard_listener(self):
            """Start the global keyboard listener."""
            pressed_keys = set()
            
            def on_press(key):
                if key in RECORD_KEYS:
                    pressed_keys.add(key)
                    if pressed_keys == RECORD_KEYS and not self.is_recording:
                        self._start_recording()
            
            def on_release(key):
                if key in RECORD_KEYS:
                    pressed_keys.discard(key)
                    if self.is_recording:
                        self._stop_recording()
            
            self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.keyboard_listener.start()
        
        def _start_recording(self):
            """Start recording audio."""
            self.is_recording = True
            self.audio_data = []
            
            if self.icon:
                self.icon.icon = self._create_icon_image("red")
            
            if self.indicator:
                self.indicator.show("Listening...")
            
            try:
                self.audio_stream = sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype=np.float32,
                    callback=self._audio_callback
                )
                self.audio_stream.start()
                print("🎤 Recording...")
            except Exception as e:
                print(f"❌ Microphone Error: {e}")
                self.is_recording = False
                if self.icon:
                    self.icon.icon = self._create_icon_image("green")
                if self.indicator:
                    self.indicator.update("Microphone error", "error")
                    time.sleep(2)
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
            
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None
            
            if self.icon:
                self.icon.icon = self._create_icon_image("yellow")
            
            if self.indicator:
                self.indicator.update("Transcribing...", "processing")
            
            print("⏹️  Processing...")
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
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_wav = f.name
                    audio_int16 = (audio * 32767).astype(np.int16)
                    wavfile.write(temp_wav, SAMPLE_RATE, audio_int16)
                
                try:
                    model_path = self.models_dir / self.current_model_file
                    
                    start = time.time()
                    result = subprocess.run(
                        [str(self.whisper_cpp), "-m", str(model_path), "-f", temp_wav, "--no-timestamps", "-nt"],
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
                    
                    copy_to_clipboard(transcript)
                    print(f"✅ Copied ({elapsed:.1f}s): {transcript[:60]}...")
                    
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
            if self.icon:
                self.icon.icon = self._create_icon_image("green")
            if self.indicator:
                self.indicator.hide()
        
        def run(self):
            """Run the application."""
            # Create and run the system tray icon
            self.icon = pystray.Icon(
                "VoiceToClipboard",
                self._create_icon_image("green"),
                "VoiceToClipboard",
                menu=self._build_menu()
            )
            self.icon.run()


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
        if IS_WINDOWS:
            print("\nRun setup_windows.bat to install whisper.cpp and download models.")
        else:
            print("\nRun ./setup.sh to install whisper.cpp and download models.")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
