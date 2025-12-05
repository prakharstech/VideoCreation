import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- PATH FIX FOR FFMPEG (Addressing pydub warning) ---
# For pydub on macOS with Homebrew, set the path to FFmpeg explicitly
# This ensures pydub can find the necessary executables for audio duration calculation.
# You must still run 'brew install ffmpeg' and 'pip install pydub' to resolve warnings.
if sys.platform == "darwin" and Path("/opt/homebrew/bin/ffmpeg").exists():
    os.environ["FFMPEG_PATH"] = "/opt/homebrew/bin/ffmpeg"
    os.environ["FFPROBE_PATH"] = "/opt/homebrew/bin/ffprobe"

# --- THIRD-PARTY IMPORTS ---

# Required for accurate audio duration calculation
try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None
    print("⚠️ WARNING: pydub not installed. Cannot calculate accurate audio duration.")

# ElevenLabs SDK Imports
from elevenlabs.client import ElevenLabs
try:
    # Attempt to import from the modern, correct location
    from elevenlabs.exceptions import APIError, RateLimitError
except ImportError:
    # Fallback for older/unstable library versions
    APIError = Exception
    RateLimitError = Exception
    print("⚠️ WARNING: ElevenLabs API error classes not found. Using generic Exception.")

# Optional: Add gTTS as a simple fallback
try:
    from gtts import gTTS
except ImportError:
    gTTS = None


# --- CONFIGURATION & INITIALIZATION ---

# Load environment variables from .env file
load_dotenv()

# --- Best Practice Constants ---
AUDIO_DIR = Path("assets/audio_clips")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 1. TEXT TO CONVERT: REPLACE THIS STRING with the text you want the AI to speak.
# ==============================================================================
TEXT_TO_SYNTHESIZE = (
    "Navigating the dynamics between teams and managers is often a love-hate journey."
    "This message confirms all issues have been resolved."
)

# 2. API KEY: Read from environment for security.
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# 3. MODEL ID: Use the latest, high-quality, multilingual model for best results
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"

# 4. VOICE ID: Use a professional voice ID (Rachel)
ELEVENLABS_VOICE_ID = os.getenv(
    "ELEVENLABS_VOICE_ID", "R2e83kjR96zNPDiAnQl3")  # Default to 'Rachel'

# Initialize ElevenLabs Client
client = None
if ELEVENLABS_API_KEY:
    try:
        # Initialize the client with the API key
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        print("✅ ElevenLabs Client Initialized.")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize ElevenLabs Client: {e}")
        client = None
else:
    print("❌ FATAL: ELEVENLABS_API_KEY is missing. TTS will rely on gTTS fallback.")
# ----------------------------------------


def _calculate_duration(audio_path: str) -> float:
    """Calculates the actual duration of the MP3 file in seconds using pydub."""
    # Check both if AudioSegment was imported AND if FFmpeg paths were set/found
    if AudioSegment and (os.environ.get("FFMPEG_PATH") or sys.platform != "darwin"):
        try:
            audio = AudioSegment.from_file(audio_path)
            # pydub returns duration in milliseconds, convert to seconds
            return len(audio) / 1000.0
        except Exception as e:
            print(f"❌ Error calculating duration with pydub: {e}")
            return 5.0  # Fallback placeholder
    # Fallback if pydub or the required FFmpeg is not functional
    return 5.0  # Fallback placeholder


# 🔑 FIX APPLIED HERE: This function now correctly accepts and processes the generator.
def _save_audio_clip(audio_generator, index: int, source: str) -> tuple[str, float]:
    """Saves raw audio data (from a generator) to a file and returns the path and duration."""
    filename = f"scene_{index}_{source}.mp3"
    audio_path = AUDIO_DIR / filename

    # Iterate through the generator and write chunks to the file
    with open(audio_path, "wb") as f:
        for chunk in audio_generator:
            if chunk:
                f.write(chunk)

    # Calculate the actual duration
    duration = _calculate_duration(str(audio_path))

    return str(audio_path), duration


def _create_placeholder_audio(index: int) -> tuple[str, float]:
    """Creates a dummy file path and returns a placeholder duration."""
    filename = f"scene_{index}_silent_placeholder.mp3"
    audio_path = AUDIO_DIR / filename
    # Create an empty file (will be silent)
    audio_path.touch()
    duration = 5.0
    return str(audio_path), duration


def text_to_speech(text: str, index: int, voice_id: str = ELEVENLABS_VOICE_ID, model_id: str = ELEVENLABS_MODEL_ID) -> tuple[str, float]:
    """
    Generates an audio clip from text using ElevenLabs with best model/voice.
    Returns (audio_clip_path, duration_seconds).
    """
    print(f"\n--- Processing Scene {index} ---")

    if client:
        print(
            f"Generating audio using ElevenLabs (Model: {model_id}, Voice: {voice_id})...")
        try:
            # ✅ FIX: Using correct keyword arguments 'voice_id' and 'model_id'
            audio_generator = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
            )

            # Pass the generator (audio_generator) directly to the saving function
            audio_path, duration = _save_audio_clip(
                audio_generator, index+1, "elevenlabs")
            print(
                f"✅ ElevenLabs Audio saved to {audio_path} (Duration: {duration:.2f}s)")
            return audio_path, duration

        # Catch specific API errors for better logging
        except RateLimitError as e:
            print(
                f"❌ ElevenLabs Rate Limit/Quota Exceeded Error: {e}. Falling back...")
        except APIError as e:
            print(
                f"❌ ElevenLabs API Error (Invalid Key/Voice/Model) for scene {index}: {e}. Falling back...")
        except Exception as e:
            print(f"❌ ElevenLabs Unexpected Error: {e}. Falling back...")

    # --- Fallback to gTTS if ElevenLabs failed or client was not initialized ---
    if gTTS:
        print(f"Falling back to gTTS for scene {index}...")
        try:
            tts = gTTS(text=text, lang='en')
            filename = f"scene_{index}_gtts_fallback.mp3"
            audio_path = AUDIO_DIR / filename
            tts.save(str(audio_path))

            # Calculate duration for gTTS file
            duration = _calculate_duration(str(audio_path))

            print(
                f"✅ Fallback audio saved to {audio_path} (Duration: {duration:.2f}s)")
            return str(audio_path), duration
        except Exception as e:
            print(f"❌ gTTS Fallback Failed for scene {index}: {e}")
            # Final fallback: create an empty placeholder file
            return _create_placeholder_audio(index)

    # --- Final Placeholder if everything fails ---
    print(
        f"❌ All TTS methods failed. Creating silent placeholder for scene {index}.")
    return _create_placeholder_audio(index)


if __name__ == '__main__':

    # Check if the client initialized before trying to use the function
    if client or gTTS:
        # Pass the dedicated constant for the text input
        path, duration = text_to_speech(TEXT_TO_SYNTHESIZE, 1)
        print(
            f"\nCompleted processing. Final audio path: {path}, Duration: {duration:.2f}s")
    else:
        print("\nScript terminated because no TTS client (ElevenLabs or gTTS) could be initialized.")
