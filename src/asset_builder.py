import os
import cv2
import math
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from src.config import ASSETS_DIR

OVERLAYS_DIR = ASSETS_DIR / "overlays"
PARTICLES_DIR = ASSETS_DIR / "particles"
TEMPLATES_DIR = ASSETS_DIR / "templates"

def init_asset_directories():
    OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
    PARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

def generate_light_leak_asset(width: int = 1080, height: int = 1920, style: str = "golden_hour") -> np.ndarray:
    """Generates high-resolution optical light leak texture overlay."""
    img = np.zeros((height, width, 3), dtype=np.float32)

    if style == "golden_hour":
        # Warm golden-red sun flare from top-right corner
        cv2.circle(img, (int(width * 0.85), int(height * 0.15)), int(width * 0.6), (255, 180, 80), -1)
        cv2.circle(img, (int(width * 0.70), int(height * 0.25)), int(width * 0.4), (255, 120, 40), -1)
        img = cv2.GaussianBlur(img, (199, 199), 0)

    elif style == "cyan_anamorphic":
        # Horizontal anamorphic cyan streak
        cv2.ellipse(img, (int(width * 0.5), int(height * 0.3)), (int(width * 0.8), int(height * 0.08)), 15, 0, 360, (80, 220, 255), -1)
        img = cv2.GaussianBlur(img, (151, 151), 0)

    else: # sunset_violet
        cv2.circle(img, (int(width * 0.2), int(height * 0.8)), int(width * 0.7), (200, 100, 255), -1)
        img = cv2.GaussianBlur(img, (199, 199), 0)

    out = np.clip(img, 0.0, 255.0).astype(np.uint8)
    return out

def generate_bokeh_particle_asset(width: int = 1080, height: int = 1920, seed: int = 42) -> np.ndarray:
    """Generates multi-depth bokeh particle texture asset."""
    np.random.seed(seed)
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # 40 Soft floating bokeh circles of varying sizes and opacities
    for p in range(45):
        cx = int(np.random.randint(0, width))
        cy = int(np.random.randint(0, height))
        radius = int(np.random.randint(15, 65))
        brightness = np.random.randint(140, 255)
        color = (brightness, int(brightness * 0.85), int(brightness * 0.6))

        overlay = img.copy()
        cv2.circle(overlay, (cx, cy), radius, color, -1)
        # Soft blur border
        blur_size = radius if radius % 2 == 1 else radius + 1
        overlay = cv2.GaussianBlur(overlay, (blur_size, blur_size), 0)
        img = cv2.addWeighted(img, 1.0, overlay, 0.4, 0)

    return img

def build_motion_graphic_dataset():
    """Generates and prepares the full local motion graphic asset library."""
    init_asset_directories()
    print("[AssetBuilder] Building & training motion graphic asset dataset...")

    # 1. Build Light Leak Overlays
    for style in ["golden_hour", "cyan_anamorphic", "sunset_violet"]:
        out_path = OVERLAYS_DIR / f"light_leak_{style}.png"
        if not out_path.exists():
            leak_img = generate_light_leak_asset(1080, 1920, style)
            cv2.imwrite(str(out_path), cv2.cvtColor(leak_img, cv2.COLOR_RGB2BGR))

    # 2. Build Bokeh Particle Datasets
    for i in range(3):
        out_path = PARTICLES_DIR / f"bokeh_particles_{i+1}.png"
        if not out_path.exists():
            bokeh_img = generate_bokeh_particle_asset(1080, 1920, seed=100 + i)
            cv2.imwrite(str(out_path), cv2.cvtColor(bokeh_img, cv2.COLOR_RGB2BGR))

    print(f"[AssetBuilder] Dataset ready! Overlays in {OVERLAYS_DIR}, Particles in {PARTICLES_DIR}")

if __name__ == "__main__":
    build_motion_graphic_dataset()
