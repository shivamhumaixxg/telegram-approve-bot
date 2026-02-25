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

WELCOME_MSG = (
    "✅ <b>Request Approved!</b>\n\n"
    "🎉 <b>{first_name}</b>, aapki request <b>{chat_title}</b> "
    "mein approve ho gayi hai!\n\n"
    "Welcome! Ab aap join ho chuke ho. 🥳\n\n"
    "🤖 Bot se connected rehne ke liye neeche button dabao."
)

# ─── BOT INIT ───
app = Client(
    "request_approve_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# ═══════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


async def register_chat(client: Client, chat_id: int):
    """Helper to register a chat in database by fetching its info"""
    try:
        chat = await client.get_chat(chat_id)
        chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
        db.add_chat(chat.id, chat.title or "", chat_type)
        logger.info(f"📥 Chat registered: {chat.title} ({chat.id})")
        return True
    except Exception as e:
        logger.error(f"Failed to register chat {chat_id}: {e}")
        return False


# ═══════════════════════════════════════════════════════
#  /start COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user = message.from_user
    db.add_user(user.id, user.first_name or "", user.username or "")

    bot_me = await client.get_me()
    bot_username = bot_me.username

    # ─── Check if deeplink welcome ───
    if len(message.text.split()) > 1 and "welcome" in message.text.split()[1]:
        await message.reply_text(
            f"🎉 <b>Welcome {user.first_name}!</b>\n\n"
            f"Aap successfully register ho gaye hain is bot mein.\n"
            f"Ab aapko future updates aur broadcasts milenge! ✅"
        )
        return

    # ─── ADMIN START ───
    if is_admin(user.id):
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
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_info"),
                InlineKeyboardButton("📋 Approve Pending", callback_data="admin_approve_pending"),
            ],
        ])

        text = (
            f"👋 <b>Welcome Admin {user.first_name}!</b>\n\n"
            f"Main hoon <b>Request Approve Bot</b> 🤖\n\n"
            f"🔹 Mujhe Channel ya Group mein add karo\n"
            f"🔹 Main automatically join requests approve karunga\n"
            f"🔹 Approve hone ke baad welcome message bhi bhejunga\n\n"
            f"📌 <b>Admin Panel neeche hai ⬇️</b>"
        )
    else:
        # ─── NORMAL USER START ───
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

    await message.reply_text(text, reply_markup=keyboard)


# ═══════════════════════════════════════════════════════
#  /stats COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("stats") & filters.private)
async def stats_cmd(client: Client, message: Message):
    user = message.from_user
    db.add_user(user.id, user.first_name or "", user.username or "")

    active = db.get_user_count()
    blocked = db.get_blocked_count()
    total = db.get_total_user_count()
    chats_count = db.get_chat_count()
    approved = db.get_total_approved()

    text = (
        "📊 <b>Bot Statistics:</b>\n\n"
        f"👥 Total Users: <b>{total}</b>\n"
        f"✅ Active Users: <b>{active}</b>\n"
        f"🚫 Blocked Users: <b>{blocked}</b>\n"
        f"💬 Active Chats: <b>{chats_count}</b>\n"
        f"📋 Total Approved: <b>{approved}</b>"
    )

    if is_admin(user.id):
        chats = db.get_all_chats()
        if chats:
            text += "\n\n📝 <b>Chat List:</b>\n"
            for i, ch in enumerate(chats, 1):
                text += f"  {i}. <b>{ch['chat_title']}</b> ({ch['chat_type']})\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="status")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
    ])

    await message.reply_text(text, reply_markup=keyboard)


# ═══════════════════════════════════════════════════════
#  /addchat COMMAND (Admin Only) - Manually register chat
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("addchat") & filters.private)
async def addchat_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin chat add kar sakta hai!")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply_text(
            "📝 <b>Chat Manually Add Karo:</b>\n\n"
            "Channel/Group ka username ya ID bhejo:\n\n"
            "<code>/addchat @channelusername</code>\n"
            "<code>/addchat -1001234567890</code>\n\n"
            "💡 Channel ID kaise pata kare?\n"
            "Channel ka koi message forward karo @userinfobot ko."
        )
        return

    chat_input = parts[1]

    status_msg = await message.reply_text("⏳ Chat check ho rahi hai...")

    try:
        # Try to get chat info
        chat = await client.get_chat(chat_input)
        chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
        db.add_chat(chat.id, chat.title or "", chat_type)

        await status_msg.edit_text(
            f"✅ <b>Chat successfully added!</b>\n\n"
            f"📛 Name: <b>{chat.title}</b>\n"
            f"🆔 ID: <code>{chat.id}</code>\n"
            f"📂 Type: {chat_type}\n\n"
            f"Ab /approve_pending se pending requests approve kar sakte ho."
        )
    except Exception as e:
        await status_msg.edit_text(
            f"❌ <b>Chat add nahi ho saki!</b>\n\n"
            f"Error: <code>{str(e)[:100]}</code>\n\n"
            f"Check karo:\n"
            f"• Bot us chat mein admin hai?\n"
            f"• Username ya ID sahi hai?\n"
            f"• Channel/Group public hai ya bot add hai?"
        )


# ═══════════════════════════════════════════════════════
#  /broadcast COMMAND (Admin Only)
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin broadcast kar sakta hai!")
        return

    if not message.reply_to_message:
        await message.reply_text(
            "📢 <b>Broadcast Kaise Karein:</b>\n\n"
            "1️⃣ Pehle apna message type karo (text/photo/video/document)\n"
            "2️⃣ Phir us message pe <b>reply</b> karo <code>/broadcast</code> likh ke\n\n"
            "✅ Bot sabhi active users ko wo message bhej dega."
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

        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"📢 <b>Broadcast Complete!</b>\n\n"
        f"✅ Successfully Sent: <b>{success}</b>\n"
        f"🚫 Blocked/Deactivated: <b>{blocked}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"📊 Total: <b>{total}</b>"
    )


# ═══════════════════════════════════════════════════════
#  /approve_pending COMMAND (Admin Only)
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("approve_pending") & filters.private)
async def approve_pending_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin pending requests approve kar sakta hai!")
        return

    chats = db.get_all_chats()

    if not chats:
        await message.reply_text(
            "❌ <b>Koi chat registered nahi hai!</b>\n\n"
            "Chat manually add karo:\n"
            "<code>/addchat @channelusername</code>\n"
            "<code>/addchat -1001234567890</code>\n\n"
            "Ya bot ko channel/group se remove karke dobara add karo."
        )
        return

    status_msg = await message.reply_text(
        "⏳ <b>Pending requests check ho rahi hain...</b>\n"
        "Har chat check ki ja rahi hai, please wait..."
    )

    total_approved, total_errors, chat_results = await process_pending_requests(client)

    results_text = "\n".join(chat_results) if chat_results else "Koi chat nahi mili."

    await status_msg.edit_text(
        f"📋 <b>Pending Requests - Results:</b>\n\n"
        f"{results_text}\n\n"
        f"─────────────────\n"
        f"✅ Total Approved: <b>{total_approved}</b>\n"
        f"❌ Total Errors: <b>{total_errors}</b>"
    )


# ═══════════════════════════════════════════════════════
#  /set_welcome COMMAND (Admin Only)
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("set_welcome") & filters.private)
async def set_welcome_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin welcome message set kar sakta hai!")
        return

    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>Welcome Message Set Karo:</b>\n\n"
            "<code>/set_welcome Aapka naya welcome message yahan likho</code>\n\n"
            "<b>Variables jo use kar sakte ho:</b>\n"
            "<code>{first_name}</code> - User ka naam\n"
            "<code>{chat_title}</code> - Chat ka naam\n\n"
            "<b>Example:</b>\n"
            "<code>/set_welcome 🎉 Welcome {first_name}! Aap {chat_title} mein join ho gaye!</code>"
        )
        return

    global WELCOME_MSG
    WELCOME_MSG = message.text.split(None, 1)[1]

    await message.reply_text(
        f"✅ <b>Welcome message updated!</b>\n\n"
        f"<b>Preview:</b>\n{WELCOME_MSG}"
    )


# ═══════════════════════════════════════════════════════
#  SHARED FUNCTION: Process Pending Requests
# ═══════════════════════════════════════════════════════

async def process_pending_requests(client: Client):
    """Shared logic for both command and button to approve pending requests"""
    chats = db.get_all_chats()
    total_approved = 0
    total_errors = 0
    chat_results = []

    for chat in chats:
        chat_id = chat["chat_id"]
        chat_title = chat["chat_title"]
        approved_count = 0
        error_count = 0

        try:
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

                    try:
                        bot_me = await client.get_me()
                        welcome_text = (
                            f"✅ <b>Request Approved!</b>\n\n"
                            f"🎉 <b>{request.user.first_name}</b>, aapki pending request "
                            f"<b>{chat_title}</b> mein approve ho gayi hai!\n\n"
                            f"Welcome! 🥳"
                        )
                        keyboard = InlineKeyboardMarkup([
                            [InlineKeyboardButton("🤖 Bot Start Karo",
                                                  url=f"https://t.me/{bot_me.username}?start=welcome")],
                        ])
                        await client.send_message(
                            chat_id=request.user.id,
                            text=welcome_text,
                            reply_markup=keyboard,
                        )
                    except Exception:
                        pass

                    await asyncio.sleep(0.5)

                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    try:
                        await client.approve_chat_join_request(chat_id, request.user.id)
                        approved_count += 1
                    except Exception:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error approving pending: {e}")

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

    return total_approved, total_errors, chat_results


# ═══════════════════════════════════════════════════════
#  CALLBACK QUERIES (Buttons)
# ═══════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^help$"))
async def help_callback(client: Client, callback: CallbackQuery):
    text = (
        "📖 <b>Bot Commands:</b>\n\n"
        "/start - Bot start karo\n"
        "/stats - Statistics dekho\n"
        "/broadcast - Sabko message bhejo (Admin)\n"
        "/approve_pending - Pending requests approve karo (Admin)\n"
        "/set_welcome - Welcome message set karo (Admin)\n"
        "/addchat - Chat manually register karo (Admin)\n\n"
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


@app.on_callback_query(filters.regex("^back_start$"))
async def back_start_callback(client: Client, callback: CallbackQuery):
    user = callback.from_user
    bot_me = await client.get_me()
    bot_username = bot_me.username

    if is_admin(user.id):
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
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_info"),
                InlineKeyboardButton("📋 Approve Pending", callback_data="admin_approve_pending"),
            ],
        ])
        text = (
            f"👋 <b>Welcome Admin {user.first_name}!</b>\n\n"
            f"Main hoon <b>Request Approve Bot</b> 🤖\n\n"
            f"🔹 Mujhe Channel ya Group mein add karo\n"
            f"🔹 Main automatically join requests approve karunga\n\n"
            f"📌 <b>Admin Panel neeche hai ⬇️</b>"
        )
    else:
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
            f"🔹 Main automatically join requests approve karunga\n\n"
            f"⬇️ Neeche button dabao aur mujhe add karo!"
        )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ─── ADMIN BUTTON: Broadcast Info ───
@app.on_callback_query(filters.regex("^admin_broadcast_info$"))
async def admin_broadcast_info(client: Client, callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return

    text = (
        "📢 <b>Broadcast Kaise Karein:</b>\n\n"
        "1️⃣ Koi bhi message type karo (text/photo/video/document)\n"
        "2️⃣ Us message pe <b>reply</b> karo <code>/broadcast</code> likh ke\n\n"
        "✅ Bot sabhi active users ko wo message forward kar dega.\n"
        "📊 Live progress dikhega."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ─── ADMIN BUTTON: Approve Pending ───
@app.on_callback_query(filters.regex("^admin_approve_pending$"))
async def admin_approve_pending_btn(client: Client, callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return

    chats = db.get_all_chats()

    if not chats:
        await callback.answer()
        await callback.message.edit_text(
            "❌ <b>Koi chat registered nahi hai!</b>\n\n"
            "Chat manually add karo:\n"
            "<code>/addchat @channelusername</code>\n"
            "<code>/addchat -1001234567890</code>\n\n"
            "Ya bot ko channel/group se remove karke dobara add karo.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
            ]),
        )
        return

    await callback.answer("⏳ Processing...")

    await callback.message.edit_text(
        "⏳ <b>Pending requests check ho rahi hain...</b>\n"
        "Har chat check ki ja rahi hai, please wait..."
    )

    total_approved, total_errors, chat_results = await process_pending_requests(client)

    results_text = "\n".join(chat_results) if chat_results else "Koi chat nahi mili."

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Phir Se Check Karo", callback_data="admin_approve_pending")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
    ])

    await callback.message.edit_text(
        f"📋 <b>Pending Requests - Results:</b>\n\n"
        f"{results_text}\n\n"
        f"─────────────────\n"
        f"✅ Total Approved: <b>{total_approved}</b>\n"
        f"❌ Total Errors: <b>{total_errors}</b>",
        reply_markup=keyboard,
    )


# ═══════════════════════════════════════════════════════
#  AUTO APPROVE JOIN REQUESTS
#  *** ALSO REGISTERS CHAT AUTOMATICALLY ***
# ═══════════════════════════════════════════════════════

@app.on_chat_join_request()
async def auto_approve_request(client: Client, join_request: ChatJoinRequest):
    user = join_request.from_user
    chat = join_request.chat

    try:
        # ★★★ AUTO REGISTER CHAT - Ye hai main fix! ★★★
        # Jab bhi koi join request aaye, chat ko database mein register karo
        chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
        db.add_chat(chat.id, chat.title or "", chat_type)

        # Approve the request
        await join_request.approve()

        db.add_user(user.id, user.first_name or "", user.username or "")
        db.log_approved_request(user.id, chat.id)

        logger.info(
            f"✅ Approved: {user.first_name} ({user.id}) in {chat.title} ({chat.id})"
        )

        # Send welcome message to user in PM
        try:
            bot_me = await client.get_me()

            welcome_text = WELCOME_MSG.format(
                first_name=user.first_name or "User",
                chat_title=chat.title or "Chat",
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Bot Start Karo",
                                      url=f"https://t.me/{bot_me.username}?start=welcome")],
            ])

            await client.send_message(
                chat_id=user.id,
                text=welcome_text,
                reply_markup=keyboard,
            )
        except (UserIsBlocked, PeerIdInvalid, InputUserDeactivated):
            logger.info(f"Could not send welcome to {user.id} - hasn't started bot")
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


# ═══════════════════════════════════════════════════════
#  BOT ADDED/REMOVED FROM CHATS
# ═══════════════════════════════════════════════════════

@app.on_message(filters.new_chat_members)
async def bot_added_to_chat(client: Client, message: Message):
    bot_me = await client.get_me()

    for member in message.new_chat_members:
        if member.id == bot_me.id:
            chat = message.chat
            chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
            db.add_chat(chat.id, chat.title or "", chat_type)
            logger.info(f"📥 Bot added to: {chat.title} ({chat.id})")

            try:
                await message.reply_text(
                    f"✅ <b>Bot Active!</b>\n\n"
                    f"Main ab <b>{chat.title}</b> mein active hoon.\n"
                    f"Ab se join requests automatically approve hongi!\n\n"
                    f"📌 Mujhe admin banao aur 'invite_users' permission do."
                )
            except Exception:
                pass


@app.on_chat_member_updated()
async def chat_member_updated(client: Client, chat_member_updated):
    """Detect when bot is added/removed from channels"""
    try:
        if chat_member_updated.new_chat_member and chat_member_updated.new_chat_member.user:
            bot_me = await client.get_me()
            if chat_member_updated.new_chat_member.user.id == bot_me.id:
                new_status = chat_member_updated.new_chat_member.status

                if new_status in [
                    enums.ChatMemberStatus.ADMINISTRATOR,
                    enums.ChatMemberStatus.MEMBER,
                ]:
                    chat = chat_member_updated.chat
                    chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
                    db.add_chat(chat.id, chat.title or "", chat_type)
                    logger.info(f"📥 Bot added/promoted in: {chat.title} ({chat.id})")

                elif new_status in [
                    enums.ChatMemberStatus.BANNED,
                    enums.ChatMemberStatus.LEFT,
                ]:
                    chat = chat_member_updated.chat
                    db.remove_chat(chat.id)
                    logger.info(f"📤 Bot removed from: {chat.title} ({chat.id})")
    except Exception as e:
        logger.error(f"Chat member update error: {e}")


# ═══════════════════════════════════════════════════════
#  TRACK USER ACTIVITY (Group 1 - doesn't block commands)
# ═══════════════════════════════════════════════════════

@app.on_message(filters.private, group=1)
async def track_user_activity(client: Client, message: Message):
    """Track all private messages for user activity.
    Runs in group 1 so it does NOT block command handlers in group 0."""
    if message.from_user:
        user = message.from_user
        db.add_user(user.id, user.first_name or "", user.username or "")
        db.set_user_blocked(user.id, False)


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    logger.info("🔧 Initializing database...")
    db.init_db()

    logger.info("🚀 Starting Request Approve Bot...")
    logger.info(f"👤 Admin ID: {ADMIN_ID}")
    app.run()


if __name__ == "__main__":
    main()
