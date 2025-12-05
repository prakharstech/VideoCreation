# image_gen.py
"""
Generate images using the Gemini REST API, specifically targeting the
gemini-2.5-flash-image-preview model via the generateContent endpoint.

NOTE: This implementation reads GOOGLE_API_KEY from the environment.
"""

import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Tuple
import time

load_dotenv()

# --- Configuration for Gemini Image API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # REQUIRED
IMAGE_GEN_MODEL = "gemini-2.5-flash-image"
_GEMINI_IMAGES_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta"
# Default size options: "512x512", "1024x1024", "2048x2048"
DEFAULT_SIZE = os.getenv("GEMINI_IMAGE_SIZE", "1024x1024")
# ------------------------------------------


IMAGE_DIR = Path("assets/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def generate_image(prompt: str, index: int, size: str | None = None, output_format: str = "png") -> Tuple[str, dict]:
    """
    Generate an image for `prompt` using the Gemini Image Generation model.
    Returns (image_path, raw_response_json).
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY not set in environment. Cannot generate images.")

    size = size or DEFAULT_SIZE
    url = f"{_GEMINI_IMAGES_ENDPOINT}/models/{IMAGE_GEN_MODEL}:generateContent?key={GOOGLE_API_KEY}"

    # Use the generateContent structure for image generation
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        # NOTE: For this specific model/endpoint combination,
        # size and numberOfImages must NOT be in a separate imageGenerationConfig block.
        # They may be unsupported or passed differently.
        # We are removing the block that caused the error.
        "generationConfig": {
            "responseModalities": ["IMAGE"],
        },
    }

    headers = {
        "Content-Type": "application/json"
    }

    # Exponential backoff for retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                url, json=payload, headers=headers, timeout=120)

            if resp.status_code != 200:
                # Retry on server errors
                if resp.status_code >= 500 and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                # -------------------
                # The 'size' parameter is not supported in the generateContent
                # endpoint for image models, even in generationConfig.
                # A 400 error may still occur if the user attempts to set it.
                # -------------------
                raise RuntimeError(
                    f"Gemini image generation failed: {resp.status_code} {resp.text}")

            data = resp.json()

            # --- Extract image data ---
            b64_image = None
            try:
                # Standard path for generateContent image response
                b64_image = data['candidates'][0]['content']['parts'][0]['inlineData']['data']
            except (KeyError, IndexError):
                # Fallback path for other known structures
                prediction = data.get('predictions', [{}])
                if prediction and prediction[0].get('bytesBase64Encoded'):
                    b64_image = prediction[0]['bytesBase64Encoded']
                else:
                    raise RuntimeError(
                        "Could not find base64 image in Gemini response. Raw response keys: " + str(data.keys()))

            if not b64_image:
                raise RuntimeError(
                    "Could not find base64 image in Gemini response.")

            # decode base64 and write file
            image_bytes = base64.b64decode(b64_image)

            ext = output_format or "png"
            filename = IMAGE_DIR / f"scene_{index}_gemini.{ext}"
            with open(filename, "wb") as fh:
                fh.write(image_bytes)

            return str(filename), data

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(
                    f"Network error (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(
                f"Gemini image generation failed after {max_retries} attempts: {e}")

    # Should be unreachable
    raise RuntimeError("Image generation process failed unexpectedly.")
