"""
main.py — One-prompt video pipeline orchestrator.

Usage:
    python main.py "Your prompt here"
    python main.py "Your prompt here" --duration 5
    python main.py "Your prompt here" --duration 0.5

Arguments:
    prompt        Your video description (required)
    --duration N  Video length in minutes (default: 2)

Examples:
    python main.py "Create a UK SaaS marketing reel about AI automation" --duration 5
    python main.py "Create an educational tutorial about machine learning" --duration 3
    python main.py "Create a viral TikTok about productivity hacks" --duration 1

Output:
    final/output_<timestamp>.mp4
"""
import argparse
import os
import subprocess
import sys
import time

import requests

from script_gen import generate_script
from image_gen import generate_image
from tts_gen import text_to_speech
from video_build import image_to_clip, add_fade, concatenate_clips

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCENES_DIR = os.path.join(BASE_DIR, "scenes")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
CLIPS_DIR = os.path.join(BASE_DIR, "clips")
FINAL_DIR = os.path.join(BASE_DIR, "final")
COMFY_DIR = os.path.join(BASE_DIR, "ComfyUI")


def _ensure_dirs():
    for d in [SCENES_DIR, AUDIO_DIR, CLIPS_DIR, FINAL_DIR]:
        os.makedirs(d, exist_ok=True)


def _comfyui_is_running() -> bool:
    try:
        resp = requests.get("http://127.0.0.1:8188/system_stats", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def _start_comfyui():
    """Start ComfyUI as a detached background process (Windows). Returns None."""
    print("[main] Starting ComfyUI (CPU mode) ...")
    log_path = os.path.join(BASE_DIR, "comfyui.log")
    err_path = os.path.join(BASE_DIR, "comfyui_err.log")

    subprocess.Popen([
        "powershell", "-command",
        f"Start-Process python -ArgumentList 'main.py','--cpu' "
        f"-WorkingDirectory '{COMFY_DIR}' "
        f"-RedirectStandardOutput '{log_path}' "
        f"-RedirectStandardError '{err_path}' "
        f"-WindowStyle Hidden"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait up to 90 seconds for ComfyUI to respond
    for i in range(30):
        time.sleep(3)
        if _comfyui_is_running():
            print("[main] ComfyUI is ready.")
            return None
        print(f"[main] Waiting for ComfyUI ... ({(i+1)*3}s)", end='\r')

    raise RuntimeError(
        "ComfyUI did not start within 90 seconds.\n"
        "Check comfyui_err.log for details.\n"
        "Or start manually: cd ComfyUI && python main.py --cpu"
    )


def run_pipeline(prompt: str, duration_minutes: float) -> str:
    """
    Full pipeline: prompt + duration -> final MP4 path.

    Args:
        prompt: user's video description
        duration_minutes: target video length in minutes

    Returns:
        Path to the final output video file.
    """
    _ensure_dirs()
    target_sec = duration_minutes * 60

    print(f"\n{'='*60}")
    print(f"  AI Video Pipeline")
    print(f"  Prompt  : {prompt}")
    print(f"  Duration: {duration_minutes} min ({int(target_sec)}s)")
    print(f"{'='*60}\n")

    # Step 1: Generate script based on duration
    print("[main] Generating scene script ...")
    scenes = generate_script(prompt, target_duration_sec=target_sec)
    actual_duration = sum(s['duration_sec'] for s in scenes)
    print(f"[main] {len(scenes)} scenes | {actual_duration:.0f}s total | "
          f"{scenes[0]['duration_sec']:.1f}s per scene\n")

    # Step 2: Start ComfyUI if not already running
    comfy_proc = None
    if not _comfyui_is_running():
        comfy_proc = _start_comfyui()
    else:
        print("[main] ComfyUI already running.")

    clip_paths = []

    # Step 3: Process each scene
    for i, scene in enumerate(scenes):
        print(f"\n[main] ── Scene {i+1}/{len(scenes)} ({scene['duration_sec']:.1f}s) ──")
        print(f"  Voice: {scene['voiceover'][:80]}{'...' if len(scene['voiceover']) > 80 else ''}")

        image_path = os.path.join(SCENES_DIR, f"scene_{i:03d}.png")
        audio_path = os.path.join(AUDIO_DIR, f"scene_{i:03d}.wav")
        clip_raw = os.path.join(CLIPS_DIR, f"clip_{i:03d}_raw.mp4")
        clip_faded = os.path.join(CLIPS_DIR, f"clip_{i:03d}.mp4")

        generate_image(scene["visual_prompt"], image_path, scene_index=i)
        text_to_speech(scene["voiceover"], audio_path)
        image_to_clip(image_path, audio_path, clip_raw, duration=scene["duration_sec"])
        add_fade(clip_raw, clip_faded)
        clip_paths.append(clip_faded)

    # Step 4: Concatenate all clips into final video
    print(f"\n[main] Assembling {len(clip_paths)} clips into final video ...")
    timestamp = int(time.time())
    output_path = os.path.join(FINAL_DIR, f"output_{timestamp}.mp4")
    concatenate_clips(clip_paths, output_path)

    # Step 5: Stop ComfyUI if we started it
    if comfy_proc:
        comfy_proc.terminate()
        print("[main] ComfyUI stopped.")

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"\n{'='*60}")
    print(f"  Done!")
    print(f"  Video : {output_path}")
    print(f"  Size  : {size_mb:.1f} MB")
    print(f"  Length: ~{duration_minutes} min")
    print(f"{'='*60}\n")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="AI Video Pipeline — one prompt, full video with voice",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Create a UK SaaS marketing reel about AI automation" --duration 5
  python main.py "Create an educational tutorial about machine learning" --duration 3
  python main.py "Create a viral TikTok about productivity hacks" --duration 1
        """
    )
    parser.add_argument(
        "prompt",
        nargs="+",
        help="Your video description"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=2.0,
        metavar="MINUTES",
        help="Target video length in minutes (default: 2)"
    )

    args = parser.parse_args()
    prompt = " ".join(args.prompt)

    if args.duration <= 0:
        print("Error: --duration must be greater than 0")
        sys.exit(1)

    run_pipeline(prompt, duration_minutes=args.duration)


if __name__ == "__main__":
    main()
