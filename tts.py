"""
Centralized TTS helper for the project.

Exports:
- text_to_speech(text: str, index: int, voice_id: str | None = None, model_id: str | None = None) -> tuple[str, float]
- client: ElevenLabs client object or None
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Always define `client` so other modules can import it safely
client = None

# If you're on macOS and installed ffmpeg via Homebrew, help pydub find it
if sys.platform == "darwin" and Path("/opt/homebrew/bin/ffmpeg").exists():
    os.environ["FFMPEG_PATH"] = "/opt/homebrew/bin/ffmpeg"
    os.environ["FFPROBE_PATH"] = "/opt/homebrew/bin/ffprobe"

# Optional imports
try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

try:
    from elevenlabs.client import ElevenLabs
    try:
        from elevenlabs.exceptions import APIError, RateLimitError
    except Exception:
        APIError = Exception
        RateLimitError = Exception
except Exception:
    ElevenLabs = None
    APIError = Exception
    RateLimitError = Exception

try:
    from gtts import gTTS
except Exception:
    gTTS = None

# Configuration
AUDIO_DIR = Path("assets/audio_clips")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "R2e83kjR96zNPDiAnQl3")
ELEVENLABS_VERBOSE = os.getenv("ELEVENLABS_VERBOSE", "false").lower() in ("true", "1", "yes")

# Try to initialize ElevenLabs client after defining client variable
if ElevenLabs and ELEVENLABS_API_KEY:
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        if ELEVENLABS_VERBOSE:
            print("✅ ElevenLabs client initialized.")
    except Exception as e:
        print(f"❌ ElevenLabs client initialization failed: {e}")
        client = None
elif ElevenLabs and not ELEVENLABS_API_KEY:
    print("❌ ELEVENLABS_API_KEY not set. ElevenLabs disabled; will fall back to gTTS if available.")
else:
    print("⚠️ ElevenLabs SDK not available — fallback TTS will be used if possible.")

# Helpers
def _calculate_duration(path: str) -> float:
    """Return duration in seconds (best-effort using pydub; fallback to 5s)."""
    if AudioSegment:
        try:
            audio = AudioSegment.from_file(path)
            return len(audio) / 1000.0
        except Exception:
            pass
    return 5.0

def _save_audio(audio_obj, index: int, source: str) -> tuple[str, float]:
    """
    Save audio object to disk. Accepts:
      - bytes/bytearray
      - file-like (has .read())
      - iterator/generator yielding bytes chunks
    Returns (path, duration_seconds).
    """
    filename = f"scene_{index}_{source}.mp3"
    out_path = AUDIO_DIR / filename

    try:
        with open(out_path, "wb") as fh:
            # raw bytes
            if isinstance(audio_obj, (bytes, bytearray)):
                fh.write(audio_obj)
            # file-like
            elif hasattr(audio_obj, "read"):
                fh.write(audio_obj.read())
            else:
                # iterable of chunks
                for chunk in audio_obj:
                    if not chunk:
                        continue
                    if hasattr(chunk, "read"):
                        fh.write(chunk.read())
                    else:
                        # Convert chunk to bytes if needed
                        if isinstance(chunk, str):
                            chunk = chunk.encode()
                        fh.write(chunk)
    except Exception as e:
        print(f"❌ Error saving audio to {out_path}: {e}")
        out_path.touch(exist_ok=True)

    duration = _calculate_duration(str(out_path))
    return str(out_path), duration


def _create_placeholder(index: int) -> tuple[str, float]:
    path = AUDIO_DIR / f"scene_{index}_placeholder.mp3"
    path.touch(exist_ok=True)
    return str(path), 5.0

# Public API
def text_to_speech(text: str, index: int, voice_id: str | None = None, model_id: str | None = None) -> tuple[str, float]:
    """
    Generate an audio clip from `text`. Returns (audio_path, duration_seconds).
    Priority:
      1. ElevenLabs (if client is initialized)
      2. gTTS fallback (if installed)
      3. Silent placeholder
    """
    print(f"\n--- Processing Scene {index} ---")

    voice = voice_id or ELEVENLABS_VOICE_ID
    model = model_id or ELEVENLABS_MODEL_ID

    # ----------------------------
    # TRY ELEVENLABS FIRST
    # ----------------------------
    if client:
        try:
            if ELEVENLABS_VERBOSE:
                print(f"Generating via ElevenLabs (model={model}, voice={voice})...")

            audio_stream = client.text_to_speech.convert(
                text=text,
                voice_id=voice,
                model_id=model
            )

            path, dur = _save_audio(audio_stream, index, "elevenlabs")

            # ❗ CRITICAL FIX: Detect EMPTY or INVALID MP3 files
            # Usually if request failed (401, 429, etc.)
            # the output file will be < 1KB
            if os.path.getsize(path) < 1000:
                raise ValueError("ElevenLabs returned invalid audio (empty file).")

            return path, dur

        except Exception as e:
            print(f"❌ ElevenLabs TTS failed: {e} — falling back to gTTS")

    # ----------------------------
    # FALL BACK TO gTTS
    # ----------------------------
    if gTTS:
        try:
            print("🔄 Using gTTS fallback...")
            tts = gTTS(text=text, lang="en")
            out_file = AUDIO_DIR / f"scene_{index}_gtts.mp3"
            tts.save(str(out_file))
            duration = _calculate_duration(str(out_file))
            return str(out_file), duration
        except Exception as e:
            print(f"❌ gTTS fallback failed: {e}")

    # ----------------------------
    # FINAL FALLBACK — SILENT PLACEHOLDER
    # ----------------------------
    print("❌ All TTS methods failed — creating silent placeholder.")
    return _create_placeholder(index)


__all__ = ["text_to_speech", "client"]
