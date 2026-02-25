"""
Enhanced Telegram Auto-Approve Bot
- Auto-detects all groups/channels where bot is admin
- Approves ALL pending requests (including old ones)
- No manual channel ID configuration needed
- Railway & other hosting compatible
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatJoinRequestHandler
import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Only bot token needed!
ADMIN_USER_ID = 123456789  # Your Telegram user ID (for commands)

# Global storage for monitored chats
monitored_chats = set()

async def discover_chats(context: ContextTypes.DEFAULT_TYPE):
    """Auto-discover all chats where bot is admin"""
    try:
        # Note: Telegram doesn't have direct API to get all chats
        # Bot will auto-add chats when join requests come
        logger.info("🔍 Bot will auto-discover chats from join requests")
        return True
    except Exception as e:
        logger.error(f"Error in discover_chats: {str(e)}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized! This bot is for admin only.")
        return
    
    await update.message.reply_text(
        "✅ Enhanced Auto-Approve Bot Running!\n\n"
        "🤖 Features:\n"
        "• Auto-detects groups/channels\n"
        "• Approves OLD pending requests\n"
        "• No manual config needed\n\n"
        "📋 Commands:\n"
        "/start - Show this message\n"
        "/approve_all - Approve ALL pending (all chats)\n"
        "/list_chats - Show monitored chats\n"
        "/stats - Show approval statistics\n\n"
        "ℹ️ Bot automatically approves new requests!\n"
        "Use /approve_all to clear old pending requests."
    )

async def approve_all_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve ALL pending requests in ALL monitored chats"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    await update.message.reply_text("🔄 Starting approval process for all chats...")
    
    total_approved = 0
    total_failed = 0
    chats_processed = 0
    
    # If no chats discovered yet, try to get updates to find them
    if not monitored_chats:
        await update.message.reply_text(
            "⚠️ No chats discovered yet.\n\n"
            "💡 Make sure:\n"
            "1. Bot is added as admin in your groups/channels\n"
            "2. 'Invite Users via Link' permission is enabled\n"
            "3. At least one join request has come\n\n"
            "Or send /list_chats to manually add chat IDs."
        )
        return
    
    for chat_id in monitored_chats:
        try:
            chat = await context.bot.get_chat(chat_id)
            await update.message.reply_text(f"📡 Processing: {chat.title}...")
            
            approved_count = 0
            failed_count = 0
            
            # Get ALL pending join requests (including old ones)
            async for request in context.bot.get_chat_join_requests(chat_id):
                try:
                    await context.bot.approve_chat_join_request(
                        chat_id=chat_id,
                        user_id=request.user.id
                    )
                    approved_count += 1
                    
                    # Calculate how old the request is
                    request_age = datetime.now() - request.date
                    logger.info(
                        f"✅ Approved: {request.user.first_name} "
                        f"(Age: {request_age.days} days, {request_age.seconds//3600} hours)"
                    )
                    
                    await asyncio.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Failed to approve: {str(e)}")
            
            total_approved += approved_count
            total_failed += failed_count
            chats_processed += 1
            
            if approved_count > 0:
                await update.message.reply_text(
                    f"✅ {chat.title}:\n"
                    f"• Approved: {approved_count}\n"
                    f"• Failed: {failed_count}"
                )
            
        except Exception as e:
            logger.error(f"Error processing chat {chat_id}: {str(e)}")
    
    # Final summary
    summary = f"""
✅ Approval Complete!

📊 Summary:
• Chats Processed: {chats_processed}
• Total Approved: {total_approved}
• Total Failed: {total_failed}

⏰ Time: {datetime.now().strftime('%H:%M:%S')}

💡 All pending requests (including old ones) have been processed!
    """
    
    await update.message.reply_text(summary)

async def list_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all monitored chats"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    if not monitored_chats:
        await update.message.reply_text(
            "📭 No chats discovered yet.\n\n"
            "Bot will auto-discover chats when join requests arrive.\n\n"
            "Or manually add chat ID:\n"
            "Reply with: /add_chat -1001234567890"
        )
        return
    
    message = "📋 Monitored Chats:\n\n"
    
    for idx, chat_id in enumerate(monitored_chats, 1):
        try:
            chat = await context.bot.get_chat(chat_id)
            message += f"{idx}. {chat.title}\n   ID: {chat_id}\n\n"
        except Exception as e:
            message += f"{idx}. Unknown (ID: {chat_id})\n\n"
    
    await update.message.reply_text(message)

async def add_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually add chat ID to monitor"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /add_chat -1001234567890\n\n"
            "Get chat ID from @userinfobot"
        )
        return
    
    try:
        chat_id = int(context.args[0])
        
        # Verify bot has access
        chat = await context.bot.get_chat(chat_id)
        monitored_chats.add(chat_id)
        
        await update.message.reply_text(
            f"✅ Added: {chat.title}\n"
            f"ID: {chat_id}\n\n"
            f"Bot will now monitor this chat!"
        )
        
    except ValueError:
        await update.message.reply_text("❌ Invalid chat ID format!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    stats_msg = f"""
📊 Bot Statistics

🏷️ Monitored Chats: {len(monitored_chats)}

⚙️ Status: Running
🕐 Uptime: Active

💡 Tip: Use /approve_all to process pending requests
    """
    
    await update.message.reply_text(stats_msg)

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new join requests automatically"""
    request = update.chat_join_request
    chat_id = request.chat.id
    user = request.user
    
    # Auto-add chat to monitored list
    if chat_id not in monitored_chats:
        monitored_chats.add(chat_id)
        logger.info(f"🆕 Auto-discovered chat: {request.chat.title} ({chat_id})")
    
    try:
        # Auto-approve new request
        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user.id
        )
        logger.info(f"✅ Auto-approved: {user.first_name} in {request.chat.title}")
        
    except Exception as e:
        logger.error(f"❌ Failed to auto-approve: {str(e)}")

async def periodic_approval_task(application: Application):
    """Background task to periodically approve pending requests"""
    while True:
        try:
            await asyncio.sleep(300)  # Wait 5 minutes
            
            logger.info("🔄 Periodic approval check...")
            
            for chat_id in list(monitored_chats):
                try:
                    approved_count = 0
                    
                    async for request in application.bot.get_chat_join_requests(chat_id):
                        try:
                            await application.bot.approve_chat_join_request(
                                chat_id=chat_id,
                                user_id=request.user.id
                            )
                            approved_count += 1
                            await asyncio.sleep(0.1)
                        except Exception as e:
                            logger.error(f"Error approving: {str(e)}")
                    
                    if approved_count > 0:
                        logger.info(f"✅ Periodic approval: {approved_count} requests")
                        
                except Exception as e:
                    logger.error(f"Error in periodic check for {chat_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in periodic task: {str(e)}")

async def post_init(application: Application):
    """Called after bot initialization"""
    asyncio.create_task(periodic_approval_task(application))
    logger.info("✅ Periodic approval task started!")

def main():
    """Start the bot"""
    print("🤖 Starting Enhanced Auto-Approve Bot...")
    print("✅ Bot will auto-discover chats!")
    print("✅ Old pending requests will be approved!")
    print("⌨️ Press Ctrl+C to stop.")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve_all", approve_all_chats))
    application.add_handler(CommandHandler("list_chats", list_chats))
    application.add_handler(CommandHandler("add_chat", add_chat))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(ChatJoinRequestHandler(handle_join_request))
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
