import sys
import shutil
from pathlib import Path

# Configure UTF-8 encoding for Windows console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.config import TELEGRAM_BOT_TOKEN, AUTHORIZED_CHAT_ID, USE_AI_MOTION
from src.bot import run_bot

def main():
    print("=" * 60)
    print(" 🌅 Vadodara Sky Challenge — Automated Reel Generation System")
    print("=" * 60)

    # Verify FFmpeg is installed
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        print("[CAUTION] FFmpeg was not found in system PATH!")
        print("Please install FFmpeg and add it to your system PATH environment variable.")
        sys.exit(1)
    else:
        print(f"✓ FFmpeg detected at: {ffmpeg_path}")

    # Check Telegram Token configuration
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("[WARNING] TELEGRAM_BOT_TOKEN is not configured in .env file!")
        print("Please edit your .env file and set your TELEGRAM_BOT_TOKEN from @BotFather.")

    if AUTHORIZED_CHAT_ID:
        print(f"✓ Bot access restricted to Authorized Chat ID: {AUTHORIZED_CHAT_ID}")
    else:
        print("ℹ Bot access is unrestricted (anyone can trigger generation). Set AUTHORIZED_CHAT_ID in .env to restrict.")

    print(f"✓ Motion Engine Mode: {'Stable Video Diffusion (SVD-XT GPU)' if USE_AI_MOTION else 'Depth Parallax (CPU)'}")
    print("-" * 60)

    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped gracefully.")

if __name__ == "__main__":
    main()
