import os
import logging
from datetime import datetime, timezone

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Add BOT_TOKEN in Railway Variables."
    )


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# TEMPORARY REPORT STORAGE
# ============================================================

reports = []


# ============================================================
# /START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📝 Submit Report",
                callback_data="submit_report",
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ About",
                callback_data="about",
            ),
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help",
            ),
        ],
    ]

    await update.message.reply_text(
        "👋 Welcome to Telegram Report Assistant\n\n"
        "This bot helps you prepare a legitimate report "
        "about a Telegram channel or message.\n\n"
        "Choose an option below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================
# BUTTON HANDLER
# ============================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    await query.answer()

    # --------------------------------------------------------
    # SUBMIT REPORT
    # --------------------------------------------------------

    if query.data == "submit_report":

        context.user_data.clear()

        context.user_data["waiting_for_link"] = True

        await query.edit_message_text(
            "📝 Submit a Report\n\n"
            "Send the Telegram channel or message link "
            "you want to report.\n\n"
            "Example:\n"
            "https://t.me/example/123"
        )

    # --------------------------------------------------------
    # ABOUT
    # --------------------------------------------------------

    elif query.data == "about":

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back_start",
                )
            ]
        ]

        await query.edit_message_text(
            "ℹ️ About This Bot\n\n"
            "This bot helps users organize legitimate "
            "Telegram report requests.\n\n"
            "You can provide a Telegram link, select the "
            "appropriate reason, and describe the issue.\n\n"
            "The bot does NOT send repeated or automated "
            "mass reports."
            ,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    elif query.data == "help":

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back_start",
                )
            ]
        ]

        await query.edit_message_text(
            "❓ How To Use\n\n"
            "1️⃣ Press Submit Report.\n\n"
            "2️⃣ Send the Telegram channel or message link.\n\n"
            "3️⃣ Select the reason.\n\n"
            "4️⃣ Explain the problem.\n\n"
            "5️⃣ Your report request will be recorded.\n\n"
            "Use accurate information when making a report.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    elif query.data == "back_start":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Submit Report",
                    callback_data="submit_report",
                )
            ],
            [
                InlineKeyboardButton(
                    "ℹ️ About",
                    callback_data="about",
                ),
                InlineKeyboardButton(
                    "❓ Help",
                    callback_data="help",
                ),
            ],
        ]

        await query.edit_message_text(
            "👋 Welcome to Telegram Report Assistant\n\n"
            "Choose an option below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ============================================================
# RECEIVE TELEGRAM LINK
# ============================================================

async def receive_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not context.user_data.get("waiting_for_link"):
        return

    if not update.message or not update.message.text:
        return

    link = update.message.text.strip()

    # Basic Telegram link validation
    valid_link = (
        link.startswith("https://t.me/")
        or link.startswith("http://t.me/")
        or link.startswith("t.me/")
        or link.startswith("https://telegram.me/")
        or link.startswith("http://telegram.me/")
    )

    if not valid_link:

        await update.message.reply_text(
            "❌ Invalid Telegram link.\n\n"
            "Please send a Telegram channel or message link.\n\n"
            "Example:\n"
            "https://t.me/example/123"
        )

        return

    context.user_data["report_link"] = link
    context.user_data["waiting_for_link"] = False

    keyboard = [
        [
            InlineKeyboardButton(
                "🚫 Spam / Scam",
                callback_data="reason_spam",
            )
        ],
        [
            InlineKeyboardButton(
                "⚠️ Illegal Content",
                callback_data="reason_illegal",
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Impersonation",
                callback_data="reason_impersonation",
            )
        ],
        [
            InlineKeyboardButton(
                "📌 Other",
                callback_data="reason_other",
            )
        ],
    ]

    await update.message.reply_text(
        "✅ Telegram link received.\n\n"
        "Now select the reason that best describes "
        "the problem:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================
# REASON HANDLER
# ============================================================

async def reason_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    await query.answer()

    reasons = {
        "reason_spam": "Spam / Scam",
        "reason_illegal": "Illegal Content",
        "reason_impersonation": "Impersonation",
        "reason_other": "Other",
    }

    reason = reasons.get(
        query.data,
        "Other",
    )

    context.user_data["reason"] = reason
    context.user_data["waiting_for_description"] = True

    await query.edit_message_text(
        f"📌 Reason: {reason}\n\n"
        "Now send a short explanation of the problem.\n\n"
        "Please provide accurate information."
    )


# ============================================================
# RECEIVE DESCRIPTION
# ============================================================

async def receive_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not context.user_data.get("waiting_for_description"):
        return

    if not update.message or not update.message.text:
        return

    description = update.message.text.strip()

    if len(description) < 5:

        await update.message.reply_text(
            "❌ Please provide more information.\n\n"
            "Your explanation should be at least a few words."
        )

        return

    link = context.user_data.get(
        "report_link",
        "Unknown",
    )

    reason = context.user_data.get(
        "reason",
        "Other",
    )

    user = update.effective_user

    # Create report record
    report = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "link": link,
        "reason": reason,
        "description": description,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    reports.append(report)

    # Clear temporary conversation data
    context.user_data.clear()

    await update.message.reply_text(
        "✅ Report Request Recorded\n\n"
        f"🔗 Link:\n{link}\n\n"
        f"📌 Reason:\n{reason}\n\n"
        f"📝 Description:\n{description}\n\n"
        "The request has been recorded. "
        "For an actual report, use Telegram's official "
        "reporting functionality."
    )


# ============================================================
# /STATS
# ============================================================

async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        "📊 Bot Statistics\n\n"
        f"Report requests recorded: {len(reports)}"
    )


# ============================================================
# /CANCEL
# ============================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Current report cancelled.\n\n"
        "Use /start to begin again."
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.error(
        "Telegram bot error:",
        exc_info=context.error,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info("Starting Telegram Report Assistant...")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "stats",
            stats,
        )
    )

    application.add_handler(
        CommandHandler(
            "cancel",
            cancel,
        )
    )

    # Main menu buttons
    application.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern="^(submit_report|about|help|back_start)$",
        )
    )

    # Reason buttons
    application.add_handler(
        CallbackQueryHandler(
            reason_handler,
            pattern="^reason_",
        )
    )

    # Text messages
    #
    # The link handler only acts when the user is waiting
    # for a Telegram link.
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_link,
        ),
        group=0,
    )

    # Description handler only acts after a reason is selected.
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_description,
        ),
        group=1,
    )

    application.add_error_handler(
        error_handler
    )

    logger.info("Bot is running.")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    main()
