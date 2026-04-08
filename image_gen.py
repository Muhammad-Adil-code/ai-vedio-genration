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
    """Load workflow.json and inject the visual prompt and seed."""
    with open(WORKFLOW_PATH) as f:
        workflow = json.load(f)
    workflow["6"]["inputs"]["text"] = visual_prompt
    workflow["3"]["inputs"]["seed"] = seed
    return workflow


def _submit_prompt(workflow: dict) -> str:
    """POST workflow to ComfyUI /prompt. Returns prompt_id."""
    resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow}, timeout=30)
    resp.raise_for_status()
    return resp.json()["prompt_id"]


def _wait_for_result(prompt_id: str, timeout: int = 900) -> dict:
    """
    Poll GET /history/{prompt_id} until generation completes.
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
    raise TimeoutError(
        f"ComfyUI did not complete prompt {prompt_id} within {timeout}s. "
        f"CPU generation can be slow — try reducing steps in workflow.json (currently 15)."
    )


def _extract_filename(history_entry: dict) -> str:
    """Extract output PNG filename from ComfyUI history entry (node 9 = SaveImage)."""
    return history_entry["outputs"]["9"]["images"][0]["filename"]


def generate_image(visual_prompt: str, output_path: str, scene_index: int = 0) -> str:
    """
    Full image generation:
      visual_prompt -> ComfyUI SD 1.5 (CPU) -> PNG saved to output_path

    Args:
        visual_prompt: descriptive text for the scene image
        output_path: where to save the PNG (e.g. 'scenes/scene_000.png')
        scene_index: used to produce a unique seed per scene

    Returns:
        output_path (str)
    """
    seed = (scene_index * 1337 + 42) % 2147483647
    print(f"  [image] Scene {scene_index}: submitting to ComfyUI (seed={seed}) ...")

    workflow = _load_workflow(visual_prompt, seed)
    prompt_id = _submit_prompt(workflow)
    print(f"  [image] Waiting ... (CPU generation takes 3–8 min, prompt_id={prompt_id})")

    history = _wait_for_result(prompt_id)
    filename = _extract_filename(history)
    src = os.path.join(COMFY_OUTPUT_DIR, filename)
    shutil.copy2(src, output_path)
    print(f"  [image] Saved -> {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    os.makedirs("scenes", exist_ok=True)
    prompt = " ".join(sys.argv[1:]) or "cinematic startup office, golden hour, professional, 8k"
    generate_image(prompt, "scenes/test_000.png", scene_index=0)
