import numpy as np
import cv2
from typing import List, Tuple, Union
from src.config import USE_AI_MOTION, TARGET_WIDTH, TARGET_HEIGHT, FPS, REEL_DURATION_SEC
from src.depth_parallax import generate_parallax_frames
from src.ai_motion import generate_svd_motion

def crossfade_transition(clip1_frames: List[np.ndarray], clip2_frames: List[np.ndarray], transition_frames: int = 15) -> List[np.ndarray]:
    """Applies a smooth crossfade blend transition between two clip frame sequences."""
    if not clip1_frames or not clip2_frames:
        return clip1_frames + clip2_frames

    num_trans = min(transition_frames, len(clip1_frames), len(clip2_frames))
    base1 = clip1_frames[:-num_trans]
    trans1 = clip1_frames[-num_trans:]
    trans2 = clip2_frames[:num_trans]
    base2 = clip2_frames[num_trans:]

    blended = []
    for i in range(num_trans):
        alpha = i / float(num_trans - 1) if num_trans > 1 else 0.5
        f1 = trans1[i].astype(np.float32)
        f2 = trans2[i].astype(np.float32)
        blend = cv2.addWeighted(f1, 1.0 - alpha, f2, alpha, 0)
        blended.append(blend.astype(np.uint8))

    return base1 + blended + base2

def generate_motion(
    image_paths: Union[str, List[str]],
    motion_style: str = "parallax_zoom",
    duration_sec: float = REEL_DURATION_SEC,
    fps: int = FPS,
    target_w: int = TARGET_WIDTH,
    target_h: int = TARGET_HEIGHT
) -> Tuple[List[np.ndarray], str]:
    """
    Generates a full 15-second motion graphic video sequence.
    Supports single photo OR multiple photos (album upload) with seamless transitions.
    """
    if isinstance(image_paths, str):
        paths = [image_paths]
    else:
        paths = list(image_paths)

    if not paths:
        raise ValueError("No image paths provided for motion generation.")

    total_frames = max(375, int(duration_sec * fps)) # Guarantee min 15 seconds (375 frames)
    num_images = len(paths)

    # 1. Single Photo Mode (Full 15-second camera flight)
    if num_images == 1:
        path = paths[0]
        if motion_style == "ai_motion" and USE_AI_MOTION:
            try:
                print("[MotionEngine] Attempting SVD AI motion generation...")
                frames = generate_svd_motion(
                    image_path=path,
                    duration_sec=duration_sec,
                    fps=fps,
                    target_w=target_w,
                    target_h=target_h
                )
                return frames, "SVD-AI Motion (GPU)"
            except Exception as e:
                print(f"[Warning] SVD AI motion failed: {e}. Auto-falling back to 15s Depth Parallax.")

        effective_style = "parallax_zoom" if motion_style == "ai_motion" else motion_style
        frames = generate_parallax_frames(
            image_path=path,
            motion_style=effective_style,
            duration_sec=duration_sec,
            fps=fps,
            target_w=target_w,
            target_h=target_h
        )
        return frames, f"Depth Parallax 15s ({effective_style})"

    # 2. Multi-Photo Mode (Album upload split evenly over 15 seconds)
    print(f"[MotionEngine] Generating 15-second multi-photo reel with {num_images} images...")
    per_image_duration = duration_sec / float(num_images)

    clips = []
    for idx, path in enumerate(paths):
        sub_frames = generate_parallax_frames(
            image_path=path,
            motion_style="parallax_pan" if idx % 2 == 1 else "parallax_zoom",
            duration_sec=per_image_duration,
            fps=fps,
            target_w=target_w,
            target_h=target_h
        )
        clips.append(sub_frames)

    # Stitch clips with crossfade transitions
    combined = clips[0]
    for k in range(1, len(clips)):
        combined = crossfade_transition(combined, clips[k], transition_frames=12)

    # Adjust combined length to exactly total_frames (375 frames = 15s)
    if len(combined) < total_frames:
        # Pad last frame if needed
        last_frame = combined[-1]
        while len(combined) < total_frames:
            combined.append(last_frame)
    elif len(combined) > total_frames:
        combined = combined[:total_frames]

    return combined, f"Multi-Photo ({num_images} Sky Photos, 15s)"
