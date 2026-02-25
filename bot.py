import asyncio
import logging
import os
import time

from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    ChatJoinRequest,
    CallbackQuery,
)
from pyrogram.errors import (
    FloodWait,
    UserIsBlocked,
    InputUserDeactivated,
    PeerIdInvalid,
    ChatAdminRequired,
    UserNotParticipant,
)

import database as db

# ─── LOGGING ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ─── CONFIG ───
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
WELCOME_MSG = os.environ.get(
    "WELCOME_MSG",
    "✅ <b>Aapki request approve ho gayi hai!</b>\n\n"
    "🎉 Welcome! Ab aap group/channel mein join ho chuke ho.\n"
    "Bot se connected rehne ke liye /start dabayein.",
)

# ─── BOT INIT ───
app = Client(
    "request_approve_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# ─── HELPER: Check Admin ───
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ─── /start COMMAND ───
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user = message.from_user
    db.add_user(user.id, user.first_name or "", user.username or "")

    bot_me = await client.get_me()
    bot_username = bot_me.username

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Channel Mein Add Karo",
                url=f"https://t.me/{bot_username}?startchannel=true&admin=invite_users",
            ),
        ],
        [
            InlineKeyboardButton(
                "➕ Group Mein Add Karo",
                url=f"https://t.me/{bot_username}?startgroup=true&admin=invite_users",
            ),
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ],
    ])

    text = (
        f"👋 <b>Assalamu Alaikum {user.first_name}!</b>\n\n"
        f"Main hoon <b>Request Approve Bot</b> 🤖\n\n"
        f"🔹 Mujhe Channel ya Group mein add karo\n"
        f"🔹 Main automatically join requests approve karunga\n"
        f"🔹 Approve hone ke baad welcome message bhi bhejunga\n\n"
        f"📌 <b>Features:</b>\n"
        f"• Auto Request Approve\n"
        f"• Welcome Message\n"
        f"• Pending Requests Approve\n"
        f"• Broadcast to All Users\n"
        f"• User Statistics\n\n"
        f"⬇️ Neeche button dabao aur mujhe add karo!"
    )

    await message.reply_text(text, reply_markup=keyboard)


# ─── HELP CALLBACK ───
@app.on_callback_query(filters.regex("^help$"))
async def help_callback(client: Client, callback: CallbackQuery):
    text = (
        "📖 <b>Bot Commands:</b>\n\n"
        "/start - Bot start karo\n"
        "/stats - Statistics dekho\n"
        "/broadcast - Sabko message bhejo (Admin)\n"
        "/approve_pending - Pending requests approve karo (Admin)\n"
        "/set_welcome - Welcome message set karo (Admin)\n\n"
        "📌 <b>Kaise kaam karta hai?</b>\n"
        "1️⃣ Bot ko channel/group mein add karo\n"
        "2️⃣ Bot ko Admin banao (invite_users permission)\n"
        "3️⃣ Channel/Group mein 'Request to Join' ON karo\n"
        "4️⃣ Ab jo bhi request aayegi, bot auto approve karega!"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ─── STATUS CALLBACK ───
@app.on_callback_query(filters.regex("^status$"))
async def status_callback(client: Client, callback: CallbackQuery):
    active = db.get_user_count()
    blocked = db.get_blocked_count()
    total = db.get_total_user_count()
    chats = db.get_chat_count()
    approved = db.get_total_approved()

    text = (
        "📊 <b>Bot Statistics:</b>\n\n"
        f"👥 Total Users: <b>{total}</b>\n"
        f"✅ Active Users: <b>{active}</b>\n"
        f"🚫 Blocked Users: <b>{blocked}</b>\n"
        f"💬 Active Chats: <b>{chats}</b>\n"
        f"📋 Total Approved: <b>{approved}</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="status")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("✅ Stats Updated!")


# ─── BACK TO START CALLBACK ───
@app.on_callback_query(filters.regex("^back_start$"))
async def back_start_callback(client: Client, callback: CallbackQuery):
    user = callback.from_user
    bot_me = await client.get_me()
    bot_username = bot_me.username

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Channel Mein Add Karo",
                url=f"https://t.me/{bot_username}?startchannel=true&admin=invite_users",
            ),
        ],
        [
            InlineKeyboardButton(
                "➕ Group Mein Add Karo",
                url=f"https://t.me/{bot_username}?startgroup=true&admin=invite_users",
            ),
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ],
    ])

    text = (
        f"👋 <b>Assalamu Alaikum {user.first_name}!</b>\n\n"
        f"Main hoon <b>Request Approve Bot</b> 🤖\n\n"
        f"🔹 Mujhe Channel ya Group mein add karo\n"
        f"🔹 Main automatically join requests approve karunga\n"
        f"🔹 Approve hone ke baad welcome message bhi bhejunga\n\n"
        f"⬇️ Neeche button dabao aur mujhe add karo!"
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ─── AUTO APPROVE JOIN REQUESTS ───
@app.on_chat_join_request()
async def auto_approve_request(client: Client, join_request: ChatJoinRequest):
    user = join_request.from_user
    chat = join_request.chat

    try:
        # Approve the request
        await join_request.approve()

        # Log to database
        db.add_user(user.id, user.first_name or "", user.username or "")
        db.log_approved_request(user.id, chat.id)

        logger.info(
            f"✅ Approved: {user.first_name} ({user.id}) in {chat.title} ({chat.id})"
        )

        # Send welcome message to user in PM
        try:
            welcome_text = (
                f"✅ <b>Request Approved!</b>\n\n"
                f"🎉 <b>{user.first_name}</b>, aapki request <b>{chat.title}</b> "
                f"mein approve ho gayi hai!\n\n"
                f"Welcome! Ab aap join ho chuke ho. 🥳\n\n"
                f"🤖 Iss bot se connected rehne ke liye /start dabayein."
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Bot Start Karo", url=f"https://t.me/{(await client.get_me()).username}?start=welcome")],
            ])

            await client.send_message(
                chat_id=user.id,
                text=welcome_text,
                reply_markup=keyboard,
            )
        except (UserIsBlocked, PeerIdInvalid, InputUserDeactivated):
            # User hasn't started the bot or blocked it
            logger.info(f"Could not send welcome to {user.id} - user hasn't started bot")
        except Exception as e:
            logger.warning(f"Welcome message failed for {user.id}: {e}")

    except FloodWait as e:
        logger.warning(f"FloodWait: Sleeping {e.value}s")
        await asyncio.sleep(e.value)
        await auto_approve_request(client, join_request)
    except ChatAdminRequired:
        logger.error(f"❌ No admin rights in {chat.title} ({chat.id})")
    except Exception as e:
        logger.error(f"❌ Error approving {user.id} in {chat.id}: {e}")


# ─── BOT ADDED TO GROUP/CHANNEL ───
@app.on_message(filters.new_chat_members)
async def bot_added_to_chat(client: Client, message: Message):
    bot_me = await client.get_me()

    for member in message.new_chat_members:
        if member.id == bot_me.id:
            chat = message.chat
            db.add_chat(chat.id, chat.title or "", chat.type.value)
            logger.info(f"📥 Bot added to: {chat.title} ({chat.id})")

            try:
                await message.reply_text(
                    f"✅ <b>Bot Active!</b>\n\n"
                    f"Main ab <b>{chat.title}</b> mein active hoon.\n"
                    f"Ab se join requests automatically approve hongi!\n\n"
                    f"📌 <b>Note:</b> Mujhe admin banao aur 'invite_users' permission do.\n"
                    f"📌 Purani pending requests ke liye admin bot mein /approve_pending use kare."
                )
            except Exception as e:
                logger.warning(f"Could not send activation msg: {e}")


# ─── BOT ADDED TO CHANNEL (via my_chat_member) ───
@app.on_raw_update()
async def handle_raw_update(client, update, users, chats):
    """Handle channel additions via raw updates since filters don't catch channel adds directly"""
    from pyrogram.raw.types import (
        UpdateBotChatInviteRequester,
    )
    # This is handled by pyrogram's built-in handlers
    pass


@app.on_chat_member_updated()
async def chat_member_updated(client: Client, chat_member_updated):
    """Detect when bot is added/removed from channels and groups"""
    if chat_member_updated.new_chat_member and chat_member_updated.new_chat_member.user:
        bot_me = await client.get_me()
        if chat_member_updated.new_chat_member.user.id == bot_me.id:
            new_status = chat_member_updated.new_chat_member.status

            if new_status in [
                enums.ChatMemberStatus.ADMINISTRATOR,
                enums.ChatMemberStatus.MEMBER,
            ]:
                chat = chat_member_updated.chat
                db.add_chat(chat.id, chat.title or "", chat.type.value if hasattr(chat.type, 'value') else str(chat.type))
                logger.info(f"📥 Bot added/promoted in: {chat.title} ({chat.id})")

            elif new_status in [
                enums.ChatMemberStatus.BANNED,
                enums.ChatMemberStatus.LEFT,
            ]:
                chat = chat_member_updated.chat
                db.remove_chat(chat.id)
                logger.info(f"📤 Bot removed from: {chat.title} ({chat.id})")


# ─── /stats COMMAND (Admin) ───
@app.on_message(filters.command("stats") & filters.private)
async def stats_cmd(client: Client, message: Message):
    active = db.get_user_count()
    blocked = db.get_blocked_count()
    total = db.get_total_user_count()
    chats_count = db.get_chat_count()
    approved = db.get_total_approved()
    chats = db.get_all_chats()

    chat_list = ""
    for i, ch in enumerate(chats, 1):
        chat_list += f"  {i}. <b>{ch['chat_title']}</b> ({ch['chat_type']})\n"

    if not chat_list:
        chat_list = "  Koi chat nahi hai abhi.\n"

    text = (
        "📊 <b>Bot Statistics:</b>\n\n"
        f"👥 Total Users: <b>{total}</b>\n"
        f"✅ Active Users: <b>{active}</b>\n"
        f"🚫 Blocked Users: <b>{blocked}</b>\n"
        f"💬 Active Chats: <b>{chats_count}</b>\n"
        f"📋 Total Approved: <b>{approved}</b>\n\n"
        f"📝 <b>Chat List:</b>\n{chat_list}"
    )

    await message.reply_text(text)


# ─── /broadcast COMMAND (Admin Only) ───
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin broadcast kar sakta hai!")
        return

    # Check if it's a reply to a message
    if not message.reply_to_message:
        await message.reply_text(
            "📢 <b>Broadcast Kaise Karein:</b>\n\n"
            "1️⃣ Apna message type karo (text/photo/video/document)\n"
            "2️⃣ Us message pe reply karo /broadcast ke saath\n\n"
            "Example: Koi message bhejo, phir uspe reply karo:\n"
            "<code>/broadcast</code>"
        )
        return

    users = db.get_all_users()
    total = len(users)

    if total == 0:
        await message.reply_text("❌ Koi user nahi hai database mein!")
        return

    status_msg = await message.reply_text(
        f"📢 <b>Broadcasting...</b>\n\n"
        f"👥 Total Users: {total}\n"
        f"⏳ Please wait..."
    )

    success = 0
    failed = 0
    blocked = 0

    for user in users:
        try:
            await message.reply_to_message.copy(user["user_id"])
            success += 1
        except UserIsBlocked:
            blocked += 1
            db.set_user_blocked(user["user_id"], True)
        except InputUserDeactivated:
            blocked += 1
            db.set_user_blocked(user["user_id"], True)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await message.reply_to_message.copy(user["user_id"])
                success += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1

        # Update status every 20 users
        if (success + failed + blocked) % 20 == 0:
            try:
                await status_msg.edit_text(
                    f"📢 <b>Broadcasting...</b>\n\n"
                    f"✅ Sent: {success}\n"
                    f"🚫 Blocked: {blocked}\n"
                    f"❌ Failed: {failed}\n"
                    f"📊 Progress: {success + failed + blocked}/{total}"
                )
            except Exception:
                pass

        await asyncio.sleep(0.05)  # Rate limit protection

    await status_msg.edit_text(
        f"📢 <b>Broadcast Complete!</b>\n\n"
        f"✅ Successfully Sent: <b>{success}</b>\n"
        f"🚫 Blocked/Deactivated: <b>{blocked}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"📊 Total: <b>{total}</b>"
    )


# ─── /approve_pending COMMAND (Admin Only) ───
@app.on_message(filters.command("approve_pending") & filters.private)
async def approve_pending_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin pending requests approve kar sakta hai!")
        return

    chats = db.get_all_chats()

    if not chats:
        await message.reply_text(
            "❌ Koi chat nahi hai!\n"
            "Pehle bot ko kisi channel/group mein add karo."
        )
        return

    status_msg = await message.reply_text(
        "⏳ <b>Pending requests check ho rahi hain...</b>\n"
        "Please wait..."
    )

    total_approved = 0
    total_errors = 0
    chat_results = []

    for chat in chats:
        chat_id = chat["chat_id"]
        chat_title = chat["chat_title"]
        approved_count = 0
        error_count = 0

        try:
            # Get pending join requests
            async for request in client.get_chat_join_requests(chat_id):
                try:
                    await client.approve_chat_join_request(chat_id, request.user.id)
                    db.add_user(
                        request.user.id,
                        request.user.first_name or "",
                        request.user.username or "",
                    )
                    db.log_approved_request(request.user.id, chat_id)
                    approved_count += 1

                    # Send welcome message
                    try:
                        welcome_text = (
                            f"✅ <b>Request Approved!</b>\n\n"
                            f"🎉 <b>{request.user.first_name}</b>, aapki pending request "
                            f"<b>{chat_title}</b> mein approve ho gayi hai!\n\n"
                            f"Welcome! 🥳"
                        )
                        await client.send_message(
                            chat_id=request.user.id,
                            text=welcome_text,
                        )
                    except Exception:
                        pass

                    await asyncio.sleep(0.5)  # Rate limit

                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    try:
                        await client.approve_chat_join_request(chat_id, request.user.id)
                        approved_count += 1
                    except Exception:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error approving pending request: {e}")

        except ChatAdminRequired:
            chat_results.append(f"❌ <b>{chat_title}</b>: Admin rights nahi hain!")
            continue
        except Exception as e:
            chat_results.append(f"❌ <b>{chat_title}</b>: Error - {str(e)[:50]}")
            continue

        total_approved += approved_count
        total_errors += error_count

        if approved_count > 0 or error_count > 0:
            chat_results.append(
                f"✅ <b>{chat_title}</b>: {approved_count} approved, {error_count} failed"
            )
        else:
            chat_results.append(f"📭 <b>{chat_title}</b>: Koi pending request nahi")

        # Update status
        try:
            await status_msg.edit_text(
                f"⏳ <b>Processing...</b>\n\n"
                f"Approved so far: {total_approved}\n"
                f"Checking: {chat_title}..."
            )
        except Exception:
            pass

    results_text = "\n".join(chat_results) if chat_results else "Koi result nahi."

    await status_msg.edit_text(
        f"📋 <b>Pending Requests - Results:</b>\n\n"
        f"{results_text}\n\n"
        f"─────────────────\n"
        f"✅ Total Approved: <b>{total_approved}</b>\n"
        f"❌ Total Errors: <b>{total_errors}</b>"
    )


# ─── /set_welcome COMMAND (Admin Only) ───
@app.on_message(filters.command("set_welcome") & filters.private)
async def set_welcome_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin welcome message set kar sakta hai!")
        return

    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>Welcome Message Set Karo:</b>\n\n"
            "<code>/set_welcome Aapka welcome message yahan likho</code>\n\n"
            "Variables:\n"
            "<code>{first_name}</code> - User ka naam\n"
            "<code>{chat_title}</code> - Chat ka naam"
        )
        return

    new_welcome = message.text.split(None, 1)[1]
    # Store in environment (for Railway, use env vars)
    global WELCOME_MSG
    WELCOME_MSG = new_welcome

    await message.reply_text(
        f"✅ <b>Welcome message updated!</b>\n\n"
        f"<b>Preview:</b>\n{new_welcome}"
    )


# ─── HANDLE /start FROM WELCOME DEEPLINK ───
@app.on_message(filters.command("start") & filters.private & filters.regex(r"^/start welcome"))
async def start_welcome_cmd(client: Client, message: Message):
    user = message.from_user
    db.add_user(user.id, user.first_name or "", user.username or "")

    await message.reply_text(
        f"🎉 <b>Welcome {user.first_name}!</b>\n\n"
        f"Aap successfully register ho gaye hain is bot mein.\n"
        f"Ab aapko future updates aur broadcasts milenge! ✅"
    )


# ─── HANDLE BLOCKED/UNBLOCKED ───
@app.on_message(filters.private & ~filters.command(["start", "stats", "broadcast", "approve_pending", "set_welcome"]))
async def handle_private_message(client: Client, message: Message):
    """Track user activity and handle unknown commands"""
    user = message.from_user
    db.add_user(user.id, user.first_name or "", user.username or "")
    db.set_user_blocked(user.id, False)  # User is active


# ─── ERROR HANDLER ───
async def error_handler(client, error):
    logger.error(f"Error: {error}")


# ─── MAIN ───
def main():
    logger.info("🔧 Initializing database...")
    db.init_db()

    logger.info("🚀 Starting Request Approve Bot...")
    app.run()


if __name__ == "__main__":
    main()
