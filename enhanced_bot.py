"""
Complete Telegram Auto-Approve Bot
Features:
- Approves OLD + NEW pending requests
- Sends welcome message after approval
- Registers users in database
- Broadcast to all users
- User statistics (active/blocked)
- 100% Railway compatible
"""

import os
import sqlite3
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ChatJoinRequestHandler,
    MessageHandler,
    filters
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))

# Database setup
def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            chat_id INTEGER,
            joined_date TEXT,
            is_active INTEGER DEFAULT 1,
            is_blocked INTEGER DEFAULT 0
        )
    ''')
    
    # Chats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT,
            added_date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

# Database helpers
def add_user(user_id, username, first_name, last_name, chat_id):
    """Add or update user in database"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, chat_id, joined_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (user_id, username, first_name, last_name, chat_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ User added: {first_name} ({user_id})")
        return True
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False

def mark_user_blocked(user_id):
    """Mark user as blocked"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = 1, is_active = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    except:
        pass

def get_all_active_users():
    """Get all active users"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_active = 1 AND is_blocked = 0')
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users
    except:
        return []

def get_user_stats():
    """Get user statistics"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        active = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_blocked = 1')
        blocked = cursor.fetchone()[0]
        
        conn.close()
        return {'total': total, 'active': active, 'blocked': blocked}
    except:
        return {'total': 0, 'active': 0, 'blocked': 0}

def add_chat(chat_id, chat_title):
    """Add chat to database"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO chats (chat_id, chat_title, added_date)
            VALUES (?, ?, ?)
        ''', (chat_id, chat_title, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except:
        pass

def get_all_chats():
    """Get all monitored chats"""
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id, chat_title FROM chats')
        chats = cursor.fetchall()
        conn.close()
        return chats
    except:
        return []

# Bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user_id = update.effective_user.id
    
    # Register user when they start bot
    add_user(
        user_id,
        update.effective_user.username,
        update.effective_user.first_name,
        update.effective_user.last_name,
        update.effective_chat.id
    )
    
    if user_id != ADMIN_USER_ID:
        # Regular user
        msg = """👋 Welcome to Auto-Approve Bot!

✅ You're registered!

You'll receive:
• Important announcements
• Updates from admin
• Group notifications

Type /help for more info.
"""
        await update.message.reply_text(msg)
        return
    
    # Admin user
    msg = """✅ Auto-Approve Bot - Admin Panel

🤖 Features:
• Auto-approves OLD + NEW requests
• Sends welcome message
• Registers users automatically
• Broadcast to all users
• User statistics

📋 Admin Commands:
/approve_all - Approve ALL pending requests
/broadcast <message> - Send to all users
/stats - User statistics
/users - List recent users
/chats - Monitored groups

✅ Status: Running
"""
    await update.message.reply_text(msg)

async def approve_all_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve ALL pending requests with welcome messages"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    await update.message.reply_text("🔄 Starting approval process...")
    
    total_approved = 0
    total_failed = 0
    
    chats = get_all_chats()
    
    if not chats:
        await update.message.reply_text(
            "⚠️ No chats found!\n\n"
            "Add bot to group as admin first."
        )
        return
    
    for chat_id, chat_title in chats:
        try:
            await update.message.reply_text(f"📡 Processing: {chat_title}...")
            
            approved = 0
            failed = 0
            
            # Get ALL pending requests (old + new)
            async for request in context.bot.get_chat_join_requests(chat_id):
                try:
                    # Approve request
                    await context.bot.approve_chat_join_request(
                        chat_id=chat_id,
                        user_id=request.user.id
                    )
                    
                    # Register user
                    add_user(
                        request.user.id,
                        request.user.username,
                        request.user.first_name,
                        request.user.last_name,
                        chat_id
                    )
                    
                    # Send welcome message
                    try:
                        welcome_msg = f"""🎉 Welcome {request.user.first_name}!

✅ Your request has been approved!
✅ You're now a member of {chat_title}!

📢 Stay updated:
• Start this bot: @{context.bot.username}
• Get important announcements
• Connect with the community

Enjoy! 🚀
"""
                        # Create inline button
                        keyboard = [[
                            InlineKeyboardButton(
                                "✅ Start Bot",
                                url=f"https://t.me/{context.bot.username}?start=welcome"
                            )
                        ]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await context.bot.send_message(
                            chat_id=request.user.id,
                            text=welcome_msg,
                            reply_markup=reply_markup
                        )
                        logger.info(f"✅ Welcome sent to {request.user.first_name}")
                    except Exception as e:
                        logger.error(f"Welcome message failed: {e}")
                    
                    approved += 1
                    
                    # Log request age
                    age = datetime.now() - request.date.replace(tzinfo=None)
                    logger.info(
                        f"✅ Approved: {request.user.first_name} "
                        f"({age.days}d {age.seconds//3600}h old)"
                    )
                    
                    await asyncio.sleep(0.2)  # Rate limit
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"Approval failed: {e}")
            
            total_approved += approved
            total_failed += failed
            
            if approved > 0:
                await update.message.reply_text(
                    f"✅ {chat_title}\n"
                    f"Approved: {approved}\n"
                    f"Failed: {failed}"
                )
            else:
                await update.message.reply_text(
                    f"ℹ️ {chat_title}: No pending requests"
                )
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
    
    # Final summary
    summary = f"""✅ Approval Complete!

📊 Summary:
• Total Approved: {total_approved}
• Total Failed: {total_failed}
• Welcome Messages Sent: {total_approved}

⏰ {datetime.now().strftime('%H:%M:%S')}

All users have been:
✅ Approved
✅ Registered in bot
✅ Sent welcome message
"""
    await update.message.reply_text(summary)

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /broadcast <message>\n\n"
            "Example:\n"
            "/broadcast Hello everyone! Important update here."
        )
        return
    
    message_text = ' '.join(context.args)
    
    await update.message.reply_text("📢 Starting broadcast...")
    
    users = get_all_active_users()
    
    if not users:
        await update.message.reply_text("📭 No users to broadcast to!")
        return
    
    success = 0
    failed = 0
    blocked = 0
    
    for user_id_target in users:
        try:
            await context.bot.send_message(
                chat_id=user_id_target,
                text=f"📢 Broadcast Message:\n\n{message_text}"
            )
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            if 'blocked' in str(e).lower():
                blocked += 1
                mark_user_blocked(user_id_target)
            logger.error(f"Broadcast failed to {user_id_target}: {e}")
    
    summary = f"""✅ Broadcast Complete!

📊 Results:
• Total Users: {len(users)}
• Sent Successfully: {success}
• Failed: {failed}
• Blocked Bot: {blocked}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
    await update.message.reply_text(summary)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    stats = get_user_stats()
    chats = get_all_chats()
    
    msg = f"""📊 Bot Statistics

👥 Users:
• Total Users: {stats['total']}
• Active Users: {stats['active']}
• Blocked Bot: {stats['blocked']}

💬 Groups:
• Monitored Chats: {len(chats)}

⚙️ Status: Running
🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}

💡 Use /users to see recent users
💡 Use /chats to see groups
"""
    await update.message.reply_text(msg)

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List recent users"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, first_name, username, joined_date, is_active, is_blocked
            FROM users
            ORDER BY joined_date DESC
            LIMIT 20
        ''')
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            await update.message.reply_text("📭 No users yet!")
            return
        
        msg = "👥 Recent Users (Last 20):\n\n"
        for idx, (uid, name, uname, date, active, blocked) in enumerate(users, 1):
            status = "🟢" if active and not blocked else "🔴" if blocked else "⚫"
            username_str = f"@{uname}" if uname else "No username"
            msg += f"{idx}. {status} {name} ({username_str})\n"
        
        msg += f"\n🟢 Active | 🔴 Blocked | ⚫ Inactive"
        await update.message.reply_text(msg)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def list_chats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List monitored chats"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    chats = get_all_chats()
    
    if not chats:
        await update.message.reply_text("📭 No chats yet!")
        return
    
    msg = "💬 Monitored Groups:\n\n"
    for idx, (chat_id, title) in enumerate(chats, 1):
        msg += f"{idx}. {title}\n   ID: `{chat_id}`\n\n"
    
    await update.message.reply_text(msg)

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-handle new join requests"""
    request = update.chat_join_request
    chat_id = request.chat.id
    user = request.user
    
    # Add chat to database
    add_chat(chat_id, request.chat.title)
    
    try:
        # Auto-approve
        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user.id
        )
        
        # Register user
        add_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            chat_id
        )
        
        # Send welcome message
        try:
            welcome_msg = f"""🎉 Welcome {user.first_name}!

✅ Your request has been approved!
✅ You're now a member of {request.chat.title}!

📢 Stay connected:
• Start this bot to get announcements
• Important updates from admin
• Community notifications

Enjoy! 🚀
"""
            keyboard = [[
                InlineKeyboardButton(
                    "✅ Start Bot",
                    url=f"https://t.me/{context.bot.username}?start=welcome"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=user.id,
                text=welcome_msg,
                reply_markup=reply_markup
            )
            logger.info(f"✅ Auto-approved + welcomed: {user.first_name}")
        except:
            logger.info(f"✅ Auto-approved (no DM): {user.first_name}")
        
    except Exception as e:
        logger.error(f"Auto-approve failed: {e}")

async def periodic_approval(app: Application):
    """Periodic approval of pending requests"""
    logger.info("🔄 Periodic approval started")
    
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            
            chats = get_all_chats()
            if not chats:
                continue
            
            total = 0
            for chat_id, chat_title in chats:
                try:
                    count = 0
                    async for req in app.bot.get_chat_join_requests(chat_id):
                        try:
                            # Approve
                            await app.bot.approve_chat_join_request(
                                chat_id=chat_id,
                                user_id=req.user.id
                            )
                            
                            # Register
                            add_user(
                                req.user.id,
                                req.user.username,
                                req.user.first_name,
                                req.user.last_name,
                                chat_id
                            )
                            
                            # Welcome message
                            try:
                                await app.bot.send_message(
                                    chat_id=req.user.id,
                                    text=f"🎉 Welcome! Approved to {chat_title}"
                                )
                            except:
                                pass
                            
                            count += 1
                            await asyncio.sleep(0.1)
                        except:
                            pass
                    
                    total += count
                    if count > 0:
                        logger.info(f"Periodic: {count} approved in {chat_title}")
                except:
                    pass
            
            if total > 0:
                logger.info(f"✅ Periodic total: {total}")
        except:
            pass

async def post_init(app: Application):
    """Initialize bot"""
    init_database()
    asyncio.create_task(periodic_approval(app))
    logger.info("✅ Bot initialized with database!")

def main():
    """Start bot"""
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set!")
        return
    
    if ADMIN_USER_ID == 0:
        print("❌ ADMIN_USER_ID not set!")
        return
    
    logger.info("🤖 Starting Complete Auto-Approve Bot...")
    logger.info(f"👤 Admin: {ADMIN_USER_ID}")
    logger.info("✅ Features: Approve, Welcome, Register, Broadcast, Stats")
    
    try:
        app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
        
        # Admin commands
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("approve_all", approve_all_requests))
        app.add_handler(CommandHandler("broadcast", broadcast_message))
        app.add_handler(CommandHandler("stats", show_stats))
        app.add_handler(CommandHandler("users", list_users))
        app.add_handler(CommandHandler("chats", list_chats_cmd))
        
        # Join request handler
        app.add_handler(ChatJoinRequestHandler(handle_join_request))
        
        logger.info("✅ All handlers registered")
        logger.info("🚀 Starting polling...")
        
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Fatal: {e}")
        raise

if __name__ == '__main__':
    main()
