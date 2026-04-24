"""
install.py — One-time setup script.

Run once before using the pipeline:
    python install.py

What it installs (all local, no admin required):
  1. FFmpeg portable (win64) -> ./ffmpeg/
  2. ComfyUI              -> ./ComfyUI/
  3. PyTorch CPU-only     -> pip (site-packages)
  4. SD 1.5 model (~4GB)  -> ./ComfyUI/models/checkpoints/
  5. Python packages      -> pip (requests, pyttsx3)

Total first-run time: 30–60 minutes (mostly model download).
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

    def progress(count, block_size, total_size):
        if total_size > 0:
            pct = min(int(count * block_size * 100 / total_size), 100)
            print(f"  {pct}%  ", end='\r')

    urllib.request.urlretrieve(url, dest_path, reporthook=progress)
    print(f"\n  Saved -> {dest_path}")


def install_ffmpeg():
    ffmpeg_exe = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        print("[setup] FFmpeg already installed, skipping.")
        return

    print("[setup] Downloading FFmpeg portable (win64) ...")
    zip_path = os.path.join(BASE_DIR, "ffmpeg.zip")
    download_file(
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
        "ffmpeg-master-latest-win64-gpl.zip",
        zip_path,
        "FFmpeg"
    )

    print("[setup] Extracting ...")
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

    print("[setup] Cloning ComfyUI ...")
    run(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git", comfy_dir])

    print("[setup] Installing PyTorch CPU-only (~800MB, please wait) ...")
    run([sys.executable, "-m", "pip", "install",
         "torch", "torchvision",
         "--index-url", "https://download.pytorch.org/whl/cpu"])

    print("[setup] Installing ComfyUI requirements ...")
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
    print("[setup] Downloading SD 1.5 model (~4GB, takes 10–30 min) ...")
    download_file(
        "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5"
        "/resolve/main/v1-5-pruned-emaonly.safetensors",
        model_path,
        "Stable Diffusion v1.5"
    )
    print("[setup] Model downloaded.")


def install_python_packages():
    print("[setup] Installing Python packages (requests, pyttsx3) ...")
    run([sys.executable, "-m", "pip", "install", "requests", "pyttsx3"])
    print("[setup] Python packages installed.")


def create_folders():
    for folder in ["scenes", "audio", "clips", "final"]:
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)
    print("[setup] Project folders created.")


if __name__ == "__main__":
    print("=" * 60)
    print("  AI Video Pipeline — One-Time Setup")
    print("=" * 60)

    create_folders()
    install_ffmpeg()
    install_comfyui()
    download_model()
    install_python_packages()

    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("")
    print("  Generate a 2-minute video:")
    print('  python main.py "Create a SaaS marketing reel" --duration 2')
    print("")
    print("  Generate a 5-minute video:")
    print('  python main.py "Create a UK SaaS marketing reel about AI" --duration 5')
    print("=" * 60)
