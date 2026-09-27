import torch
import numpy as np
import cv2
from PIL import Image
from typing import List, Optional
from src.config import TARGET_WIDTH, TARGET_HEIGHT, FPS, MODELS_DIR

# Cache pipeline instance
_SVD_PIPELINE = None

def check_gpu_memory() -> bool:
    """Checks if CUDA is available and has at least ~6GB free VRAM for SVD."""
    if not torch.cuda.is_available():
        return False
    try:
        free_bytes, total_bytes = torch.cuda.mem_get_info()
        free_gb = free_bytes / (1024 ** 3)
        print(f"[AIMotion] Available VRAM: {free_gb:.2f} GB")
        return free_gb >= 5.5
    except Exception as e:
        print(f"[AIMotion] Error querying GPU memory: {e}")
        return False

def get_svd_pipeline():
    """Loads Stable Video Diffusion pipeline with FP16 precision."""
    global _SVD_PIPELINE
    if _SVD_PIPELINE is not None:
        return _SVD_PIPELINE

    if not check_gpu_memory():
        raise RuntimeError("Insufficient VRAM or CUDA unavailable for SVD generation.")

    from diffusers import StableVideoDiffusionPipeline

    print("[AIMotion] Loading Stable Video Diffusion (SVD-XT) pipeline...")
    model_id = "stabilityai/stable-video-diffusion-img2vid-xt"

    try:
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            variant="fp16",
            cache_dir=str(MODELS_DIR)
        )
        pipe.to("cuda")
        pipe.enable_model_cpu_offload()  # Saves VRAM
        _SVD_PIPELINE = pipe
        return _SVD_PIPELINE
    except Exception as e:
        raise RuntimeError(f"Failed to load SVD pipeline: {e}")

def generate_svd_motion(
    image_path: str,
    duration_sec: float = 4.0,
    fps: int = FPS,
    target_w: int = TARGET_WIDTH,
    target_h: int = TARGET_HEIGHT
) -> List[np.ndarray]:
    """
    Generates video frame sequence using Stable Video Diffusion (SVD).
    Returns list of RGB numpy arrays formatted to 1080x1920 vertical canvas.
    """
    pipe = get_svd_pipeline()

    # Load image and resize to SVD standard aspect ratio (e.g. 576x1024 for vertical)
    init_image = Image.open(image_path).convert("RGB")
    svd_w, svd_h = 576, 1024
    init_image = init_image.resize((svd_w, svd_h), Image.Resampling.LANCZOS)

    num_frames = int(duration_sec * 6)  # SVD generates around 14-25 frames

    print(f"[AIMotion] Generating AI video frames with SVD-XT...")
    generator = torch.manual_seed(42)
    output_frames = pipe(
        init_image,
        decode_chunk_size=4,
        generator=generator,
        motion_bucket_id=127,  # Subtle cloud motion
        noise_aug_strength=0.02,
        num_frames=max(14, min(num_frames, 25))
    ).frames[0]

    # Convert PIL frames to numpy arrays resized to target vertical canvas (1080x1920)
    resized_frames = []
    for frame_pil in output_frames:
        frame_np = np.array(frame_pil)
        frame_resized = cv2.resize(frame_np, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
        resized_frames.append(frame_resized)

    return resized_frames
