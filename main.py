import os
import asyncio
import logging
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

# ================= Configuration =================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")

TOTAL_SENDS = 10
INTERVAL_SECONDS = 120 / TOTAL_SENDS  # 12s between each send
# =================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ---------- Command handlers (so the bot replies to you) ----------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot is alive.\n"
        f"Target channel: {CHANNEL_ID}\n"
        f"Schedule: {TOTAL_SENDS} messages every 2 minutes.\n"
        "Commands: /status /test"
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"✅ Running.\nLast check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a single test message to the channel right now."""
    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"🧪 Test message at {datetime.now().strftime('%H:%M:%S')}"
        )
        await update.message.reply_text("✅ Test message sent to channel.")
    except TelegramError as e:
        await update.message.reply_text(f"❌ Failed: {e}")


# ---------- Scheduled reporting job ----------

async def send_channel_report(context: ContextTypes.DEFAULT_TYPE):
    """Send 10 messages, one every 12 seconds."""
    for i in range(TOTAL_SENDS):
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"📢 Report {i+1}/{TOTAL_SENDS}\n"
                     f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            logger.info(f"Sent {i+1}/{TOTAL_SENDS}")
        except TelegramError as e:
            logger.error(f"Send failed: {e}")
        if i < TOTAL_SENDS - 1:
            await asyncio.sleep(INTERVAL_SECONDS)


# ---------- Main ----------

def main():
    if not TOKEN or not CHANNEL_ID:
        logger.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID")
        return

    app = Application.builder().token(TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("test", test_cmd))

    # Schedule the report every 120 seconds
    app.job_queue.run_repeating(
        send_channel_report,
        interval=120,
        first=10  # first run 10s after startup
    )

    logger.info("Bot started. Polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
