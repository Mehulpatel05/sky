import json
import random
from typing import Dict, Any, List
from src.config import STYLE_HISTORY_FILE

MOTION_STYLES = ["ai_motion", "parallax_zoom", "parallax_pan", "speed_ramp_zoom"]
COLOR_GRADES = ["original", "natural_boost", "warm_sunset", "cool_blue", "high_contrast"]
TEXT_ANIMATIONS = ["fade_in", "slide_up", "typewriter"]
OVERLAY_EFFECTS = ["light_dust_particles", "lens_flare", "film_grain"]
TRANSITION_STYLES = ["crossfade", "whip_pan", "glitch_cut", "light_leak"]

def load_style_history() -> List[Dict[str, Any]]:
    """Loads past style selections from JSON history file."""
    if not STYLE_HISTORY_FILE.exists():
        return []
    try:
        with open(STYLE_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Warning] Could not load style history: {e}")
        return []

def save_style_history(history: List[Dict[str, Any]]):
    """Saves style selections to JSON history file."""
    try:
        with open(STYLE_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[Error] Failed to save style history: {e}")

def pick_non_repeating_option(options: List[str], recent_used: List[str]) -> str:
    """Selects an option prioritizing those not present in recent_used history."""
    available = [opt for opt in options if opt not in recent_used]
    if available:
        return random.choice(available)
    # If all options were recently used, fall back to random choice
    return random.choice(options)

def generate_reel_style(day_number: int) -> Dict[str, Any]:
    """
    Generates a randomized style combination ensuring no repeats from the last 5 reels.
    """
    history = load_style_history()
    last_5 = history[-5:] if len(history) >= 5 else history

    recent_motions = [h.get("motion_style") for h in last_5 if h.get("motion_style")]
    recent_colors = [h.get("color_grade") for h in last_5 if h.get("color_grade")]
    recent_texts = [h.get("text_animation") for h in last_5 if h.get("text_animation")]
    recent_overlays = [h.get("overlay_effect") for h in last_5 if h.get("overlay_effect") and h.get("overlay_effect") != "none"]

    motion_style = pick_non_repeating_option(MOTION_STYLES, recent_motions)
    color_grade = pick_non_repeating_option(COLOR_GRADES, recent_colors)
    text_animation = pick_non_repeating_option(TEXT_ANIMATIONS, recent_texts)

    # 30% chance for an overlay effect
    if random.random() < 0.30:
        overlay_effect = pick_non_repeating_option(OVERLAY_EFFECTS, recent_overlays)
    else:
        overlay_effect = "none"

    chosen_style = {
        "day": day_number,
        "motion_style": motion_style,
        "color_grade": color_grade,
        "text_animation": text_animation,
        "overlay_effect": overlay_effect
    }

    # Record in history
    history.append(chosen_style)
    save_style_history(history)

    return chosen_style

def format_style_summary(style: Dict[str, Any], motion_mode_used: str = "") -> str:
    """Formats a human-readable text summary of chosen styles for Telegram caption."""
    motion_display = style['motion_style']
    if motion_mode_used:
        motion_display += f" ({motion_mode_used})"
        
    lines = [
        f"🎨 **Style Combination (Day {style.get('day', '?')})**",
        f"• **Motion**: `{motion_display}`",
        f"• **Color Grade**: `{style['color_grade']}`",
        f"• **Text Style**: `{style['text_animation']}`",
        f"• **Overlay**: `{style['overlay_effect']}`"
    ]
    return "\n".join(lines)
