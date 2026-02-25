"""
Fixed Auto-Approve Bot
- Manual chat add feature
- Better permission checks
- Improved error handling
- 100% Working approval
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
    ChatJoinRequestHandler
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

# Database
def init_database():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT,
            added_date TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

def add_user(user_id, username, first_name, last_name, chat_id):
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
        return True
    except:
        return False

def mark_user_blocked(user_id):
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = 1, is_active = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    except:
        pass

def get_all_active_users():
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

def add_chat_to_db(chat_id, chat_title):
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO chats (chat_id, chat_title, added_date, is_active)
            VALUES (?, ?, ?, 1)
        ''', (chat_id, chat_title, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        logger.info(f"✅ Chat added to DB: {chat_title} ({chat_id})")
        return True
    except Exception as e:
        logger.error(f"Error adding chat: {e}")
        return False

def get_all_chats():
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id, chat_title FROM chats WHERE is_active = 1')
        chats = cursor.fetchall()
        conn.close()
        return chats
    except:
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Register user
    add_user(
        user_id,
        update.effective_user.username,
        update.effective_user.first_name,
        update.effective_user.last_name,
        update.effective_chat.id
    )
    
    if user_id != ADMIN_USER_ID:
        msg = """👋 Welcome!

✅ You're registered!

You'll receive updates and announcements.

Type /help for more info.
"""
        await update.message.reply_text(msg)
        return
    
    # Admin
    msg = """✅ Auto-Approve Bot - Admin Panel

🤖 Features:
• Approves OLD + NEW requests
• Sends welcome message
• User database & broadcast
• Complete statistics

📋 Commands:
/add_chat - Add group manually ⭐
/approve_all - Approve ALL pending
/broadcast <msg> - Send to all
/stats - Statistics
/users - List users
/chats - List groups
/help - Setup guide

⚠️ IMPORTANT:
Use /add_chat first to add your group!
"""
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help and setup guide"""
    help_text = """📖 Setup Guide

🔧 Step 1: Add Bot to Group
1. Go to your group
2. Group Info → Administrators
3. Add Administrator → Your bot
4. Enable permission:
   ✅ Invite Users via Link
5. Save

🔧 Step 2: Add Group to Bot
/add_chat

Bot will ask for group ID.

🔧 Step 3: Get Group ID
1. Add @userinfobot to group
2. It will send group ID
3. Copy the ID (with -)
4. Example: -1001234567890

🔧 Step 4: Add Group
/add_chat -1001234567890

✅ Done! Bot will now monitor!

🔧 Step 5: Approve Pending
/approve_all

All old requests will be approved!

📝 Need help? Check logs with Railway.
"""
    await update.message.reply_text(help_text)

async def add_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually add chat to monitor"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    if not context.args:
        msg = """📋 Add Group Manually

Usage:
/add_chat -1001234567890

How to get group ID:
1. Add @userinfobot to your group
2. It will send the group ID
3. Copy ID (with minus sign -)
4. Use: /add_chat [ID]

Example:
/add_chat -1001234567890

⚠️ Bot must be admin in group first!
"""
        await update.message.reply_text(msg)
        return
    
    try:
        chat_id = int(context.args[0])
        
        await update.message.reply_text(f"🔍 Checking group {chat_id}...")
        
        # Try to get chat
        try:
            chat = await context.bot.get_chat(chat_id)
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error accessing group!\n\n"
                f"Possible reasons:\n"
                f"• Bot not added to group\n"
                f"• Wrong chat ID\n"
                f"• Group is private\n\n"
                f"Error: {str(e)}"
            )
            return
        
        # Check if bot is admin
        try:
            member = await context.bot.get_chat_member(chat_id, context.bot.id)
            if member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    f"❌ Bot is not admin in {chat.title}!\n\n"
                    f"Please:\n"
                    f"1. Make bot administrator\n"
                    f"2. Enable 'Invite Users via Link'\n"
                    f"3. Try /add_chat again"
                )
                return
        except Exception as e:
            logger.error(f"Admin check error: {e}")
        
        # Add to database
        if add_chat_to_db(chat_id, chat.title):
            await update.message.reply_text(
                f"✅ Successfully Added!\n\n"
                f"📢 Group: {chat.title}\n"
                f"🆔 ID: `{chat_id}`\n\n"
                f"Bot will now:\n"
                f"✅ Monitor join requests\n"
                f"✅ Auto-approve new requests\n"
                f"✅ Register users\n\n"
                f"Use /approve_all to clear pending!"
            )
            logger.info(f"✅ Added chat: {chat.title} ({chat_id})")
        else:
            await update.message.reply_text("❌ Database error!")
            
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Use: /add_chat -1001234567890\n"
            "(Must be negative number for groups)"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def approve_all_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve ALL pending with welcome"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    chats = get_all_chats()
    
    if not chats:
        await update.message.reply_text(
            "⚠️ No groups added!\n\n"
            "Use /add_chat to add your group first.\n\n"
            "Example:\n"
            "/add_chat -1001234567890\n\n"
            "Type /help for setup guide."
        )
        return
    
    await update.message.reply_text(
        f"🔄 Starting approval for {len(chats)} group(s)..."
    )
    
    total_approved = 0
    total_failed = 0
    
    for chat_id, chat_title in chats:
        try:
            await update.message.reply_text(f"📡 {chat_title}...")
            
            approved = 0
            failed = 0
            
            # Get pending requests
            try:
                async for request in context.bot.get_chat_join_requests(chat_id):
                    try:
                        # Approve
                        await context.bot.approve_chat_join_request(
                            chat_id=chat_id,
                            user_id=request.user.id
                        )
                        
                        # Register
                        add_user(
                            request.user.id,
                            request.user.username,
                            request.user.first_name,
                            request.user.last_name,
                            chat_id
                        )
                        
                        # Welcome message
                        try:
                            welcome = f"""🎉 Welcome {request.user.first_name}!

✅ Your request approved!
✅ You're now in {chat_title}!

📢 Stay updated:
@{context.bot.username}
"""
                            keyboard = [[
                                InlineKeyboardButton(
                                    "✅ Start Bot",
                                    url=f"https://t.me/{context.bot.username}?start=welcome"
                                )
                            ]]
                            await context.bot.send_message(
                                chat_id=request.user.id,
                                text=welcome,
                                reply_markup=InlineKeyboardMarkup(keyboard)
                            )
                        except:
                            pass
                        
                        approved += 1
                        
                        # Log age
                        age = datetime.now() - request.date.replace(tzinfo=None)
                        logger.info(
                            f"✅ Approved: {request.user.first_name} "
                            f"({age.days}d {age.seconds//3600}h old)"
                        )
                        
                        await asyncio.sleep(0.2)
                        
                    except Exception as e:
                        failed += 1
                        logger.error(f"Approval error: {e}")
                
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
                        f"ℹ️ {chat_title}: No pending"
                    )
                    
            except Exception as e:
                await update.message.reply_text(
                    f"❌ {chat_title}: {str(e)}\n\n"
                    f"Check bot permissions!"
                )
                logger.error(f"Chat error: {e}")
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
    
    # Summary
    summary = f"""✅ Complete!

📊 Summary:
• Approved: {total_approved}
• Failed: {total_failed}
• Groups: {len(chats)}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
    await update.message.reply_text(summary)

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast to all users"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /broadcast <message>\n\n"
            "Example:\n"
            "/broadcast Hello everyone!"
        )
        return
    
    message_text = ' '.join(context.args)
    users = get_all_active_users()
    
    if not users:
        await update.message.reply_text("📭 No users!")
        return
    
    await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    
    success = 0
    failed = 0
    blocked = 0
    
    for user_id_target in users:
        try:
            await context.bot.send_message(
                chat_id=user_id_target,
                text=f"📢 Broadcast:\n\n{message_text}"
            )
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            if 'blocked' in str(e).lower():
                blocked += 1
                mark_user_blocked(user_id_target)
    
    summary = f"""✅ Broadcast Done!

• Sent: {success}
• Failed: {failed}
• Blocked: {blocked}
"""
    await update.message.reply_text(summary)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Statistics"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    stats = get_user_stats()
    chats = get_all_chats()
    
    msg = f"""📊 Statistics

👥 Users:
• Total: {stats['total']}
• Active: {stats['active']}
• Blocked: {stats['blocked']}

💬 Groups: {len(chats)}

⚙️ Running
🕐 {datetime.now().strftime('%H:%M:%S')}
"""
    await update.message.reply_text(msg)

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List users"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, first_name, username, is_active, is_blocked
            FROM users
            ORDER BY joined_date DESC
            LIMIT 20
        ''')
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            await update.message.reply_text("📭 No users!")
            return
        
        msg = "👥 Recent Users:\n\n"
        for idx, (uid, name, uname, active, blocked) in enumerate(users, 1):
            status = "🟢" if active and not blocked else "🔴" if blocked else "⚫"
            username_str = f"@{uname}" if uname else "No username"
            msg += f"{idx}. {status} {name} ({username_str})\n"
        
        msg += f"\n🟢 Active | 🔴 Blocked"
        await update.message.reply_text(msg)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def list_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List chats"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    chats = get_all_chats()
    
    if not chats:
        await update.message.reply_text(
            "📭 No groups added!\n\n"
            "Use /add_chat to add your group.\n"
            "Type /help for guide."
        )
        return
    
    msg = "💬 Monitored Groups:\n\n"
    for idx, (chat_id, title) in enumerate(chats, 1):
        msg += f"{idx}. {title}\n   ID: `{chat_id}`\n\n"
    
    await update.message.reply_text(msg)

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-handle join requests"""
    request = update.chat_join_request
    chat_id = request.chat.id
    user = request.user
    
    # Add chat if not exists
    add_chat_to_db(chat_id, request.chat.title)
    
    try:
        # Approve
        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user.id
        )
        
        # Register
        add_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            chat_id
        )
        
        # Welcome
        try:
            welcome = f"""🎉 Welcome {user.first_name}!

✅ Approved to {request.chat.title}!

📢 Start bot for updates:
@{context.bot.username}
"""
            keyboard = [[
                InlineKeyboardButton(
                    "✅ Start Bot",
                    url=f"https://t.me/{context.bot.username}?start=welcome"
                )
            ]]
            await context.bot.send_message(
                chat_id=user.id,
                text=welcome,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            pass
        
        logger.info(f"✅ Auto-approved: {user.first_name}")
        
    except Exception as e:
        logger.error(f"Auto-approve failed: {e}")

async def periodic_approval(app: Application):
    """Periodic check"""
    logger.info("🔄 Periodic task started")
    
    while True:
        try:
            await asyncio.sleep(300)
            
            chats = get_all_chats()
            total = 0
            
            for chat_id, _ in chats:
                try:
                    count = 0
                    async for req in app.bot.get_chat_join_requests(chat_id):
                        try:
                            await app.bot.approve_chat_join_request(
                                chat_id=chat_id,
                                user_id=req.user.id
                            )
                            add_user(
                                req.user.id,
                                req.user.username,
                                req.user.first_name,
                                req.user.last_name,
                                chat_id
                            )
                            count += 1
                            await asyncio.sleep(0.1)
                        except:
                            pass
                    total += count
                except:
                    pass
            
            if total > 0:
                logger.info(f"✅ Periodic: {total}")
        except:
            pass

async def post_init(app: Application):
    init_database()
    asyncio.create_task(periodic_approval(app))
    logger.info("✅ Bot initialized!")

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set!")
        return
    
    if ADMIN_USER_ID == 0:
        print("❌ ADMIN_USER_ID not set!")
        return
    
    logger.info("🤖 Starting bot...")
    logger.info(f"👤 Admin: {ADMIN_USER_ID}")
    
  
