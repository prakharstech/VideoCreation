# video_builder.py
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from pathlib import Path

# --- Configuration ---
FINAL_VIDEO_DIR = "assets/videos"
os.makedirs(FINAL_VIDEO_DIR, exist_ok=True)
# ---------------------


def build_video(scene_records, output_filename="final_video.mp4"):
    """
    Assembles individual scene video clips (with attached audio) into a final video.

    :param scene_records: A list of dictionaries, each containing 'video_path', 
                          'audio_path', and 'duration_seconds'.
    :param output_filename: The name of the final output file (e.g., 'final.mp4').
    """
    if not scene_records:
        print("❌ ERROR: No scene records found. Cannot build video.")
        return

    # 1. Create a list of VideoFileClip objects
    video_clips = []
    print("   Loading video clips...")
    for record in scene_records:
        video_path = record.get("video_path")
        if video_path and Path(video_path).exists():
            try:
                # Load the clip; its audio should already be attached from video_gen.py
                clip = VideoFileClip(str(video_path))
                video_clips.append(clip)
            except Exception as e:
                print(f"⚠️ Warning: Could not load clip {video_path}: {e}")
        else:
            print(
                f"⚠️ Warning: Video file not found for a scene: {video_path}")

    if not video_clips:
        print("❌ ERROR: No valid video clips were loaded. Aborting video build.")
        return

    # 2. Concatenate the clips
    print(f"   Concatenating {len(video_clips)} clips...")
    try:
        final_clip = concatenate_videoclips(video_clips, method="compose")
    except Exception as e:
        print(f"❌ ERROR: Failed to concatenate video clips: {e}")
        # Clean up loaded clips to free memory
        for clip in video_clips:
            clip.close()
        return

    # 3. Write the final output file
    output_path = Path(FINAL_VIDEO_DIR) / output_filename
    print(f"   Writing final video to {output_path}...")

    # Use 'libx264' codec for good compatibility and 'aac' for audio
    final_clip.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        fps=24,  # Standard frame rate
        verbose=False,
        logger=None
    )

    # 4. Clean up loaded clips
    final_clip.close()
    for clip in video_clips:
        clip.close()

    print(f"✅ Final video assembly complete.")
    return str(output_path)
