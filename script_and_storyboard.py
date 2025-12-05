# script_and_storyboard.py
import json
from pathlib import Path
from dotenv import load_dotenv

from image_gen import generate_image
from tts import text_to_speech, client as tts_client
from llm import generate_scenes_from_title

load_dotenv()

AUDIO_DIR = Path("assets/audio_clips")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_DIR = Path("assets/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def generate_script_and_storyboard(title: str, num_scenes: int = 5, out_manifest: str | None = None):
    """
    Main entry point used by the rest of the project.

    1. Uses the LLM (Gemini) to generate a rich storyboard:
       - narration per scene
       - image_prompt per scene
       - shot_type
       - desired duration

    2. For each scene:
       - Generates audio with TTS from narration
       - Generates an image using the image_prompt
       - Stores everything in a manifest list

    3. Optionally writes the manifest to JSON.

    The manifest entries look like:

    {
      "scene": 1,
      "text": "...",             # alias of narration (for backwards compat)
      "narration": "...",        # full script
      "image_prompt": "...",
      "shot_type": "wide",
      "desired_duration": 7.5,   # from LLM (may be None)
      "audio_path": "assets/audio_clips/scene_1_....mp3",
      "duration": 7.32,          # actual TTS duration in seconds
      "image_path": "assets/images/scene_1_....png"
    }
    """

    if not title or not title.strip():
        raise ValueError("title must be provided")

    print(f"🧠 Calling LLM to generate storyboard for: {title!r} ({num_scenes} scenes)...")
    scenes = generate_scenes_from_title(title, num_scenes=num_scenes)

    manifest: list[dict] = []

    for idx, scene in enumerate(scenes, start=1):
        narration = (scene.get("narration") or "").strip()
        image_prompt = (scene.get("image_prompt") or "").strip()
        shot_type = (scene.get("shot_type") or "").strip()
        desired_duration = scene.get("duration", None)

        if not narration:
            # Safety: never send empty text to TTS
            narration = f"This is scene {idx} for the topic: {title}."

        print(f"\n--- Processing Scene {idx} ---")
        provider_label = "ElevenLabs" if tts_client else "gTTS (fallback)"
        print(f"🎬 Generating audio for scene {idx} via: {provider_label}")

        audio_path, actual_duration = text_to_speech(narration, idx)
        print(f"✅ Saved audio for scene {idx} -> {audio_path} (duration: {actual_duration:.2f}s)")

        # If LLM didn't give us an image_prompt, build one from narration
        if not image_prompt:
            image_prompt = (
                f"{narration} — cinematic, high quality, visually expressive, 16:9 composition"
            )

        img_prompt_for_model = (
            f"{image_prompt} — high quality, photorealistic illustration, cinematic lighting, 16:9"
        )

        try:
            print(f"🖼️ Generating image for scene {idx} via Gemini...")
            image_path, _raw = generate_image(img_prompt_for_model, idx)
            print(f"✅ Gemini image saved to {image_path}")
        except Exception as e:
            print(f"❌ Gemini image generation failed for scene {idx}: {e}")
            image_path = ""  # video_gen/video_builder should fallback to a black frame if missing

        manifest.append({
            "scene": idx,
            # Backwards-compat: some parts of your project might still read "text"
            "text": narration,
            "narration": narration,
            "image_prompt": image_prompt,
            "shot_type": shot_type,
            # LLM-suggested duration (may be None) vs actual TTS duration
            "desired_duration": desired_duration,
            "audio_path": audio_path,
            "duration": actual_duration,
            "image_path": image_path,
        })

    if out_manifest:
        try:
            with open(out_manifest, "w", encoding="utf-8") as fh:
                json.dump(manifest, fh, indent=2, ensure_ascii=False)
            print(f"\n📝 Manifest written to {out_manifest}")
        except Exception as e:
            print(f"⚠️ Could not write manifest: {e}")

    return manifest


# Backwards compatibility function
def synthesize_storyboard_lines(lines):
    """
    Given a list of plain text lines, this function still generates
    audio + images and returns a manifest with minimal metadata.
    Useful for testing or legacy usage.
    """
    manifest = []
    for idx, line in enumerate(lines, start=1):
        narration = (line or "").strip() or f"Scene {idx}."
        audio_path, duration = text_to_speech(narration, idx)
        try:
            image_path, _ = generate_image(
                f"{narration} — cinematic, high quality, 16:9", idx
            )
        except Exception:
            image_path = ""

        manifest.append({
            "scene": idx,
            "text": narration,
            "narration": narration,
            "image_prompt": narration,
            "shot_type": "",
            "desired_duration": None,
            "audio_path": audio_path,
            "duration": duration,
            "image_path": image_path,
        })
    return manifest


if __name__ == "__main__":
    sample_title = "Navigating the dynamics between teams and managers is often a love-hate journey"
    m = generate_script_and_storyboard(
        sample_title,
        num_scenes=5,
        out_manifest="manifest.json"
    )
    print(json.dumps(m, indent=2, ensure_ascii=False))
