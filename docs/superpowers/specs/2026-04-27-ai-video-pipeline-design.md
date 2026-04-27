# AI Video Pipeline — Design Specification

**Status:** Approved
**Author:** Muhammad-Adil-code
**Date:** 2026-04-27

## Problem

Generating short marketing reels, educational explainers, and social shorts currently requires either:

1. SaaS APIs (Runway, Pika, Synthesia) — expensive, non-private, rate-limited
2. Manual editing in Premiere/CapCut — slow, requires skill
3. AnimateDiff or full video diffusion — needs a dedicated GPU

I want a third option: a fully local pipeline that takes a single prompt and produces a complete narrated MP4 — runnable on a typical laptop (16 GB RAM, integrated graphics).

## Goals

- **One prompt, one command, one MP4.** No multi-step UI, no manual stitching.
- **Fully local.** No SaaS API calls, no data leaves the machine.
- **Variable duration.** Same pipeline produces a 30-second short or a 5-minute explainer.
- **Reasonable hardware floor.** Must run end-to-end on a CPU-only Windows laptop.
- **Voice-driven.** Every scene has narration synced to its visual.

## Non-goals

- Real frame-by-frame video diffusion (AnimateDiff) — out of scope on integrated GPU.
- Browser UI / web app — pipeline is CLI-first.
- Cross-platform Day 1 — Windows-first, Linux/Mac later.
- Cloud rendering / GPU offload — local only.

## Approach

Three-stage pipeline orchestrated by `main.py`:

1. **Plan** — `script_gen.py` converts the prompt into N scenes, each with a visual prompt + voiceover line. Number of scenes scales with target duration.
2. **Generate** — `image_gen.py` calls a local ComfyUI server for each scene image. `tts_gen.py` produces a WAV per scene from voiceover text.
3. **Assemble** — `video_build.py` uses FFmpeg to add Ken Burns motion to each still, merges audio, adds caption overlay, then concatenates with fades.

ComfyUI runs as a detached background process; `main.py` starts and stops it. Stable Diffusion 1.5 was chosen over SDXL — SD 1.5 is roughly 4× faster on CPU at 512×512 and produces acceptable quality for cinematic, motion-driven scenes where a single still is held under 30 seconds with zoom.

## Component Boundaries

| Module | Inputs | Outputs | Owns |
|---|---|---|---|
| `script_gen.py` | prompt str, target_duration_sec | list of scene dicts | scene templates, type detection, word-count math |
| `image_gen.py` | visual_prompt str, output path | PNG file path | ComfyUI HTTP client, polling, file copy |
| `tts_gen.py` | text str, output path | WAV file path | pyttsx3 engine, voice selection |
| `video_build.py` | image, audio, output path | MP4 file path | FFmpeg invocation, motion filters, concat |
| `main.py` | argv | final MP4 path | ComfyUI lifecycle, scene iteration, final assembly |

Each module is independently testable. `main.py` is the only file that imports more than one of the others.

## Data Flow

```
prompt + duration
     │
     ▼
[script_gen.py]
  scenes = [
    {visual_prompt, voiceover, duration_sec},
    ...
  ]
     │
     │ for each scene:
     ▼
[image_gen.py]   →   scenes/scene_NNN.png
[tts_gen.py]     →   audio/scene_NNN.wav
[video_build.py] →   clips/clip_NNN.mp4
     │
     │ after all scenes:
     ▼
[video_build.py concatenate_clips]
     │
     ▼
final/output_TIMESTAMP.mp4
```

## Design Decisions

**Why CPU-only as the baseline?**
The target user has a laptop with integrated graphics. A pipeline that requires a GPU has zero adoption ceiling but a high adoption floor. Better to optimise for the floor and let GPU users get the same code running 10× faster.

**Why ComfyUI over diffusers directly?**
ComfyUI's API is stable, the workflow JSON is portable, and switching to a different checkpoint (SDXL, Pony, etc.) is a one-line change in `workflow.json`. Direct `diffusers` integration would require maintaining model loading and pipeline code.

**Why pyttsx3 for TTS instead of Coqui or Bark?**
pyttsx3 uses native Windows SAPI voices — no model download, instant generation, works on Python 3.13. Coqui TTS has Python 3.13 compatibility issues at this point and adds 1 GB of model files. Quality is "professional but not premium" — fine for marketing reels where the visuals carry most of the content.

**Why duration-aware scene count?**
A 30-second TikTok wants 5 fast scenes; a 5-minute explainer wants 10 deeper scenes. Forcing a fixed scene count makes one of those bad. Sliding the count with duration keeps per-scene pacing constant (~30 seconds maximum).

**Why Ken Burns instead of true video?**
True video on CPU = AnimateDiff, which is 30+ minutes per scene and crashes on integrated GPU. Ken Burns gives the illusion of motion at the cost of being a "moving still" — acceptable for the use case (the voice carries the content, the visual is atmospheric).

## Risk: CPU generation time

5 scenes × 5 minutes per image = 25 minutes per video. This is a real limitation, not a bug. Mitigations:

- Cache scene images by visual_prompt hash so re-runs of the same prompt are instant
- Allow user to swap to a faster model (e.g. SD-Turbo, LCM) via `workflow.json`
- Document GPU upgrade path clearly so users with hardware can use it

## Open Questions

- Should we add a mode that skips image generation and uses pure FFmpeg kinetic typography? Would be sub-30-second generation and acceptable for some use cases.
- Should `script_gen.py` call a local LLM (Ollama) for higher-quality scripts instead of templates? Quality vs zero-dep trade-off.
- Is 145 WPM the right TTS speed, or should it scale with video type (faster for social, slower for educational)?

These can be addressed in follow-up work — they're not blocking initial release.
