# AI Video Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully local "one prompt → full MP4 video with voice" pipeline — Claude Code orchestrates script generation, ComfyUI generates images, pyttsx3 generates voiceover, and FFmpeg assembles the final video with motion.

**Architecture:** `main.py` takes a single prompt → `script_gen.py` breaks it into 5 scenes (visual prompt + voiceover per scene) → `image_gen.py` sends each scene to ComfyUI (SD 1.5, CPU mode) → `tts_gen.py` generates WAV audio per scene → `video_build.py` uses FFmpeg to add Ken Burns zoom/pan to each image, merge audio, and concatenate into final MP4.

**Tech Stack:** Python 3.13, ComfyUI (SD 1.5 safetensors, CPU), FFmpeg portable (win64), pyttsx3 (Windows SAPI TTS), requests

**Hardware:** Intel UHD 620, 16GB RAM — CPU-only mode, 512x512, 15 steps per image (~3–8 min per scene)

---

## File Map

| File | Responsibility |
|---|---|
| `install.py` | One-time setup: download FFmpeg portable, clone ComfyUI, download SD 1.5 model, install pip packages |
| `workflow.json` | ComfyUI API workflow (SD 1.5 txt2img, 512x512, 15 steps) |
| `requirements.txt` | Python deps: requests, pyttsx3 |
| `script_gen.py` | Prompt → list of 5 scene dicts `{visual_prompt, voiceover, duration_sec}` |
| `image_gen.py` | POST to ComfyUI `/prompt`, poll `/history/{id}`, copy output image to `scenes/` |
| `tts_gen.py` | pyttsx3: text → WAV saved to `audio/` |
| `video_build.py` | FFmpeg: image+zoom → silent MP4, merge audio, add fade transitions, concatenate all clips |
| `main.py` | Orchestrator: starts ComfyUI if needed, calls all modules, outputs `final/output_<timestamp>.mp4` |

**Runtime folders (auto-created):**
```
scenes/    ← generated PNG images
audio/     ← generated WAV files
clips/     ← per-scene MP4 clips
final/     ← final output MP4
ffmpeg/    ← portable FFmpeg binary
ComfyUI/   ← ComfyUI installation
```

---

### Task 1: Project structure and requirements.txt

**Files:**
- Create: `requirements.txt`
- Create: `scenes/`, `audio/`, `clips/`, `final/` directories

- [ ] **Step 1: Create requirements.txt**

```
requests>=2.31.0
pyttsx3>=2.90
```

Save to: `C:\Users\saboo\Desktop\vedio\requirements.txt`

- [ ] **Step 2: Create project folders**

Run in `C:\Users\saboo\Desktop\vedio\`:
```bash
mkdir -p scenes audio clips final
```

- [ ] **Step 3: Install Python packages**

```bash
pip install requests pyttsx3
```

Expected output: `Successfully installed pyttsx3-2.90 requests-2.31.0` (versions may differ)

- [ ] **Step 4: Verify pyttsx3 works**

Run Python one-liner to confirm SAPI is available:
```bash
python -c "import pyttsx3; e = pyttsx3.init(); print('TTS OK — voices:', len(e.getProperty('voices')))"
```

Expected: `TTS OK — voices: 2` (or more)

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/saboo/Desktop/vedio"
git add requirements.txt
git commit -m "feat: add requirements.txt for video pipeline"
```

---

### Task 2: workflow.json — ComfyUI SD 1.5 API workflow

**Files:**
- Create: `workflow.json`

- [ ] **Step 1: Create workflow.json**

Save the following to `C:\Users\saboo\Desktop\vedio\workflow.json`:

```json
{
  "3": {
    "inputs": {
      "seed": 42,
      "steps": 15,
      "cfg": 7.0,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["4", 0],
      "positive": ["6", 0],
      "negative": ["7", 0],
      "latent_image": ["5", 0]
    },
    "class_type": "KSampler"
  },
  "4": {
    "inputs": {
      "ckpt_name": "v1-5-pruned-emaonly.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "5": {
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "6": {
    "inputs": {
      "text": "cinematic office scene, professional, 8k",
      "clip": ["4", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "7": {
    "inputs": {
      "text": "blurry, low quality, distorted, watermark, text, signature, ugly, deformed",
      "clip": ["4", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "8": {
    "inputs": {
      "samples": ["3", 0],
      "vae": ["4", 2]
    },
    "class_type": "VAEDecode"
  },
  "9": {
    "inputs": {
      "filename_prefix": "scene",
      "images": ["8", 0]
    },
    "class_type": "SaveImage"
  }
}
```

- [ ] **Step 2: Verify JSON is valid**

```bash
python -c "import json; json.load(open('workflow.json')); print('workflow.json is valid')"
```

Expected: `workflow.json is valid`

- [ ] **Step 3: Commit**

```bash
git add workflow.json
git commit -m "feat: add ComfyUI SD 1.5 CPU workflow"
```

---

### Task 3: install.py — one-time setup

**Files:**
- Create: `install.py`

- [ ] **Step 1: Create install.py**

Save to `C:\Users\saboo\Desktop\vedio\install.py`:

```python
"""
One-time setup. Run: python install.py
Installs: FFmpeg (portable), ComfyUI, SD 1.5 model, pip packages.
Takes 20-40 minutes on first run (model is 4GB).
"""
import os
import sys
import subprocess
import zipfile
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def download_file(url: str, dest_path: str, desc: str):
    print(f"  Downloading {desc} ...")
    print(f"  This may take several minutes.")

    def progress(count, block_size, total_size):
        if total_size > 0:
            pct = min(int(count * block_size * 100 / total_size), 100)
            print(f"  {pct}%", end='\r')

    urllib.request.urlretrieve(url, dest_path, reporthook=progress)
    print(f"\n  Saved to {dest_path}")


def install_ffmpeg():
    ffmpeg_exe = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        print("[setup] FFmpeg already installed, skipping.")
        return

    print("[setup] Downloading FFmpeg portable (win64)...")
    zip_path = os.path.join(BASE_DIR, "ffmpeg.zip")
    download_file(
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        zip_path,
        "FFmpeg"
    )

    print("[setup] Extracting FFmpeg...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(BASE_DIR)

    for item in os.listdir(BASE_DIR):
        full = os.path.join(BASE_DIR, item)
        if item.startswith("ffmpeg-master") and os.path.isdir(full):
            os.rename(full, os.path.join(BASE_DIR, "ffmpeg"))
            break

    os.remove(zip_path)
    print("[setup] FFmpeg installed.")


def install_comfyui():
    comfy_dir = os.path.join(BASE_DIR, "ComfyUI")
    if os.path.exists(comfy_dir):
        print("[setup] ComfyUI already installed, skipping.")
        return

    print("[setup] Cloning ComfyUI...")
    run(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git", comfy_dir])

    print("[setup] Installing PyTorch (CPU-only) — this is ~800MB, please wait...")
    run([sys.executable, "-m", "pip", "install",
         "torch", "torchvision",
         "--index-url", "https://download.pytorch.org/whl/cpu"])

    print("[setup] Installing ComfyUI requirements...")
    run([sys.executable, "-m", "pip", "install", "-r",
         os.path.join(comfy_dir, "requirements.txt")])

    print("[setup] ComfyUI installed.")


def download_model():
    model_dir = os.path.join(BASE_DIR, "ComfyUI", "models", "checkpoints")
    model_path = os.path.join(model_dir, "v1-5-pruned-emaonly.safetensors")

    if os.path.exists(model_path):
        print("[setup] SD 1.5 model already downloaded, skipping.")
        return

    os.makedirs(model_dir, exist_ok=True)
    print("[setup] Downloading SD 1.5 model (~4GB) — this will take 10-30 minutes...")
    download_file(
        "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors",
        model_path,
        "Stable Diffusion v1.5"
    )
    print("[setup] Model downloaded.")


def create_folders():
    for folder in ["scenes", "audio", "clips", "final"]:
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)
    print("[setup] Project folders created.")


if __name__ == "__main__":
    print("=" * 55)
    print("  AI Video Pipeline — One-Time Setup")
    print("=" * 55)
    create_folders()
    install_ffmpeg()
    install_comfyui()
    download_model()
    print("\n" + "=" * 55)
    print("  Setup complete!")
    print('  Run: python main.py "Your video prompt here"')
    print("=" * 55)
```

- [ ] **Step 2: Verify install.py is valid Python**

```bash
python -c "import ast; ast.parse(open('install.py').read()); print('install.py syntax OK')"
```

Expected: `install.py syntax OK`

- [ ] **Step 3: Commit**

```bash
git add install.py
git commit -m "feat: add one-time setup script"
```

---

### Task 4: script_gen.py — prompt to scenes

**Files:**
- Create: `script_gen.py`

- [ ] **Step 1: Create script_gen.py**

Save to `C:\Users\saboo\Desktop\vedio\script_gen.py`:

```python
"""
script_gen.py — converts a user prompt into a list of scene dicts.
Each scene: {visual_prompt: str, voiceover: str, duration_sec: int}
"""


def generate_script(prompt: str) -> list:
    """
    Detect video type from keywords in prompt, return 5 scene dicts.
    Supported types: marketing, educational, social (default: marketing).
    """
    p = prompt.lower()

    if any(w in p for w in ['marketing', 'reel', 'saas', 'product', 'brand', 'ad', 'advertisement', 'startup']):
        template_key = 'marketing'
    elif any(w in p for w in ['educational', 'tutorial', 'explain', 'how to', 'learn', 'course', 'teach']):
        template_key = 'educational'
    elif any(w in p for w in ['social', 'tiktok', 'shorts', 'viral', 'instagram', 'reel']):
        template_key = 'social'
    else:
        template_key = 'marketing'

    # Strip leading verb phrases to get the subject
    subject = prompt
    for prefix in ['create a', 'make a', 'generate a', 'build a', 'produce a',
                   'create', 'make', 'generate', 'build', 'produce']:
        if p.startswith(prefix):
            subject = prompt[len(prefix):].strip()
            break

    s = subject  # short alias

    templates = {
        'marketing': [
            {
                'visual_prompt': (
                    f'cinematic establishing shot, modern tech startup office, floor-to-ceiling windows, '
                    f'city skyline, professional atmosphere, {s}, photorealistic, 8k, golden hour lighting'
                ),
                'voiceover': 'The way businesses operate is changing forever.',
                'duration_sec': 4
            },
            {
                'visual_prompt': (
                    f'close up frustrated professional surrounded by paperwork and spreadsheets, '
                    f'messy desk, stressed expression, dramatic shadows, {s}, cinematic realism'
                ),
                'voiceover': 'Endless manual tasks and slow processes are holding you back.',
                'duration_sec': 5
            },
            {
                'visual_prompt': (
                    f'sleek AI dashboard interface on large monitor, data visualizations, glowing blue tones, '
                    f'clean modern UI, {s}, futuristic tech aesthetic, ultra detailed'
                ),
                'voiceover': 'Our AI platform automates it all, so your team can focus on what matters.',
                'duration_sec': 5
            },
            {
                'visual_prompt': (
                    f'diverse business team smiling and celebrating around conference table, charts showing growth, '
                    f'modern office, professional lighting, {s}'
                ),
                'voiceover': 'Join thousands of businesses saving twenty hours every week.',
                'duration_sec': 4
            },
            {
                'visual_prompt': (
                    f'clean white background with bold modern typography, professional branding, '
                    f'call to action design, minimal aesthetic, {s}'
                ),
                'voiceover': 'Start your free fourteen day trial today. No credit card required.',
                'duration_sec': 4
            },
        ],
        'educational': [
            {
                'visual_prompt': (
                    f'bright clean modern classroom, books and laptop, inspiring learning atmosphere, '
                    f'{s}, professional photography, 8k'
                ),
                'voiceover': f'Today we are going to break down everything about {subject}.',
                'duration_sec': 4
            },
            {
                'visual_prompt': (
                    f'person looking confused at complex diagram on whiteboard, question marks, '
                    f'thinking expression, soft lighting, {s}, relatable educational scene'
                ),
                'voiceover': 'Most people struggle with this because nobody explains it simply.',
                'duration_sec': 5
            },
            {
                'visual_prompt': (
                    f'clear step-by-step process diagram, numbered arrows, clean visual layout, '
                    f'educational infographic style, {s}, instructional design'
                ),
                'voiceover': 'Here is the three-step framework that changes everything.',
                'duration_sec': 5
            },
            {
                'visual_prompt': (
                    f'person confidently presenting results, achievement celebration, progress charts, '
                    f'success outcome visual, {s}, professional photography'
                ),
                'voiceover': 'Apply this framework and see real results within your first week.',
                'duration_sec': 4
            },
            {
                'visual_prompt': (
                    f'community of learners, online course platform interface, student success stories, '
                    f'motivational atmosphere, {s}'
                ),
                'voiceover': 'Subscribe now for more lessons that actually make a difference.',
                'duration_sec': 4
            },
        ],
        'social': [
            {
                'visual_prompt': (
                    f'eye-catching vibrant visual opener, bold saturated colors, dynamic composition, '
                    f'attention-grabbing, {s}, social media optimized'
                ),
                'voiceover': 'Wait, you need to see this.',
                'duration_sec': 2
            },
            {
                'visual_prompt': (
                    f'dramatic before and after comparison, transformation visual, high contrast, '
                    f'viral social media aesthetic, {s}, engaging composition'
                ),
                'voiceover': f'This one thing about {subject} went completely viral.',
                'duration_sec': 4
            },
            {
                'visual_prompt': (
                    f'fast-paced montage style, energetic multiple-shot composition, trending aesthetic, '
                    f'{s}, gen-z visual style, dynamic'
                ),
                'voiceover': 'And the results are absolutely insane.',
                'duration_sec': 4
            },
            {
                'visual_prompt': (
                    f'proof and results display, bold statistics and numbers, social proof visual, '
                    f'credibility design, {s}, clean modern graphic'
                ),
                'voiceover': 'Over one million people have already tried this.',
                'duration_sec': 3
            },
            {
                'visual_prompt': (
                    f'engaging call to action screen, subscribe button highlight, notification bell, '
                    f'trending hashtags visual, {s}, social media native design'
                ),
                'voiceover': 'Follow for more content that actually works.',
                'duration_sec': 3
            },
        ],
    }

    return templates[template_key]


if __name__ == '__main__':
    import json
    import sys

    prompt = ' '.join(sys.argv[1:]) or 'Create a UK SaaS marketing reel about AI automation'
    scenes = generate_script(prompt)
    print(json.dumps(scenes, indent=2))
    print(f"\nTotal scenes: {len(scenes)}")
    total_duration = sum(s['duration_sec'] for s in scenes)
    print(f"Estimated video length: {total_duration}s")
```

- [ ] **Step 2: Smoke test script_gen.py**

```bash
python script_gen.py "Create a UK SaaS marketing reel about AI automation"
```

Expected: JSON with 5 scenes printed, each with `visual_prompt`, `voiceover`, `duration_sec`. Final line: `Estimated video length: 22s`

- [ ] **Step 3: Test educational detection**

```bash
python script_gen.py "Create an educational tutorial about machine learning"
```

Expected: 5 scenes where scene 1 voiceover starts with `"Today we are going to break down"`

- [ ] **Step 4: Commit**

```bash
git add script_gen.py
git commit -m "feat: add scene script generator"
```

---

### Task 5: image_gen.py — ComfyUI API client

**Files:**
- Create: `image_gen.py`

- [ ] **Step 1: Create image_gen.py**

Save to `C:\Users\saboo\Desktop\vedio\image_gen.py`:

```python
"""
image_gen.py — sends a visual prompt to ComfyUI, waits for result, saves PNG.
ComfyUI must be running at http://127.0.0.1:8188 before calling this module.
"""
import json
import os
import shutil
import time

import requests

COMFY_URL = "http://127.0.0.1:8188"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMFY_OUTPUT_DIR = os.path.join(BASE_DIR, "ComfyUI", "output")
WORKFLOW_PATH = os.path.join(BASE_DIR, "workflow.json")


def _load_workflow(visual_prompt: str, seed: int) -> dict:
    """Load workflow.json, inject prompt and seed. Returns workflow dict."""
    with open(WORKFLOW_PATH) as f:
        workflow = json.load(f)
    workflow["6"]["inputs"]["text"] = visual_prompt
    workflow["3"]["inputs"]["seed"] = seed
    return workflow


def _submit_prompt(workflow: dict) -> str:
    """POST workflow to ComfyUI /prompt. Returns prompt_id string."""
    resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow}, timeout=30)
    resp.raise_for_status()
    return resp.json()["prompt_id"]


def _wait_for_result(prompt_id: str, timeout: int = 900) -> dict:
    """
    Poll GET /history/{prompt_id} until completed.
    Returns the history entry dict. Raises TimeoutError after timeout seconds.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            if resp.status_code == 200:
                history = resp.json()
                if prompt_id in history and history[prompt_id].get("outputs"):
                    return history[prompt_id]
        except requests.RequestException:
            pass
        time.sleep(5)
    raise TimeoutError(f"ComfyUI did not complete prompt {prompt_id} within {timeout}s")


def _extract_filename(history_entry: dict) -> str:
    """Extract output image filename from ComfyUI history entry (node 9 = SaveImage)."""
    return history_entry["outputs"]["9"]["images"][0]["filename"]


def generate_image(visual_prompt: str, output_path: str, scene_index: int = 0) -> str:
    """
    Full image generation pipeline:
      visual_prompt -> ComfyUI (SD 1.5 CPU) -> PNG saved to output_path.

    Args:
        visual_prompt: descriptive text prompt for the scene
        output_path: where to save the output PNG (e.g. 'scenes/scene_000.png')
        scene_index: used to generate a unique seed per scene

    Returns:
        output_path (str) — path to saved image
    """
    seed = (scene_index * 1337 + 42) % 2147483647
    print(f"  [image] Scene {scene_index}: submitting to ComfyUI (seed={seed})...")

    workflow = _load_workflow(visual_prompt, seed)
    prompt_id = _submit_prompt(workflow)
    print(f"  [image] prompt_id={prompt_id} — waiting for generation (this takes 3–8 min on CPU)...")

    history = _wait_for_result(prompt_id)
    filename = _extract_filename(history)
    src = os.path.join(COMFY_OUTPUT_DIR, filename)
    shutil.copy2(src, output_path)
    print(f"  [image] Saved -> {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) or "cinematic startup office, professional lighting, 8k"
    os.makedirs("scenes", exist_ok=True)
    generate_image(prompt, "scenes/test_000.png", scene_index=0)
```

- [ ] **Step 2: Verify syntax**

```bash
python -c "import ast; ast.parse(open('image_gen.py').read()); print('image_gen.py syntax OK')"
```

Expected: `image_gen.py syntax OK`

- [ ] **Step 3: Commit**

```bash
git add image_gen.py
git commit -m "feat: add ComfyUI image generation client"
```

*Note: Full test of image_gen.py happens in Task 9 after ComfyUI is installed and running.*

---

### Task 6: tts_gen.py — text to speech

**Files:**
- Create: `tts_gen.py`

- [ ] **Step 1: Create tts_gen.py**

Save to `C:\Users\saboo\Desktop\vedio\tts_gen.py`:

```python
"""
tts_gen.py — converts voiceover text to WAV using pyttsx3 (Windows SAPI).
No internet connection or external API needed.
"""
import os

import pyttsx3


def text_to_speech(text: str, output_path: str) -> str:
    """
    Convert text to WAV audio file using Windows SAPI voices.

    Args:
        text: the voiceover narration to speak
        output_path: where to save the WAV file (e.g. 'audio/scene_000.wav')

    Returns:
        output_path (str) — path to saved WAV
    """
    engine = pyttsx3.init()
    engine.setProperty('rate', 145)    # slightly slower than default for clarity
    engine.setProperty('volume', 1.0)

    voices = engine.getProperty('voices')
    if voices:
        # Prefer a female voice (index 1 on most Windows systems = Microsoft Zira)
        voice_index = 1 if len(voices) > 1 else 0
        engine.setProperty('voice', voices[voice_index].id)

    engine.save_to_file(text, output_path)
    engine.runAndWait()
    print(f"  [tts] Saved -> {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    text = " ".join(sys.argv[1:]) or "The future of business is here. AI is transforming everything."
    os.makedirs("audio", exist_ok=True)
    text_to_speech(text, "audio/test_000.wav")
    print("Done. Play audio/test_000.wav to verify.")
```

- [ ] **Step 2: Test TTS generation**

```bash
python tts_gen.py "The future of business is here. AI is transforming everything."
```

Expected: `[tts] Saved -> audio/test_000.wav` and file exists at `audio/test_000.wav` (~50–200KB)

- [ ] **Step 3: Verify the WAV file was created**

```bash
python -c "import os; size=os.path.getsize('audio/test_000.wav'); print(f'WAV size: {size} bytes'); assert size > 1000, 'File too small'"
```

Expected: `WAV size: XXXXX bytes` (should be > 1000)

- [ ] **Step 4: Commit**

```bash
git add tts_gen.py
git commit -m "feat: add pyttsx3 TTS voice generator"
```

---

### Task 7: video_build.py — FFmpeg video assembly

**Files:**
- Create: `video_build.py`

- [ ] **Step 1: Create video_build.py**

Save to `C:\Users\saboo\Desktop\vedio\video_build.py`:

```python
"""
video_build.py — FFmpeg pipeline: image + zoom/pan motion + audio → MP4 clips → final video.
Uses portable FFmpeg from ./ffmpeg/bin/ffmpeg.exe (installed by install.py).
"""
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffmpeg.exe")
FFPROBE = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffprobe.exe")


def _get_audio_duration(audio_path: str) -> float:
    """Return audio duration in seconds using ffprobe. Falls back to 5.0 on error."""
    result = subprocess.run(
        [FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 5.0


def image_to_clip(image_path: str, audio_path: str, output_path: str, duration: float = None) -> str:
    """
    Convert a scene image + audio WAV into an MP4 clip with Ken Burns zoom-in effect.

    Steps internally:
      1. image -> silent MP4 with zoompan filter
      2. silent MP4 + WAV -> final MP4 with AAC audio

    Args:
        image_path: path to PNG scene image
        audio_path: path to WAV voiceover
        output_path: where to save the clip MP4
        duration: clip duration in seconds (auto-detected from audio if None)

    Returns:
        output_path (str)
    """
    if duration is None:
        duration = _get_audio_duration(audio_path)

    video_duration = duration + 0.3  # small buffer so audio doesn't cut
    fps = 24
    total_frames = int(video_duration * fps)

    # Ken Burns zoom-in: starts at zoom=1.0, increases by 0.0015 per frame, max 1.3
    zoom_filter = (
        f"scale=3840:-1,"
        f"zoompan=z='min(zoom+0.0015,1.3)':"
        f"d={total_frames}:"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"s=512x512:fps={fps}"
    )

    silent_path = output_path.replace(".mp4", "_silent.mp4")

    # Step 1: image → silent video with zoom
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

    # Step 2: silent video + audio → clip
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
    print(f"  [video] Clip saved -> {output_path}")
    return output_path


def add_fade(clip_path: str, output_path: str, fade_duration: float = 0.4) -> str:
    """
    Add fade-in at start and fade-out at end of a clip.
    Replaces clip_path with faded version at output_path.

    Args:
        clip_path: input MP4 path
        output_path: output MP4 path
        fade_duration: seconds for each fade (default 0.4)

    Returns:
        output_path (str)
    """
    result = subprocess.run(
        [FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', clip_path],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    fade_out_start = max(0.0, duration - fade_duration)

    subprocess.run([
        FFMPEG, '-y',
        '-i', clip_path,
        '-vf', f'fade=t=in:st=0:d={fade_duration},fade=t=out:st={fade_out_start}:d={fade_duration}',
        '-af', f'afade=t=in:st=0:d={fade_duration},afade=t=out:st={fade_out_start}:d={fade_duration}',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        output_path
    ], check=True, capture_output=True)

    os.remove(clip_path)
    return output_path


def concatenate_clips(clip_paths: list, output_path: str) -> str:
    """
    Concatenate a list of MP4 clips into a single final video.

    Args:
        clip_paths: ordered list of MP4 file paths
        output_path: where to save the final video

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
```

- [ ] **Step 2: Verify syntax**

```bash
python -c "import ast; ast.parse(open('video_build.py').read()); print('video_build.py syntax OK')"
```

Expected: `video_build.py syntax OK`

- [ ] **Step 3: Commit**

```bash
git add video_build.py
git commit -m "feat: add FFmpeg video assembly pipeline"
```

*Note: Full test of video_build.py happens in Task 9 after FFmpeg is installed.*

---

### Task 8: main.py — full orchestrator

**Files:**
- Create: `main.py` (overwrites existing empty file if any)

- [ ] **Step 1: Create main.py**

Save to `C:\Users\saboo\Desktop\vedio\main.py`:

```python
"""
main.py — One-prompt video pipeline orchestrator.

Usage:
    python main.py "Create a UK SaaS marketing reel about AI automation"

Output:
    final/output_<timestamp>.mp4 — full video with voice, motion, and transitions
"""
import os
import sys
import subprocess
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
    """Start ComfyUI as a background process. Returns the Popen object."""
    print("[main] Starting ComfyUI (CPU mode)...")
    proc = subprocess.Popen(
        [sys.executable, "main.py", "--cpu"],
        cwd=COMFY_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # Wait up to 90 seconds for ComfyUI to be ready
    for _ in range(30):
        time.sleep(3)
        if _comfyui_is_running():
            print("[main] ComfyUI is ready.")
            return proc
    raise RuntimeError(
        "ComfyUI did not start within 90 seconds. "
        "Check that ComfyUI is installed (run install.py first)."
    )


def run_pipeline(prompt: str) -> str:
    """
    Full pipeline: prompt string -> final MP4 path.

    Returns:
        Path to the final output video file.
    """
    _ensure_dirs()
    print(f"\n{'='*55}")
    print(f"  AI Video Pipeline")
    print(f"  Prompt: {prompt}")
    print(f"{'='*55}\n")

    # Step 1: Generate script
    print("[main] Generating scene script...")
    scenes = generate_script(prompt)
    total_duration = sum(s['duration_sec'] for s in scenes)
    print(f"[main] {len(scenes)} scenes | estimated ~{total_duration}s video\n")

    # Step 2: Start ComfyUI if not running
    comfy_proc = None
    if not _comfyui_is_running():
        comfy_proc = _start_comfyui()
    else:
        print("[main] ComfyUI already running.")

    clip_paths = []

    # Step 3: Process each scene
    for i, scene in enumerate(scenes):
        print(f"\n[main] ── Scene {i+1}/{len(scenes)} ──")
        print(f"  Voiceover: {scene['voiceover']}")

        image_path = os.path.join(SCENES_DIR, f"scene_{i:03d}.png")
        audio_path = os.path.join(AUDIO_DIR, f"scene_{i:03d}.wav")
        clip_raw = os.path.join(CLIPS_DIR, f"clip_{i:03d}_raw.mp4")
        clip_final = os.path.join(CLIPS_DIR, f"clip_{i:03d}.mp4")

        generate_image(scene["visual_prompt"], image_path, scene_index=i)
        text_to_speech(scene["voiceover"], audio_path)
        image_to_clip(image_path, audio_path, clip_raw, duration=scene["duration_sec"])
        add_fade(clip_raw, clip_final)
        clip_paths.append(clip_final)

    # Step 4: Concatenate all clips
    print(f"\n[main] Assembling final video from {len(clip_paths)} clips...")
    timestamp = int(time.time())
    output_path = os.path.join(FINAL_DIR, f"output_{timestamp}.mp4")
    concatenate_clips(clip_paths, output_path)

    # Step 5: Stop ComfyUI if we started it
    if comfy_proc:
        comfy_proc.terminate()
        print("[main] ComfyUI stopped.")

    print(f"\n{'='*55}")
    print(f"  Done!")
    print(f"  Video: {output_path}")
    print(f"{'='*55}\n")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py \"Your video prompt here\"")
        print('Example: python main.py "Create a UK SaaS marketing reel about AI automation"')
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    run_pipeline(prompt)
```

- [ ] **Step 2: Verify syntax**

```bash
python -c "import ast; ast.parse(open('main.py').read()); print('main.py syntax OK')"
```

Expected: `main.py syntax OK`

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add main pipeline orchestrator"
```

---

### Task 9: Run install.py — full environment setup

**Prerequisites:** Tasks 1–8 must be complete. Internet connection required. Allow 30–60 minutes for first run (4GB model download).

- [ ] **Step 1: Run the setup script**

```bash
cd "C:/Users/saboo/Desktop/vedio"
python install.py
```

Expected output sequence:
```
=======================================================
  AI Video Pipeline — One-Time Setup
=======================================================
[setup] Project folders created.
[setup] Downloading FFmpeg portable (win64)...
  Downloading FFmpeg ...
  100%
  Saved to C:\...\ffmpeg.zip
[setup] Extracting FFmpeg...
[setup] FFmpeg installed.
[setup] Cloning ComfyUI...
  $ git clone https://github.com/comfyanonymous/ComfyUI.git ...
[setup] Installing PyTorch (CPU-only) — this is ~800MB, please wait...
[setup] Installing ComfyUI requirements...
[setup] ComfyUI installed.
[setup] Downloading SD 1.5 model (~4GB) — this will take 10-30 minutes...
  100%
  Saved to C:\...\v1-5-pruned-emaonly.safetensors
[setup] Model downloaded.
=======================================================
  Setup complete!
  Run: python main.py "Your video prompt here"
=======================================================
```

- [ ] **Step 2: Verify FFmpeg installed**

```bash
./ffmpeg/bin/ffmpeg.exe -version 2>&1 | head -1
```

Expected: `ffmpeg version N-XXXXX-...`

- [ ] **Step 3: Verify ComfyUI installed**

```bash
python -c "import sys; sys.path.insert(0, 'ComfyUI'); import folder_paths; print('ComfyUI import OK')"
```

Expected: `ComfyUI import OK`

- [ ] **Step 4: Verify SD 1.5 model exists**

```bash
python -c "import os; p='ComfyUI/models/checkpoints/v1-5-pruned-emaonly.safetensors'; print('Model:', os.path.getsize(p)//1024//1024, 'MB')"
```

Expected: `Model: ~4000 MB` (3900–4200 MB range)

- [ ] **Step 5: Test TTS standalone**

```bash
python tts_gen.py "This is a test of the voice system."
```

Expected: `[tts] Saved -> audio/test_000.wav`

---

### Task 10: End-to-end pipeline test

**Prerequisites:** Task 9 complete. All files created. FFmpeg and ComfyUI installed.

- [ ] **Step 1: Run the full pipeline**

```bash
cd "C:/Users/saboo/Desktop/vedio"
python main.py "Create a UK SaaS marketing reel about AI automation"
```

Expected output:
```
=======================================================
  AI Video Pipeline
  Prompt: Create a UK SaaS marketing reel about AI automation
=======================================================

[main] Generating scene script...
[main] 5 scenes | estimated ~22s video

[main] Starting ComfyUI (CPU mode)...
[main] ComfyUI is ready.

[main] ── Scene 1/5 ──
  Voiceover: The way businesses operate is changing forever.
  [image] Scene 0: submitting to ComfyUI (seed=42)...
  [image] prompt_id=XXXX — waiting for generation (this takes 3–8 min on CPU)...
  [image] Saved -> scenes/scene_000.png
  [tts] Saved -> audio/scene_000.wav
  [video] Clip saved -> clips/clip_000_raw.mp4
...
[main] Assembling final video from 5 clips...
  [video] Final video -> final/output_XXXXXXXXXX.mp4

=======================================================
  Done!
  Video: C:\Users\saboo\Desktop\vedio\final\output_XXXXXXXXXX.mp4
=======================================================
```

Total expected time: **20–50 minutes** (5 scenes × 3–8 min image gen + assembly)

- [ ] **Step 2: Verify output file exists and has size**

```bash
python -c "
import os, glob
files = sorted(glob.glob('final/output_*.mp4'))
assert files, 'No output file found!'
size_mb = os.path.getsize(files[-1]) / 1024 / 1024
print(f'Output: {files[-1]}')
print(f'Size: {size_mb:.1f} MB')
assert size_mb > 0.5, 'File too small — pipeline may have failed'
print('Pipeline test PASSED')
"
```

Expected: `Pipeline test PASSED` with size > 0.5 MB

- [ ] **Step 3: Play the video**

```bash
start final/output_*.mp4
```

Verify: video plays, shows 5 scenes with zoom motion, has voice narration, transitions between scenes.

- [ ] **Step 4: Final commit**

```bash
git add scenes/ audio/ clips/ --ignore-errors
git status
git commit -m "feat: complete AI video pipeline — one prompt to full MP4 with voice"
```

---

## Quick Reference

After setup, generate any video with:

```bash
# Marketing reel
python main.py "Create a UK SaaS marketing reel about AI automation"

# Educational video
python main.py "Create an educational tutorial about machine learning for beginners"

# Social media content
python main.py "Create a viral TikTok about productivity hacks"
```

Output always saved to: `final/output_<timestamp>.mp4`
