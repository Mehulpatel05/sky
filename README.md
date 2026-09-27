# 🌅 Vadodara Sky Challenge — Automated Reel Generation System

An automated, **100% free, fully local & cloud-ready** system that takes sky photos sent to a Telegram bot and generates vertical 1080x1920 15-second AI Motion-Graphic Instagram Reels with randomized style combinations.

---

## 🌟 System Features

- **Input**: Single or multiple sky photos (Album upload) sent to Telegram Bot
- **Output**: Vertical 1080x1920 `.mp4` Instagram Reel (30 FPS, HD Glassmorphism motion graphics, 15 seconds)
- **Multi-Photo Album Support**: Upload 1 photo or an album of 2-5 photos — the bot automatically creates a 15-second multi-photo reel with crossfade transitions!
- **Glassmorphism Typography**: Translucent lower-third graphics card with dynamic progress bar (`Day N/30`).
- **Cost**: **₹0 / $0** (runs locally or on free cloud hosts like Render.com)
- **Variety**: Randomized Style Engine ensures no two consecutive reels look the same by tracking recent history.
- **Recap Compilation**: `/compile` command stitches all 30 days into one recap reel with intro/outro cards.

---

## 📁 Repository Structure

```
sky/
├── data/
│   ├── photos/            # Uploaded sky photos (Day_01.jpg, Day_02.jpg, ...)
│   ├── reels/             # Rendered reels (Day_01_reel.mp4, Day_02_reel.mp4, ...)
│   ├── log.json           # Day tracking & upload metadata
│   └── style_history.json # Style Engine history
├── models/                # Downloaded AI model weights (MiDaS, DepthAnything)
├── assets/
│   ├── fonts/             # Poppins-Bold Google Font
│   ├── audio/             # Background ambient music tracks (.mp3)
│   ├── overlays/          # Light leak textures & optical flares
│   └── particles/         # Bokeh particle datasets
├── src/
│   ├── config.py          # Centralized configuration & environment loader
│   ├── asset_builder.py   # Motion graphic asset dataset builder
│   ├── depth_parallax.py  # 2.5D Depth-based Parallax motion generator (DepthAnything + OpenCV)
│   ├── ai_motion.py       # Stable Video Diffusion (SVD-XT) AI pipeline (diffusers)
│   ├── motion_engine.py   # Unified motion engine with automatic SVD -> Parallax fallback
│   ├── style_randomizer.py# Randomized style engine with history tracking
│   ├── text_overlay.py    # Glassmorphism motion graphic typography & progress bar generator
│   ├── renderer.py        # FFmpeg video composition & encoding (30 FPS, CRF 16)
│   ├── compiler.py        # 30-Day Recap compilation engine with transitions
│   └── bot.py             # Telegram bot command handlers & photo listener
├── .env.example           # Configuration template
├── Dockerfile             # Render container spec (Python 3.10 + FFmpeg)
├── render.yaml            # Render Blueprint spec
├── main.py                # Bot application entry point
├── requirements.txt       # Python dependencies
└── README.md              # Installation & setup instructions
```

---

## ☁️ Deployment to Render.com (24/7 Hosting)

1. **Push Code to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy Vadodara Sky Bot to Render"
   git remote add origin https://github.com/Mehulpatel05/sky.git
   git branch -M main
   git push -u origin main
   ```

2. **Deploy on Render**:
   - Go to [Render Dashboard](https://dashboard.render.com).
   - Click **New +** -> **Background Worker**.
   - Connect your GitHub repository `Mehulpatel05/sky`.
   - Select **Docker** environment (it will automatically use the bundled `Dockerfile` containing FFmpeg).
   - Add Environment Variables:
     - `TELEGRAM_BOT_TOKEN` = `your_telegram_bot_token`
     - `AUTHORIZED_CHAT_ID` = `your_chat_id`
     - `USE_AI_MOTION` = `False` (for CPU Render free tier)
     - `REEL_DURATION_SEC` = `15.0`
     - `FPS` = `30`
   - Click **Create Background Worker**. Render will build the container and run your bot 24/7!

---

## 🚀 Local Setup Guide (Windows)

```powershell
# Navigate to project directory
cd c:\Users\swatm\Downloads\sky

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install required Python packages
pip install -r requirements.txt

# Run main bot
python main.py
```
