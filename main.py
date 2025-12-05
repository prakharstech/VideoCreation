# main.py
import argparse
from agent import execute_pipeline


def parse_args():
    p = argparse.ArgumentParser(
        description="Run full pipeline to generate a short video with TTS audio.")
    p.add_argument("--title", required=True,
                   help="Title or seed text for the storyboard/script.")
    p.add_argument("--out", required=True,
                   help="Output video filename (e.g. out.mp4).")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    execute_pipeline(args.title, args.out)
