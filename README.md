# Agentic Video Creator

An automated AI pipeline that converts a single text topic into a complete short video. This tool acts as an "agent," orchestrating the entire production process: writing the script, creating a storyboard, generating voiceovers (TTS), creating AI images, and assembling everything into a final `.mp4` video.

## 🚀 Features

* **AI Script & Storyboard**: Uses **Google Gemini** to generate a structured script, visual descriptions, and shot types based on your input title.
* **AI Image Generation**: Automatically generates cinematic images for each scene using **Gemini's Image Generation** capabilities.
* **Text-to-Speech (TTS)**: High-quality narration using **ElevenLabs** (with **gTTS** as a robust fallback).
* **Automatic Video Editing**: Assembles images and audio, handles timing, and exports a final video using `ffmpeg`.
* **Modular Design**: Separate modules for LLM, TTS, Image Generation, and Video building for easy customization.

## 🛠️ Prerequisites

* **Python 3.8+**
* **FFmpeg**: Required for video processing and audio format conversion.
    * **Mac**: `brew install ffmpeg`
    * **Windows**: [Download FFmpeg](https://ffmpeg.org/download.html) and add it to your System PATH.
    * **Linux**: `sudo apt install ffmpeg`

## 📦 Installation

1.  **Clone or Download the repository**:
    ```bash
    git clone <repository-url>
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(See [requirements.txt](requirements.txt) for full list)*

## ⚙️ Configuration

1.  Create a `.env` file in the root directory.
2.  Add your API keys to the `.env` file. You will need keys for Google Gemini (for script/images) and optionally ElevenLabs (for high-quality audio).

**Example `.env` content:**
```bash
# Required for Script & Image Generation
GEMINI_API_KEY=your_google_gemini_api_key
# OR
GOOGLE_API_KEY=your_google_gemini_api_key

# Optional: Required for High-Quality TTS (defaults to gTTS if missing)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=R2e83kjR96zNPDiAnQl3  # Optional: Default is 'Rachel'
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

## 🎬 Usage

Run the `main.py` script with your desired video title and output filename.

```bash
python main.py --title "The Future of Artificial Intelligence" --out "ai_video.mp4"
```

### Arguments:
* `--title`: The topic or title of the video. The AI will generate the script based on this.
* `--out`: The filename for the final video (e.g., `video.mp4`).

**The script will:**
* Generate a 5-scene storyboard.
* Create audio narrations (saved in `assets/audio_clips`).
* Generate images (saved in `assets/images`).
* Combine them into the final video file.

## 📂 Project Structure

```bash
prakharstech/videocreation/
├── main.py                     # Entry point (CLI)
├── agent.py                    # Pipeline orchestrator
├── script_and_storyboard.py    # Storyboard & asset generation logic
├── llm.py                      # Gemini text generation wrapper
├── image_gen.py                # Gemini image generation wrapper
├── tts.py                      # Text-to-Speech (ElevenLabs + gTTS)
├── video_gen.py                # FFmpeg video assembly
├── requirements.txt            # Python dependencies
├── .env                        # API keys configuration
│
├── assets/                     # Created at runtime
│   ├── audio_clips/            # Generated narration files
│   ├── images/                 # Generated scene images
│   └── videos/                 # Final output
│
├── templates/
│   └── prompt_templates.md     # Prompts for the LLM
│
└── Documentation
    ├── README.md               # Project documentation
    └── LICENSE                 # MIT License
```

## ⚠️ Troubleshooting

* **FFmpeg not found**: Ensure FFmpeg is installed and added to your system's PATH. On Windows, you might need to restart your terminal after installing.
* **API Errors**: Check your `.env` file to ensure your API keys are correct and have active quotas.
* **Empty Video/Black Screen**: If image generation fails (e.g., strict safety filters), the video generator will use a black screen for that scene but continue audio playback.

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.


