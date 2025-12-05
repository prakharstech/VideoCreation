# llm.py — Gemini 2.5 script + storyboard helper

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Prefer GEMINI_API_KEY, fallback to OPENAI_API_KEY just so env stays compatible
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

client = None
try:
    if not api_key:
        print("❌ ERROR: Missing GEMINI_API_KEY or OPENAI_API_KEY in environment variables.")
    else:
        # Requires: pip install google-genai
        from google import genai
        client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"⚠️ Could not initialize Gemini client, will use fallback generation. Error: {e}")
    client = None


def _call_gemini(prompt: str, model: str = "gemini-2.5-flash") -> str:
    """
    Low-level helper: send a single prompt string to Gemini and get back text.
    """
    if client is None:
        raise RuntimeError("Gemini client is not configured.")

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    # For google-genai, .text contains the concatenated text output
    return (response.text or "").strip()


def generate_scenes_from_title(title: str, num_scenes: int, model: str = "gemini-2.5-flash"):
    """
    HIGH-LEVEL API used by script_and_storyboard.py

    Returns a list of scene dicts in this shape:

    [
      {
        "scene": 1,
        "narration": "80–150 word narration...",
        "image_prompt": "visual description only...",
        "shot_type": "wide / close-up / aerial / medium / POV / etc.",
        "duration": 6.5   # desired duration in seconds (optional)
      },
      ...
    ]
    """

    title = (title or "").strip() or "your topic"

    prompt = f"""
You are a professional video scriptwriter and storyboard artist.

Create a structured storyboard for a video about:
"{title}"

Break it into EXACTLY {num_scenes} scenes.

Return STRICTLY a JSON array (no extra text, no explanations), where each element has:

{{
  "scene": 1,
  "narration": "An 80–150 word voiceover narration, cinematic, engaging, natural, as if spoken by a narrator in a YouTube video. No bullet points, no scene labels, just the narration.",
  "image_prompt": "A concise visual description of what should be shown in this scene. Do NOT include narration here. No leading words like 'Image of' or 'Picture of'. Just describe the visuals.",
  "shot_type": "One of: 'wide', 'medium', 'close-up', 'aerial', 'POV'. Pick what best fits the scene.",
  "duration": 6.5
}}

Rules:
- "narration": 80–150 words, flowing, cinematic, no scene numbers, no quotes around the whole thing.
- "image_prompt": ONLY visuals, no dialogue, no camera directions like 'camera pans'. Just what we see.
- "shot_type": a single short lowercase word like 'wide', 'medium', 'close-up', 'aerial', or 'POV'.
- "duration": a reasonable float number in seconds for how long this scene should be on screen.

VERY IMPORTANT:
- Return ONLY valid JSON.
- DO NOT wrap it in markdown.
- DO NOT add any commentary before or after the JSON.
"""

    try:
        raw = _call_gemini(prompt, model=model)
        data = json.loads(raw)

        scenes = []
        for i, scene in enumerate(data, start=1):
            scenes.append({
                "scene": scene.get("scene", i),
                "narration": (scene.get("narration") or "").strip(),
                "image_prompt": (scene.get("image_prompt") or "").strip(),
                "shot_type": (scene.get("shot_type") or "").strip(),
                "duration": scene.get("duration"),  # may be None or missing
            })

        # Make sure we don't exceed num_scenes
        return scenes[:num_scenes]

    except Exception as e:
        # If anything fails (no client, bad JSON, etc.), fall back to a simple heuristic
        print(f"⚠️ LLM storyboard generation failed, using fallback scenes instead. Error: {e}")

        fallback = []
        for i in range(1, num_scenes + 1):
            if i == 1:
                narration = (
                    f"This is the introduction to {title}. In this opening scene, we set the context, "
                    f"explain why this topic matters, and give the viewer a clear idea of what they will "
                    f"gain from watching the video from start to finish."
                )
                shot_type = "wide"
            elif i == num_scenes:
                narration = (
                    f"In this final scene, we wrap up our exploration of {title}. We briefly recap the key "
                    f"points, highlight the most important takeaway for the viewer, and end with a clear, "
                    f"motivating call to action that encourages them to apply what they've learned."
                )
                shot_type = "wide"
            else:
                narration = (
                    f"In this scene, we dive deeper into one important aspect of {title}. We explain it in a "
                    f"clear and relatable way, using simple language and concrete examples so that any viewer "
                    f"can understand and stay engaged with the story."
                )
                shot_type = "medium"

            fallback.append({
                "scene": i,
                "narration": narration,
                "image_prompt": f"A cinematic {shot_type} shot illustrating scene {i} about {title}.",
                "shot_type": shot_type,
                "duration": None,
            })

        return fallback


# Optional: backwards-compatible wrapper if something in your code still calls this
def chat_completion(messages, model: str = "gemini-2.5-flash"):
    """
    Simple wrapper to keep older agent-style code working.
    It concatenates all message contents into a single prompt.
    """
    prompt = "\n".join(m.get("content", "") for m in messages)
    return _call_gemini(prompt, model=model)
