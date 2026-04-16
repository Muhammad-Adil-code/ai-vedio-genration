"""
video_build.py — FFmpeg pipeline: image + adaptive zoom/pan + audio → MP4 clips → final video.

Key design: zoom speed is calculated per-clip so the motion always looks smooth
regardless of whether the clip is 4 seconds or 40 seconds.

Uses portable FFmpeg from ./ffmpeg/bin/ffmpeg.exe (installed by install.py).
"""
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffmpeg.exe")
FFPROBE = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffprobe.exe")


def _get_duration(media_path: str) -> float:
    """Return media file duration in seconds via ffprobe. Falls back to 5.0."""
    result = subprocess.run(
        [FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', media_path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 5.0


def image_to_clip(image_path: str, audio_path: str, output_path: str, duration: float = None) -> str:
    """
    Convert a scene image + audio WAV into an MP4 clip with Ken Burns zoom effect.

    The zoom speed adapts to the clip duration so motion always looks smooth:
      - Short clip (5s)  → faster zoom (more noticeable effect)
      - Long clip (30s)  → slower zoom (subtle cinematic feel)
    Both always zoom from 1.0x to 1.3x over the full clip length.

    Args:
        image_path: path to the PNG scene image
        audio_path: path to the WAV voiceover
        output_path: where to save the clip MP4
        duration: clip duration in seconds (auto-detected from audio if None)

    Returns:
        output_path (str)
    """
    if duration is None:
        duration = _get_duration(audio_path)

    video_duration = duration + 0.3  # tiny buffer so audio does not get cut
    fps = 24
    total_frames = int(video_duration * fps)

    # Adaptive zoom: always travels from 1.0 to 1.3 over the full clip
    # zoom_step = total_zoom_increase / total_frames = 0.3 / total_frames
    zoom_step = round(0.3 / max(total_frames, 1), 8)

    zoom_filter = (
        f"scale=3840:-1,"
        f"zoompan="
        f"z='min(zoom+{zoom_step},1.3)':"
        f"d={total_frames}:"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"s=512x512:fps={fps}"
    )

    silent_path = output_path.replace(".mp4", "_silent.mp4")

    # Step 1: image → silent video with adaptive zoom
    subprocess.run([
        FFMPEG, '-y',
        '-loop', '1',
        '-i', image_path,
        '-vf', zoom_filter,
        '-t', str(video_duration),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        silent_path
    ], check=True, capture_output=True)

    # Step 2: silent video + audio WAV → final clip with AAC audio
    subprocess.run([
        FFMPEG, '-y',
        '-i', silent_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        output_path
    ], check=True, capture_output=True)

    os.remove(silent_path)
    print(f"  [video] Clip saved -> {output_path} ({video_duration:.1f}s)")
    return output_path


def add_fade(clip_path: str, output_path: str, fade_duration: float = 0.4) -> str:
    """
    Add fade-in at start and fade-out at end of a clip.
    Deletes clip_path and saves result to output_path.

    Args:
        clip_path: source MP4 path (will be deleted after)
        output_path: destination MP4 path
        fade_duration: length of each fade in seconds (default 0.4)

    Returns:
        output_path (str)
    """
    clip_duration = _get_duration(clip_path)
    fade_out_start = max(0.0, clip_duration - fade_duration)

    subprocess.run([
        FFMPEG, '-y',
        '-i', clip_path,
        '-vf', (
            f'fade=t=in:st=0:d={fade_duration},'
            f'fade=t=out:st={fade_out_start}:d={fade_duration}'
        ),
        '-af', (
            f'afade=t=in:st=0:d={fade_duration},'
            f'afade=t=out:st={fade_out_start}:d={fade_duration}'
        ),
        '-c:v', 'libx264',
        '-c:a', 'aac',
        output_path
    ], check=True, capture_output=True)

    os.remove(clip_path)
    return output_path


def concatenate_clips(clip_paths: list, output_path: str) -> str:
    """
    Concatenate an ordered list of MP4 clips into a single final video.

    Args:
        clip_paths: list of MP4 file paths in playback order
        output_path: path to write the final MP4

    Returns:
        output_path (str)
    """
    concat_file = os.path.join(os.path.dirname(output_path), "_concat_list.txt")

    with open(concat_file, "w") as f:
        for clip in clip_paths:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    subprocess.run([
        FFMPEG, '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c', 'copy',
        output_path
    ], check=True, capture_output=True)

    os.remove(concat_file)
    print(f"  [video] Final video -> {output_path}")
    return output_path
