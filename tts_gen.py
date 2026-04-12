"""
tts_gen.py — converts voiceover text to WAV using pyttsx3 (Windows SAPI).
No internet or external APIs needed. Works on Python 3.13 + Windows.
"""
import os

import pyttsx3


def text_to_speech(text: str, output_path: str) -> str:
    """
    Convert text to WAV audio using Windows SAPI voices.

    Args:
        text: the voiceover narration to convert
        output_path: where to save the WAV file (e.g. 'audio/scene_000.wav')

    Returns:
        output_path (str)
    """
    engine = pyttsx3.init()
    engine.setProperty('rate', 145)    # 145 WPM — clear, professional pace
    engine.setProperty('volume', 1.0)

    voices = engine.getProperty('voices')
    if voices:
        # Index 1 = Microsoft Zira (female) on most Windows systems
        # Index 0 = Microsoft David (male) fallback
        voice_index = 1 if len(voices) > 1 else 0
        engine.setProperty('voice', voices[voice_index].id)

    engine.save_to_file(text, output_path)
    engine.runAndWait()
    print(f"  [tts] Saved -> {output_path} ({len(text.split())} words)")
    return output_path


if __name__ == "__main__":
    import sys
    text = " ".join(sys.argv[1:]) or (
        "The future of business is here. "
        "AI automation is transforming how companies operate, "
        "and the businesses that adapt fastest will lead their industries."
    )
    os.makedirs("audio", exist_ok=True)
    text_to_speech(text, "audio/test_000.wav")
    print("Done. Play audio/test_000.wav to verify.")
