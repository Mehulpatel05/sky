import cv2
import numpy as np
import torch
import math
from pathlib import Path
from PIL import Image
from typing import Tuple, Optional, List
from src.config import TARGET_WIDTH, TARGET_HEIGHT, FPS, REEL_DURATION_SEC, MODELS_DIR

# Global cache for Depth Estimation model & processor
_DEPTH_PROCESSOR = None
_DEPTH_MODEL = None
_DEPTH_DEVICE = None

def get_depth_model():
    """Loads lightweight depth estimation model (AutoImageProcessor & AutoModelForDepthEstimation)."""
    global _DEPTH_PROCESSOR, _DEPTH_MODEL, _DEPTH_DEVICE
    if _DEPTH_MODEL is not None:
        return _DEPTH_PROCESSOR, _DEPTH_MODEL, _DEPTH_DEVICE

    _DEPTH_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[DepthParallax] Loading DepthAnything model on {_DEPTH_DEVICE}...")

    try:
        from transformers import AutoImageProcessor, AutoModelForDepthEstimation
        model_id = "LiheYoung/depth-anything-small-hf"
        processor = AutoImageProcessor.from_pretrained(model_id, cache_dir=str(MODELS_DIR))
        model = AutoModelForDepthEstimation.from_pretrained(model_id, cache_dir=str(MODELS_DIR))
        model.to(_DEPTH_DEVICE)
        model.eval()

        _DEPTH_PROCESSOR = processor
        _DEPTH_MODEL = model
        return _DEPTH_PROCESSOR, _DEPTH_MODEL, _DEPTH_DEVICE

    except Exception as e:
        print(f"[Warning] Failed to load DepthAnything model ({e}). Attempting MiDaS torch hub...")

    try:
        midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small", trust_repo=True)
        midas.to(_DEPTH_DEVICE)
        midas.eval()
        _DEPTH_MODEL = midas
        return None, _DEPTH_MODEL, _DEPTH_DEVICE
    except Exception as e2:
        print(f"[Warning] Could not load MiDaS model ({e2}). Using sky gradient depth map.")
        return None, None, _DEPTH_DEVICE

def estimate_depth(img_rgb: np.ndarray) -> np.ndarray:
    """
    Estimates depth map for an RGB image.
    Returns normalized depth array (0.0 = background/sky, 1.0 = foreground).
    """
    h, w = img_rgb.shape[:2]
    processor, model, device = get_depth_model()

    if model is not None:
        try:
            if processor is not None:
                pil_img = Image.fromarray(img_rgb)
                inputs = processor(images=pil_img, return_tensors="pt").to(device)
                with torch.no_grad():
                    outputs = model(**inputs)
                    predicted_depth = outputs.predicted_depth

                prediction = torch.nn.functional.interpolate(
                    predicted_depth.unsqueeze(1),
                    size=(h, w),
                    mode="bicubic",
                    align_corners=False
                ).squeeze()
                depth = prediction.cpu().numpy()
            else:
                midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
                transform = midas_transforms.small_transform
                input_batch = transform(img_rgb).to(device)
                with torch.no_grad():
                    prediction = model(input_batch)
                    prediction = torch.nn.functional.interpolate(
                        prediction.unsqueeze(1),
                        size=(h, w),
                        mode="bicubic",
                        align_corners=False
                    ).squeeze()
                depth = prediction.cpu().numpy()

            d_min, d_max = depth.min(), depth.max()
            if d_max > d_min:
                depth = (depth - d_min) / (d_max - d_min)
            else:
                depth = np.zeros((h, w), dtype=np.float32)
            return depth.astype(np.float32)

        except Exception as e:
            print(f"[Warning] Depth estimation error: {e}. Falling back to gradient depth map.")

    y_coords = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    depth = np.repeat(y_coords, w, axis=1)
    return depth

def enhance_image_sharpness(img_rgb: np.ndarray) -> np.ndarray:
    """Ultra-high clarity unsharp mask sharpening for crisp cloud textures."""
    gaussian = cv2.GaussianBlur(img_rgb, (0, 0), 3.0)
    unsharp = cv2.addWeighted(img_rgb, 1.35, gaussian, -0.35, 0)
    return np.clip(unsharp, 0, 255).astype(np.uint8)

def fit_to_vertical_canvas(image: np.ndarray, target_w: int = TARGET_WIDTH, target_h: int = TARGET_HEIGHT) -> np.ndarray:
    """Crops and resizes image to fit 1080x1920 vertical canvas using 8x8 Lanczos resampling."""
    h, w = image.shape[:2]
    target_ratio = target_w / target_h
    img_ratio = w / h

    if img_ratio > target_ratio:
        new_w = int(h * target_ratio)
        start_x = (w - new_w) // 2
        cropped = image[:, start_x:start_x + new_w]
    else:
        new_h = int(w / target_ratio)
        start_y = (h - new_h) // 2
        cropped = image[start_y:start_y + new_h, :]

    # Use INTER_LANCZOS4 for maximum image sharpness and resolution detail
    resized = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    return resized

def quintic_ease_in_out(t: float) -> float:
    """Ultra-smooth 5th order quintic S-curve easing function."""
    if t < 0.5:
        return 16.0 * t * t * t * t * t
    else:
        return 1.0 - math.pow(-2.0 * t + 2.0, 5) / 2.0

def generate_parallax_frames(
    image_path: str,
    motion_style: str = "parallax_zoom",
    duration_sec: float = REEL_DURATION_SEC,
    fps: int = FPS,
    target_w: int = TARGET_WIDTH,
    target_h: int = TARGET_HEIGHT
) -> List[np.ndarray]:
    """
    Generates high-end 15-second 4K/HD quality depth motion frames using Lanczos resampling & cubic remapping.
    """
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Could not load image at {image_path}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_fitted = fit_to_vertical_canvas(img_rgb, target_w, target_h)
    img_enhanced = enhance_image_sharpness(img_fitted)

    depth = estimate_depth(img_enhanced)
    depth_smooth = cv2.GaussianBlur(depth, (25, 25), 0)

    total_frames = int(duration_sec * fps)
    frames = []

    grid_y, grid_x = np.mgrid[0:target_h, 0:target_w].astype(np.float32)

    for i in range(total_frames):
        t = i / max(1, total_frames - 1)

        if motion_style == "parallax_pan":
            pan_x = math.sin(t * math.pi * 1.5) * 45.0
            pan_y = math.cos(t * math.pi) * 25.0
            zoom = 1.04 + 0.05 * math.sin(t * math.pi)

            disp_x = (pan_x + (grid_x - target_w / 2.0) * (zoom - 1.0)) * (0.2 + 0.8 * depth_smooth)
            disp_y = (pan_y + (grid_y - target_h / 2.0) * (zoom - 1.0)) * (0.2 + 0.8 * depth_smooth)

        elif motion_style == "speed_ramp_zoom":
            ease_t = quintic_ease_in_out(t)
            zoom = 1.0 + 0.14 * ease_t
            pan_y = -30.0 * math.sin(t * math.pi)

            disp_x = (grid_x - target_w / 2.0) * (zoom - 1.0) * (0.25 + 0.75 * (1.0 - depth_smooth))
            disp_y = (pan_y + (grid_y - target_h / 2.0) * (zoom - 1.0)) * (0.25 + 0.75 * (1.0 - depth_smooth))

        else:  # parallax_zoom / ai_motion
            ease_t = quintic_ease_in_out(t)
            zoom = 1.0 + 0.10 * ease_t
            pan_x = 20.0 * math.sin(t * math.pi * 2.0)
            pan_y = -15.0 * t

            disp_x = (pan_x + (grid_x - target_w / 2.0) * (zoom - 1.0)) * (0.3 + 0.7 * (1.0 - depth_smooth))
            disp_y = (pan_y + (grid_y - target_h / 2.0) * (zoom - 1.0)) * (0.3 + 0.7 * (1.0 - depth_smooth))

        map_x = (grid_x - disp_x).astype(np.float32)
        map_y = (grid_y - disp_y).astype(np.float32)

        # High quality spatial bicubic remapping
        warped = cv2.remap(img_enhanced, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        frames.append(warped)

    return frames
