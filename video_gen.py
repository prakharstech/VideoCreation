# video_gen.py
"""
Video generator that:
- For each manifest entry (with image_path and duration), create a video segment from the image.
- Concatenate segments into a single video.
- Concatenate audio clips into combined audio.
- Mux combined audio with concatenated video -> final MP4.

Requirements:
- ffmpeg on PATH
"""

import subprocess
from pathlib import Path
import shutil
import tempfile
import os
from typing import List, Dict


def _ffmpeg_exists() -> bool:
    return shutil.which("ffmpeg") is not None


def _create_video_segment_from_image(image_path: str, duration: float, out_path: str, width=1280, height=720):
    """
    Create a silent video from a single image that lasts `duration` seconds.
    Uses ffmpeg -loop 1 -t <duration> -i <image> -c:v libx264 ...
    """
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-t", str(duration),
        "-vf", f"scale={width}:{height},format=yuv420p",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        out_path
    ]
    subprocess.run(cmd, check=True)


def _concat_videos(file_list: List[str], out_path: str):
    """
    Concatenate mp4 segments using ffmpeg concat demuxer.
    file_list: list of paths to mp4 files (in order).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        listfile = Path(tmpdir) / "videos.txt"
        with open(listfile, "w", encoding="utf-8") as fh:
            for p in file_list:
                fh.write(f"file '{os.path.abspath(p)}'\n")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
            "-c", "copy", out_path
        ]
        subprocess.run(cmd, check=True)


def _concat_audio(audio_files: List[str], out_audio: str):
    """
    Concatenate audio files (mp3) into a single mp3 using ffmpeg concat demuxer.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        listfile = Path(tmpdir) / "audios.txt"
        with open(listfile, "w", encoding="utf-8") as fh:
            for p in audio_files:
                fh.write(f"file '{os.path.abspath(p)}'\n")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
            "-c", "copy", out_audio
        ]
        subprocess.run(cmd, check=True)


def generate_video_from_manifest(manifest: List[Dict], output_file: str, width=1280, height=720):
    if not _ffmpeg_exists():
        raise EnvironmentError(
            "ffmpeg not found on PATH. Please install ffmpeg.")

    if not manifest:
        raise ValueError("Empty manifest supplied.")

    # create temp dir for intermediate files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        video_segments = []
        audio_paths = []

        for entry in sorted(manifest, key=lambda x: x["scene"]):
            scene = entry["scene"]
            duration = float(entry.get("duration", 5.0))
            img = entry.get("image_path") or ""
            audio = entry.get("audio_path")
            audio_paths.append(audio)

            seg_path = tmpdir_path / f"seg_{scene:03d}.mp4"
            # If image exists, render it; otherwise make a black frame video
            if img and Path(img).exists():
                _create_video_segment_from_image(
                    img, duration, str(seg_path), width=width, height=height)
            else:
                # create a black-colored video using ffmpeg lavfi color
                seg_path_black = tmpdir_path / f"seg_{scene:03d}_black.mp4"
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", f"color=black:s={width}x{height}:d={duration}",
                    "-c:v", "libx264",
                    "-t", str(duration),
                    "-pix_fmt", "yuv420p",
                    str(seg_path_black)
                ]
                subprocess.run(cmd, check=True)
                seg_path_black.rename(seg_path)

            video_segments.append(str(seg_path))

        # concat video segments
        combined_video = tmpdir_path / "combined_video.mp4"
        _concat_videos(video_segments, str(combined_video))

        # concat audio files
        combined_audio = tmpdir_path / "combined_audio.mp3"
        _concat_audio(audio_paths, str(combined_audio))

        # mux audio + video
        cmd_mux = [
            "ffmpeg", "-y",
            "-i", str(combined_video),
            "-i", str(combined_audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_file
        ]
        subprocess.run(cmd_mux, check=True)

    print(f"✅ Video generated: {output_file}")
