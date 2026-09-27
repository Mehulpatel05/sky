import cv2
import numpy as np
import subprocess
import shutil
import tempfile
import math
import random
from pathlib import Path
from PIL import Image
from typing import List, Dict, Any, Optional
from src.config import TARGET_WIDTH, TARGET_HEIGHT, FPS, REEL_DURATION_SEC, ASSETS_DIR

AUDIO_DIR = ASSETS_DIR / "audio"

def get_random_audio_track() -> Optional[Path]:
    """Finds a random ambient background audio track from assets/audio/ if present."""
    if not AUDIO_DIR.exists():
        return None
    audio_files = list(AUDIO_DIR.glob("*.mp3")) + list(AUDIO_DIR.glob("*.m4a")) + list(AUDIO_DIR.glob("*.wav"))
    if audio_files:
        return random.choice(audio_files)
    return None

def apply_color_grade(frame_rgb: np.ndarray, color_preset: str) -> np.ndarray:
    """
    100% Pure & Crystal Clear Photo Preservation.
    No color distortion or quality degradation.
    """
    return frame_rgb

def apply_motion_graphic_overlay(frame_rgb: np.ndarray, overlay_preset: str, frame_idx: int, total_frames: int) -> np.ndarray:
    """
    Keeps photo 100% crystal clear.
    Disables all obstructive bubbles, particles, and heavy overlays.
    """
    return frame_rgb

def render_reel(
    raw_frames: List[np.ndarray],
    text_overlay_frames: List[Image.Image],
    style: Dict[str, Any],
    output_path: Path,
    fps: int = FPS,
    audio_path: Optional[Path] = None
) -> Path:
    """
    Composites base motion frames + clean typography overlays,
    merges background audio, and encodes to 1080x1920 crystal clear vertical H.264 mp4 video.
    """
    total_frames = min(len(raw_frames), len(text_overlay_frames))
    if total_frames == 0:
        raise ValueError("No frames provided for rendering.")

    print(f"[Renderer] Rendering {total_frames} frames (100% crystal clear photo quality)...")

    if audio_path is None:
        audio_path = get_random_audio_track()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for idx in range(total_frames):
            frame_rgb = raw_frames[idx]
            text_pil = text_overlay_frames[idx]

            # Composite Animated Text & Progress Bar onto crystal clear photo frame
            bg_pil = Image.fromarray(frame_rgb).convert("RGBA")
            composite_pil = Image.alpha_composite(bg_pil, text_pil).convert("RGB")

            frame_file = temp_path / f"frame_{idx:05d}.png"
            composite_pil.save(frame_file)

        # Build FFmpeg command for ultra-crisp output (CRF 16)
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(temp_path / "frame_%05d.png")
        ]

        if audio_path and audio_path.exists():
            print(f"[Renderer] Merging background music: {audio_path.name}")
            duration_sec = total_frames / float(fps)
            cmd.extend([
                "-i", str(audio_path),
                "-t", str(duration_sec),
                "-c:a", "aac", "-b:a", "192k",
                "-shortest"
            ])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "16",  # Ultra-high quality visual output
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path)
        ])

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed: {result.stderr}")

    print(f"[Renderer] Render successful: {output_path}")
    return output_path
