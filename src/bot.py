import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from src.config import (
    TELEGRAM_BOT_TOKEN, AUTHORIZED_CHAT_ID, PHOTOS_DIR, REELS_DIR, LOG_FILE, USE_AI_MOTION,
    REEL_DURATION_SEC, FPS
)
from src.style_randomizer import generate_reel_style, format_style_summary, generate_instagram_caption
from src.motion_engine import generate_motion
from src.text_overlay import generate_text_overlay_frames
from src.renderer import render_reel
from src.compiler import compile_30_day_recap

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Debounced Media Group (Album) Storage
MEDIA_GROUP_CACHE: Dict[str, List] = {}
MEDIA_GROUP_TASKS: Dict[str, asyncio.Task] = {}
MEDIA_GROUP_UPDATES: Dict[str, Update] = {}

def check_authorized(update: Update) -> bool:
    """Verifies if the sender is authorized to use the bot."""
    if AUTHORIZED_CHAT_ID is None:
        return True
    user_id = update.effective_chat.id
    if user_id != AUTHORIZED_CHAT_ID:
        logger.warning(f"Unauthorized access attempt by Chat ID: {user_id}")
        return False
    return True

def get_next_day_number() -> int:
    """Determines the next Day number based on existing files in data/photos/."""
    existing = list(PHOTOS_DIR.glob("Day_*"))
    max_day = 0
    for p in existing:
        try:
            stem = p.name.split(".")[0]
            day_part = stem.split("_")[1]
            day_num = int(day_part)
            if day_num > max_day:
                max_day = day_num
        except (IndexError, ValueError):
            pass
    return max_day + 1

def log_reel_metadata(day_num: int, photo_paths: List[str], reel_path: str, style_info: dict):
    """Appends upload and rendering metadata to data/log.json."""
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    log_entry = {
        "day": day_num,
        "timestamp": datetime.now().isoformat(),
        "photo_files": photo_paths,
        "reel_file": reel_path,
        "style": style_info
    }
    logs.append(log_entry)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command."""
    if not check_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user. Access denied.")
        return

    chat_id = update.effective_chat.id
    msg = (
        "🌅 **Welcome to Vadodara Sky Challenge Bot!**\n\n"
        "Send me single or **multiple sky photos (Album)**, and I will automatically "
        "generate a **15-second HD Motion Graphic Reel** + **Ready-to-Copy Instagram Caption**!\n\n"
        f"• **Your Chat ID**: `{chat_id}`\n"
        f"• **Reel Duration**: `{REEL_DURATION_SEC} seconds` (30 FPS HD)\n\n"
        "Commands:\n"
        "• Upload single or multiple photos to render today's reel\n"
        "• `/status` — View challenge progress\n"
        "• `/compile` — Generate 30-day recap video"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /status command."""
    if not check_authorized(update):
        return

    next_day = get_next_day_number()
    completed = next_day - 1
    msg = (
        f"📊 **Vadodara Sky Challenge Status**\n\n"
        f"• **Completed Days**: {completed}/30\n"
        f"• **Next Day**: Day {next_day:02d}\n"
        f"• **Reel Duration**: {REEL_DURATION_SEC} seconds (30 FPS HD)"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def process_photos_pipeline(update: Update, photo_items: List, day_num: int):
    """Executes the advanced 15-second motion graphic reel pipeline for single or multiple photos."""
    photo_paths = []

    if len(photo_items) == 1:
        photo_filename = f"Day_{day_num:02d}.jpg"
        photo_path = PHOTOS_DIR / photo_filename
        photo_file = await photo_items[0].get_file()
        await photo_file.download_to_drive(str(photo_path))
        photo_paths.append(str(photo_path))
    else:
        for idx, item in enumerate(photo_items):
            photo_filename = f"Day_{day_num:02d}_{idx+1}.jpg"
            photo_path = PHOTOS_DIR / photo_filename
            photo_file = await item.get_file()
            await photo_file.download_to_drive(str(photo_path))
            photo_paths.append(str(photo_path))

    reel_filename = f"Day_{day_num:02d}_reel.mp4"
    reel_path = REELS_DIR / reel_filename

    status_msg = await update.message.reply_text(
        f"📸 **Received {len(photo_paths)} sky photo(s)** for Day {day_num:02d}!\n"
        f"⏳ Generating **15-Second HD Motion Graphic Reel**... Please wait.",
        parse_mode="Markdown"
    )

    try:
        # 1. Style Selection
        style = generate_reel_style(day_num)

        # 2. Motion Generation (Single or Multi-Photo over 15s @ 30 FPS)
        raw_frames, mode_used = generate_motion(
            image_paths=photo_paths,
            motion_style=style["motion_style"],
            duration_sec=15.0,
            fps=FPS
        )

        # 3. 15-Second Motion Graphic Text & Progress Bar Overlay
        text_frames = generate_text_overlay_frames(
            day_number=day_num,
            text_animation=style["text_animation"],
            num_frames=len(raw_frames)
        )

        # 4. Composite & Render 15-Second HD Reel
        render_reel(
            raw_frames=raw_frames,
            text_overlay_frames=text_frames,
            style=style,
            output_path=reel_path,
            fps=FPS
        )

        # 5. Log Metadata
        log_reel_metadata(day_num, photo_paths, str(reel_path), style)

        # 6. Upload 15-second Reel back to user
        photo_count_str = f"{len(photo_paths)} Photos Album" if len(photo_paths) > 1 else "1 Photo"
        video_caption = format_style_summary(style, mode_used) + f"\n📸 **Source**: `{photo_count_str}`\n⏱ **Duration**: `15.0 sec (30 FPS)`"
        
        with open(reel_path, "rb") as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=video_caption,
                parse_mode="Markdown"
            )

        # 7. Generate & Send Ready-to-Copy Instagram Caption Message
        ig_caption = generate_instagram_caption(day_num, style, photo_count=len(photo_paths))
        copy_msg = (
            f"📋 **Copy Caption for Instagram Post (Day {day_num:02d}):**\n\n"
            f"```\n{ig_caption}\n```"
        )
        await update.message.reply_text(copy_msg, parse_mode="Markdown")

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error generating 15s reel: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Error generating reel: `{e}`", parse_mode="Markdown")

async def _finalize_media_group_after_delay(media_group_id: str):
    """Waits for all photos in an album to arrive before triggering pipeline."""
    try:
        await asyncio.sleep(2.0)
        items = MEDIA_GROUP_CACHE.pop(media_group_id, [])
        update = MEDIA_GROUP_UPDATES.pop(media_group_id, None)
        MEDIA_GROUP_TASKS.pop(media_group_id, None)

        if items and update:
            day_num = get_next_day_number()
            await process_photos_pipeline(update, items, day_num)
    except Exception as e:
        logger.error(f"Error in finalize media group: {e}", exc_info=True)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles single photo and multi-photo album uploads."""
    if not check_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user.")
        return

    photos = update.message.photo
    if not photos:
        return

    media_group_id = update.message.media_group_id
    highest_res_photo = photos[-1]

    if media_group_id:
        if media_group_id not in MEDIA_GROUP_CACHE:
            MEDIA_GROUP_CACHE[media_group_id] = []
            MEDIA_GROUP_UPDATES[media_group_id] = update

        MEDIA_GROUP_CACHE[media_group_id].append(highest_res_photo)

        if media_group_id in MEDIA_GROUP_TASKS:
            MEDIA_GROUP_TASKS[media_group_id].cancel()

        task = asyncio.create_task(_finalize_media_group_after_delay(media_group_id))
        MEDIA_GROUP_TASKS[media_group_id] = task

    else:
        day_num = get_next_day_number()
        await process_photos_pipeline(update, [highest_res_photo], day_num)

async def compile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /compile command."""
    if not check_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user.")
        return

    status_msg = await update.message.reply_text("🎬 Compiling 30-Day recap reel... Please wait.")

    try:
        recap_path = compile_30_day_recap()

        with open(recap_path, "rb") as recap_video:
            await update.message.reply_video(
                video=recap_video,
                caption="🎉 **Vadodara Sky Challenge — 30-Day Recap Reel Completed!**",
                parse_mode="Markdown"
            )
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Compilation error: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Compilation failed: `{e}`", parse_mode="Markdown")

async def handle_health_check(reader, writer):
    """HTTP Health check handler for Render Free Web Service."""
    response_body = "Vadodara Sky Challenge Bot is Live & Healthy!"
    response = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: text/plain\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        f"Connection: close\r\n\r\n"
        f"{response_body}"
    )
    writer.write(response.encode('utf-8'))
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def main_async():
    """Runs Telegram Bot polling + Render HTTP Health Check Web Server concurrently."""
    if not TELEGRAM_BOT_TOKEN:
        print("[Error] TELEGRAM_BOT_TOKEN is not set in .env! Please configure your token.")
        return

    port = int(os.getenv("PORT", 10000))
    print(f"🌐 Starting HTTP Health Check Web Server on 0.0.0.0:{port} for Render Web Service...")
    health_server = await asyncio.start_server(handle_health_check, '0.0.0.0', port)

    print("🤖 Starting Vadodara Sky Challenge Telegram Bot...")
    
    # Configure robust HTTP request timeouts to prevent connection timeouts on local networks
    request_config = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(request_config).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", start_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("compile", compile_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    print("✓ Vadodara Sky Bot & Web Server successfully started!")
    await asyncio.Event().wait()

def run_bot():
    """Entry point for running the bot and health server in event loop."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped gracefully.")
