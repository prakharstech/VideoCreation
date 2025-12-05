from gtts import gTTS
import os

test_text = "This is a simple test. If you can hear this, gTTS is working."
output_file = "test_audio.mp3"

print(f"Attempting to generate audio for: '{test_text}'")

try:
    tts = gTTS(text=test_text, lang='en')
    tts.save(output_file)
    print(f"\n✅ SUCCESS: Audio saved to {output_file}")

    # Check if the file exists and is not zero size
    if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
        print("File size is valid. Playback should work.")
    else:
        print("❌ FAILURE: File was created but may be too small or empty.")

except Exception as e:
    print(f"\n❌ FAILURE: An error occurred during gTTS generation:")
    print(f"   Error Type: {type(e).__name__}")
    print(f"   Error Message: {e}")
