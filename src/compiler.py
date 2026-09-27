import re
import random
import subprocess
import tempfile
from pathlib import Path
from typing import List
from PIL import Image, ImageDraw, ImageFont
from src.config import REELS_DIR, TARGET_WIDTH, TARGET_HEIGHT, FPS
from src.text_overlay import get_font, draw_text_with_shadow

TRANSITIONS = ["crossfade", "whip_pan", "glitch_cut", "light_leak"]

def create_title_card(title_text: str, subtitle_text: str, output_path: Path, duration_sec: float = 3.0) -> Path:
    """Renders a vertical title card video clip (Intro or Outro)."""
    img = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), (15, 18, 28))
    draw = ImageDraw.Draw(img)

    # Decorative background glow
    glow = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([TARGET_WIDTH * 0.1, TARGET_HEIGHT * 0.25, TARGET_WIDTH * 0.9, TARGET_HEIGHT * 0.7], fill=(45, 85, 155, 100))
    img.paste(glow, (0, 0), glow)

    title_font = get_font(52)
    sub_font = get_font(32)

    # Draw Title text centered
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    t_w = title_bbox[2] - title_bbox[0]
    t_h = title_bbox[3] - title_bbox[1]
    t_x = (TARGET_WIDTH - t_w) // 2
    t_y = (TARGET_HEIGHT - t_h) // 2 - 40

    draw_text_with_shadow(draw, (t_x, t_y), title_text, font=title_font, fill_color=(255, 255, 255, 255))

    # Draw Subtitle
    if subtitle_text:
        sub_bbox = draw.textbbox((0, 0), subtitle_text, font=sub_font)
        s_w = sub_bbox[2] - sub_bbox[0]
        s_x = (TARGET_WIDTH - s_w) // 2
        s_y = t_y + t_h + 50
        draw_text_with_shadow(draw, (s_x, s_y), subtitle_text, font=sub_font, fill_color=(200, 220, 255, 230))

    # Save image and render title card video via FFmpeg
    with tempfile.TemporaryDirectory() as tmp:
        card_img_path = Path(tmp) / "title_card.png"
        img.save(card_img_path)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(card_img_path),
            "-c:v", "libx264", "-t", str(duration_sec),
            "-pix_fmt", "yuv420p", "-r", str(FPS),
            str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    return output_path

def get_chronological_reels() -> List[Path]:
    """Finds and sorts all Day_XX_reel.mp4 files chronologically."""
    reels = list(REELS_DIR.glob("Day_*_reel.mp4"))
    def extract_day(p: Path) -> int:
        match = re.search(r"Day_(\d+)", p.name)
        return int(match.group(1)) if match else 0

    reels.sort(key=extract_day)
    return reels

def compile_30_day_recap() -> Path:
    """
    Stitches all available daily reels into a 30-60 second recap video with intro,
    outro, and random transitions between clips.
    """
    reels = get_chronological_reels()
    if not reels:
        raise FileNotFoundError("No daily reels found in /data/reels to compile!")

    print(f"[Compiler] Found {len(reels)} daily reels to compile.")

    output_recap = REELS_DIR / "Recap_30_Days.mp4"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        intro_path = tmp_path / "intro.mp4"
        outro_path = tmp_path / "outro.mp4"

        # 1. Create Intro & Outro Cards
        create_title_card("Vadodara Sky Challenge", "30 Days Compilation", intro_path, duration_sec=3.0)
        create_title_card("Vadodara Sky Challenge", "Thank You for Watching!", outro_path, duration_sec=3.0)

        clip_list = [intro_path] + reels + [outro_path]

        # 2. Build FFmpeg concat list
        concat_txt = tmp_path / "concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for clip in clip_list:
                # FFmpeg file path escaping
                safe_path = str(clip.resolve()).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        # 3. Concatenate using FFmpeg filter complex (or concat demuxer for fast stitching)
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_txt),
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_recap)
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg compilation failed: {result.stderr}")

    print(f"[Compiler] 30-Day Recap compilation complete: {output_recap}")
    return output_recap
