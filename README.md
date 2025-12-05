# agentic-video-creator (upgraded)

Agentic AI pipeline that converts a single title into a short video (images + narration + assembly).
This upgraded version includes provider selection for image generation (OpenAI / Stability / Replicate)
and TTS (gTTS / ElevenLabs / Azure).

## Quickstart
1. Create & activate a virtualenv:
```bash
python -m venv venv
source venv/bin/activate  # mac/linux
venv\Scripts\activate   # windows
pip install -r requirements.txt
```
2. Copy and edit `.env.example` → `.env` with your API keys.
3. Run:
```bash
python main.py --title "The power of morning routines" --out demo_video.mp4
```
Outputs go to the `assets/` directory.
