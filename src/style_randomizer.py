import json
import random
from typing import Dict, Any, List
from src.config import STYLE_HISTORY_FILE

MOTION_STYLES = ["ai_motion", "parallax_zoom", "parallax_pan", "speed_ramp_zoom"]
COLOR_GRADES = ["original", "natural_boost", "warm_sunset", "cool_blue", "high_contrast"]
TEXT_ANIMATIONS = ["fade_in", "slide_up", "typewriter"]
OVERLAY_EFFECTS = ["none", "light_dust_particles", "lens_flare", "film_grain"]
TRANSITION_STYLES = ["crossfade", "whip_pan", "glitch_cut", "light_leak"]

INSTAGRAM_QUOTES = [
    "Every sky tells a story, every cloud has a dream.",
    "Chasing horizons and capturing moments in the sky.",
    "Nature is painting for us, day after day, pictures of infinite beauty.",
    "The sky is a canvas of infinite possibilities.",
    "Sunsets are proof that no matter what happens, every day can end beautifully.",
    "Above the clouds, there is always sunshine.",
    "Sky above, earth below, peace within.",
    "Clouds come floating into my life to add color to my sunset sky.",
    "Look up, there's a whole world of magic floating above us.",
    "Watching the sky change colors is my favorite therapy.",
    "The sky speaks in colors of emotion.",
    "Golden hours and sky power.",
    "Breathe in the sky, exhale the ordinary.",
    "Soft skies and quiet thoughts.",
    "Canvas of heaven painted over Vadodara."
]

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

    motion_style = pick_non_repeating_option(MOTION_STYLES, recent_motions)
    color_grade = pick_non_repeating_option(COLOR_GRADES, recent_colors)
    text_animation = pick_non_repeating_option(TEXT_ANIMATIONS, recent_texts)

    chosen_style = {
        "day": day_number,
        "motion_style": motion_style,
        "color_grade": color_grade,
        "text_animation": text_animation,
        "overlay_effect": "none"
    }

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
        f"• **Text Style**: `{style['text_animation']}`"
    ]
    return "\n".join(lines)

def generate_instagram_caption(day_num: int, style: Dict[str, Any], photo_count: int = 1) -> str:
    """Generates a complete, ready-to-copy Instagram post caption."""
    quote = INSTAGRAM_QUOTES[(day_num - 1) % len(INSTAGRAM_QUOTES)]
    motion_str = style.get("motion_style", "parallax_zoom").replace("_", " ").title()
    color_str = style.get("color_grade", "original").replace("_", " ").title()
    anim_str = style.get("text_animation", "fade_in").replace("_", " ").title()
    
    caption = (
        f"Day {day_num:02d}/30 🌅 Vadodara Sky Challenge\n\n"
        f"\"{quote}\" ✨\n\n"
        f"📍 Location: Vadodara, Gujarat, India\n"
        f"📸 Source: {photo_count} Sky Photo{'s' if photo_count > 1 else ''}\n\n"
        f"🎨 Motion Graphic Presets:\n"
        f"• Motion: {motion_str}\n"
        f"• Color Preset: {color_str}\n"
        f"• Text Style: {anim_str}\n"
        f"• Resolution: 1080x1920 Vertical (30 FPS)\n\n"
        f"#VadodaraSkyChallenge #Vadodara #VadodaraSkies #Skyline #Cloudscape "
        f"#NaturePhotography #InstagramReels #AIReels #ReelsIndia #SunsetLovers #Gujarat"
    )
    return caption
