import os
import math
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import List, Optional, Tuple
from src.config import FONTS_DIR, TARGET_WIDTH, TARGET_HEIGHT

def get_font(font_size: int = 42) -> ImageFont.ImageFont:
    """Retrieves or downloads clean Poppins-Bold Google Font."""
    font_path = FONTS_DIR / "Poppins-Bold.ttf"
    if not font_path.exists():
        url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf"
        try:
            print(f"[TextOverlay] Downloading Poppins font to {font_path}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(font_path, 'wb') as out_file:
                out_file.write(response.read())
        except Exception as e:
            print(f"[Warning] Could not download Poppins font ({e}). Using default PIL font.")
            return ImageFont.load_default()

    try:
        return ImageFont.truetype(str(font_path), font_size)
    except Exception:
        return ImageFont.load_default()

def draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    shadow_color: Tuple[int, int, int, int] = (0, 0, 0, 200)
):
    """Draws multi-layer drop shadow text for maximum readability and crisp contrast."""
    x, y = position
    shadow_offsets = [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4)]
    for dx, dy in shadow_offsets:
        draw.text((x + dx, y + dy), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill_color)

def draw_glassmorphism_card(
    overlay: Image.Image,
    rect: Tuple[int, int, int, int],
    bg_alpha: int = 120,
    border_alpha: int = 70
):
    """Renders a modern translucent Glassmorphism lower-third container card."""
    draw = ImageDraw.Draw(overlay)
    x1, y1, x2, y2 = rect

    # Card background (dark translucent glass)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=16, fill=(12, 16, 26, bg_alpha))
    # Glass border highlight
    draw.rounded_rectangle([x1, y1, x2, y2], radius=16, outline=(255, 255, 255, border_alpha), width=2)

def generate_progress_bar_layer(
    day_number: int,
    total_days: int = 30,
    progress_ratio: float = 1.0,
    width: int = TARGET_WIDTH,
    height: int = TARGET_HEIGHT
) -> Image.Image:
    """Renders a glowing modern progress bar graphic."""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    bar_width = int(width * 0.72)
    bar_height = 8
    bar_x = (width - bar_width) // 2
    bar_y = height - 120

    max_ratio = max(1, min(day_number, total_days)) / float(total_days)
    curr_filled_width = int(bar_width * max_ratio * max(0.0, min(1.0, progress_ratio)))

    # Track background
    draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
        radius=4,
        fill=(255, 255, 255, 55)
    )

    # Filled progress track
    if curr_filled_width > 0:
        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + curr_filled_width, bar_y + bar_height],
            radius=4,
            fill=(255, 255, 255, 240)
        )

    return overlay

def generate_text_overlay_frames(
    day_number: int,
    text_animation: str = "fade_in",
    num_frames: int = 450,  # 15s @ 30fps = 450 frames
    target_w: int = TARGET_WIDTH,
    target_h: int = TARGET_HEIGHT
) -> List[Image.Image]:
    """
    Generates high-end Glassmorphism motion graphic typography overlay frames for 15 seconds.
    """
    font_large = get_font(72)
    font_medium = get_font(42)
    font_small = get_font(30)

    intro_title = f"DAY {day_number:02d}"
    intro_subtitle = "VADODARA SKY CHALLENGE"
    bottom_text = f"Day {day_number}/30 — Vadodara Sky Challenge"
    outro_text = "Follow 30 Days of Vadodara Skies"

    frames = []

    for i in range(num_frames):
        t = i / max(1, num_frames - 1)  # [0..1] over 15 seconds
        frame = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        # STAGE 1: INTRO MOTION GRAPHICS TITLE (0.0s – 3.0s -> t in 0.0 to 0.20)
        if t <= 0.20:
            stage_t = t / 0.20
            if stage_t < 0.8:
                alpha = int(255 * min(1.0, stage_t / 0.25))
            else:
                alpha = int(255 * ((1.0 - stage_t) / 0.2))

            # Glassmorphism Card Container for Intro
            card_w = int(target_w * 0.85)
            card_h = 240
            card_x1 = (target_w - card_w) // 2
            card_y1 = target_h // 2 - 120
            card_x2 = card_x1 + card_w
            card_y2 = card_y1 + card_h

            draw_glassmorphism_card(frame, (card_x1, card_y1, card_x2, card_y2), bg_alpha=int(140 * (alpha / 255.0)), border_alpha=int(90 * (alpha / 255.0)))
            draw = ImageDraw.Draw(frame)

            # "DAY N" Title
            bbox_t = draw.textbbox((0, 0), intro_title, font=font_large)
            tw = bbox_t[2] - bbox_t[0]
            th = bbox_t[3] - bbox_t[1]
            tx = (target_w - tw) // 2
            ty = card_y1 + 35

            draw_text_with_shadow(
                draw, (tx, ty), intro_title, font=font_large,
                fill_color=(255, 255, 255, alpha),
                shadow_color=(0, 0, 0, int(alpha * 0.8))
            )

            # Accent line
            line_w = int(tw * min(1.0, stage_t * 1.5))
            line_x1 = (target_w - line_w) // 2
            line_y = ty + th + 15
            draw.line([(line_x1, line_y), (line_x1 + line_w, line_y)], fill=(255, 255, 255, alpha), width=3)

            # Subtitle
            bbox_sub = draw.textbbox((0, 0), intro_subtitle, font=font_small)
            sw = bbox_sub[2] - bbox_sub[0]
            sx = (target_w - sw) // 2
            sy = line_y + 18

            draw_text_with_shadow(
                draw, (sx, sy), intro_subtitle, font=font_small,
                fill_color=(230, 240, 255, alpha),
                shadow_color=(0, 0, 0, int(alpha * 0.7))
            )

        # STAGE 2: MAIN REVEAL & GLASSMORPHISM LOWER THIRD (3.0s – 12.5s -> t in 0.20 to 0.83)
        elif t <= 0.83:
            stage_t = (t - 0.20) / (0.83 - 0.20)
            alpha = int(255 * min(1.0, stage_t / 0.08))

            bbox = draw.textbbox((0, 0), bottom_text, font=font_medium)
            bw = bbox[2] - bbox[0]
            bx = (target_w - bw) // 2
            by = target_h - 185

            # Glassmorphism Lower-Third Card
            card_w = bw + 70
            card_h = 75
            card_x1 = (target_w - card_w) // 2
            card_y1 = by - 15
            card_x2 = card_x1 + card_w
            card_y2 = card_y1 + card_h

            draw_glassmorphism_card(frame, (card_x1, card_y1, card_x2, card_y2), bg_alpha=int(110 * (alpha / 255.0)), border_alpha=int(60 * (alpha / 255.0)))
            draw = ImageDraw.Draw(frame)

            draw_text_with_shadow(
                draw, (bx, by), bottom_text, font=font_medium,
                fill_color=(255, 255, 255, alpha),
                shadow_color=(0, 0, 0, int(alpha * 0.7))
            )

            progress_layer = generate_progress_bar_layer(
                day_number=day_number,
                total_days=30,
                progress_ratio=stage_t,
                width=target_w,
                height=target_h
            )
            frame = Image.alpha_composite(frame, progress_layer)

        # STAGE 3: OUTRO CTA HOLD (12.5s – 15.0s -> t > 0.83)
        else:
            stage_t = (t - 0.83) / (1.0 - 0.83)
            alpha = 255

            bbox = draw.textbbox((0, 0), bottom_text, font=font_medium)
            bw = bbox[2] - bbox[0]
            bx = (target_w - bw) // 2
            by = target_h - 225

            # Glassmorphism Card
            card_w = bw + 80
            card_h = 115
            card_x1 = (target_w - card_w) // 2
            card_y1 = by - 15
            card_x2 = card_x1 + card_w
            card_y2 = card_y1 + card_h

            draw_glassmorphism_card(frame, (card_x1, card_y1, card_x2, card_y2), bg_alpha=120, border_alpha=75)
            draw = ImageDraw.Draw(frame)

            draw_text_with_shadow(
                draw, (bx, by), bottom_text, font=font_medium,
                fill_color=(255, 255, 255, alpha),
                shadow_color=(0, 0, 0, 180)
            )

            # CTA Subtitle
            bbox_cta = draw.textbbox((0, 0), outro_text, font=font_small)
            cw = bbox_cta[2] - bbox_cta[0]
            cx = (target_w - cw) // 2
            cy = by + 52

            draw_text_with_shadow(
                draw, (cx, cy), outro_text, font=font_small,
                fill_color=(255, 220, 150, alpha),
                shadow_color=(0, 0, 0, 180)
            )

            progress_layer = generate_progress_bar_layer(
                day_number=day_number,
                total_days=30,
                progress_ratio=1.0,
                width=target_w,
                height=target_h
            )
            frame = Image.alpha_composite(frame, progress_layer)

        frames.append(frame)

    return frames
