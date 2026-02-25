"""
🤖 Telegram Pending Request Auto-Approve Bot (Deployment Ready)
================================================================
Yeh version hosting platforms ke liye ready hai.
Token environment variable se read hota hai.
"""

import os
import asyncio
import logging
from telegram import Update, Bot
from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    CommandHandler,
    ContextTypes,
)

# ========================== SETTINGS ==========================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable set nahi hai!")
# ==============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

stats = {"approved": 0}


async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Naye join requests auto approve"""
    join_request = update.chat_join_request
    user = join_request.from_user
    chat = join_request.chat
    try:
        await join_request.approve()
        stats["approved"] += 1
        logger.info(f"✅ APPROVED: {user.full_name} (ID: {user.id}) -> {chat.title}")
    except Exception as e:
        logger.error(f"❌ Error approving {user.full_name}: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Pending Request Approve Bot*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Join requests *automatically* approve hoti hain!\n\n"
        "📋 *Commands:*\n"
        "/start - Bot info\n"
        "/stats - Kitni requests approve hui\n\n"
        "⚙️ Bot ko channel mein admin banao with 'Add Members' permission.",
        parse_mode="Markdown",
    )


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 *Bot Stats*\n✅ Approved: {stats['approved']}",
        parse_mode="Markdown",
    )


def main():
    print("🤖 Telegram Approve Bot Starting...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    print("✅ Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
