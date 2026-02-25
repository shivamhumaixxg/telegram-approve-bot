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
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    PasswordHashInvalid,
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

# ─── BOT CLIENT ───
app = Client(
    "request_approve_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ─── USERBOT (will be set after login) ───
userbot = None

# ─── LOGIN STATE MANAGEMENT ───
# Stores login flow state for admin
# login_state[user_id] = {
#   "step": "phone" | "otp" | "2fa",
#   "phone": "...",
#   "client": Client object,
#   "phone_code_hash": "..."
# }
login_state = {}


# ═══════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def is_logged_in() -> bool:
    return userbot is not None


async def start_userbot_from_session(session_string: str) -> bool:
    """Start userbot from saved session string"""
    global userbot
    try:
        userbot = Client(
            "userbot_pending",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True,
        )
        await userbot.start()
        me = await userbot.get_me()
        logger.info(f"✅ Userbot started: {me.first_name} ({me.id})")
        return True
    except Exception as e:
        logger.error(f"❌ Userbot start failed: {e}")
        userbot = None
        return False


async def stop_userbot():
    """Stop userbot and clear session"""
    global userbot
    if userbot:
        try:
            await userbot.stop()
        except Exception:
            pass
        userbot = None


# ═══════════════════════════════════════════════════════
#  /start COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user = message.from_user
    db.add_user(user.id, user.first_name or "", user.username or "")

    bot_me = await client.get_me()
    bot_username = bot_me.username

    # Deeplink welcome
    if len(message.text.split()) > 1 and "welcome" in message.text.split()[1]:
        await message.reply_text(
            f"🎉 <b>Welcome {user.first_name}!</b>\n\n"
            f"Aap successfully register ho gaye hain is bot mein.\n"
            f"Ab aapko future updates aur broadcasts milenge! ✅"
        )
        return

    # ADMIN START
    if is_admin(user.id):
        login_status = "✅ Logged In" if is_logged_in() else "❌ Not Logged In"

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
            [
                InlineKeyboardButton(
                    "🔓 Logout" if is_logged_in() else "🔐 Login Account",
                    callback_data="admin_logout" if is_logged_in() else "admin_login_info",
                ),
            ],
        ])

        text = (
            f"👋 <b>Welcome Admin {user.first_name}!</b>\n\n"
            f"Main hoon <b>Request Approve Bot</b> 🤖\n\n"
            f"🔹 Mujhe Channel ya Group mein add karo\n"
            f"🔹 Main automatically join requests approve karunga\n"
            f"🔹 Approve hone ke baad welcome message bhi bhejunga\n\n"
            f"🔑 <b>Account Status:</b> {login_status}\n\n"
            f"⬇️ <b>Admin Panel neeche hai</b>"
        )
    else:
        # NORMAL USER START
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
            f"👋 <b>ram ram bhai {user.first_name}!</b>\n\n"
            f"Main hoon <b>Request Approve Bot</b> 🤖\n\n"
            f"🔹 Mujhe Channel ya Group mein add karo\n"
            f"🔹 Main automatically join requests approve karunga\n"
            f"🔹 Approve hone ke baad welcome message bhi bhejunga\n\n"
            f"⬇️ Neeche button dabao aur mujhe add karo!"
        )

    await message.reply_text(text, reply_markup=keyboard)


# ═══════════════════════════════════════════════════════
#  /login COMMAND - START LOGIN FLOW
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("login") & filters.private)
async def login_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin login kar sakta hai!")
        return

    if is_logged_in():
        await message.reply_text(
            "✅ <b>Already logged in hai!</b>\n\n"
            "Pehle logout karo: /logout"
        )
        return

    # Start login flow
    login_state[message.from_user.id] = {"step": "phone"}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")],
    ])

    await message.reply_text(
        "🔐 <b>Account Login</b>\n\n"
        "Apna <b>phone number</b> bhejo (with country code):\n\n"
        "Example: <code>+919876543210</code>\n\n"
        "⚠️ <b>Note:</b> Ye aapka personal Telegram account login karega\n"
        "sirf pending requests approve karne ke liye.",
        reply_markup=keyboard,
    )


# ═══════════════════════════════════════════════════════
#  /logout COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("logout") & filters.private)
async def logout_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin logout kar sakta hai!")
        return

    if not is_logged_in():
        await message.reply_text("❌ Koi account logged in nahi hai!")
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Haan, Logout Karo", callback_data="confirm_logout"),
            InlineKeyboardButton("❌ Cancel", callback_data="back_start"),
        ],
    ])

    await message.reply_text(
        "🔓 <b>Logout Confirmation</b>\n\n"
        "Kya aap sure hain? Logout karne ke baad pending approve kaam nahi karega.",
        reply_markup=keyboard,
    )


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
        login_status = "✅ Logged In" if is_logged_in() else "❌ Not Logged In"
        text += f"\n\n🔑 <b>Account:</b> {login_status}"

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
#  /addchat COMMAND (Admin Only)
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
            "<code>/addchat @channelusername</code>\n"
            "<code>/addchat -1001234567890</code>"
        )
        return

    chat_input = parts[1]
    status_msg = await message.reply_text("⏳ Chat check ho rahi hai...")

    try:
        chat = await client.get_chat(chat_input)
        chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
        db.add_chat(chat.id, chat.title or "", chat_type)

        await status_msg.edit_text(
            f"✅ <b>Chat added!</b>\n\n"
            f"📛 <b>{chat.title}</b>\n"
            f"🆔 <code>{chat.id}</code>\n"
            f"📂 {chat_type}"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: <code>{str(e)[:100]}</code>")


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
            "1️⃣ Apna message type karo\n"
            "2️⃣ Us message pe <b>reply</b> karo <code>/broadcast</code> likh ke"
        )
        return

    users = db.get_all_users()
    total = len(users)

    if total == 0:
        await message.reply_text("❌ Koi user nahi hai!")
        return

    status_msg = await message.reply_text(
        f"📢 <b>Broadcasting...</b>\n👥 Total: {total}\n⏳ Wait..."
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
                    f"📢 <b>Broadcasting...</b>\n"
                    f"✅ {success} | 🚫 {blocked} | ❌ {failed} | 📊 {success+failed+blocked}/{total}"
                )
            except Exception:
                pass
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"📢 <b>Broadcast Complete!</b>\n\n"
        f"✅ Sent: <b>{success}</b>\n"
        f"🚫 Blocked: <b>{blocked}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"📊 Total: <b>{total}</b>"
    )


# ═══════════════════════════════════════════════════════
#  /approve_pending COMMAND (Admin Only)
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("approve_pending") & filters.private)
async def approve_pending_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin!")
        return

    if not is_logged_in():
        await message.reply_text(
            "❌ <b>Account login nahi hai!</b>\n\n"
            "Pehle /login karo apna Telegram account se.\n"
            "Phir pending requests approve hogi."
        )
        return

    chats = db.get_all_chats()
    if not chats:
        await message.reply_text(
            "❌ <b>Koi chat nahi!</b>\n<code>/addchat @channelusername</code>"
        )
        return

    status_msg = await message.reply_text(
        "⏳ <b>Pending requests check ho rahi hain...</b>"
    )

    total_approved, total_errors, chat_results = await process_pending_requests(client)
    results_text = "\n".join(chat_results) if chat_results else "Koi result nahi."

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
        await message.reply_text("❌ Sirf admin!")
        return

    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>Welcome Message Set Karo:</b>\n\n"
            "<code>/set_welcome 🎉 Welcome {first_name}! Aap {chat_title} mein join ho gaye!</code>"
        )
        return

    global WELCOME_MSG
    WELCOME_MSG = message.text.split(None, 1)[1]
    await message.reply_text(f"✅ <b>Updated!</b>\n\n<b>Preview:</b>\n{WELCOME_MSG}")


# ═══════════════════════════════════════════════════════
#  LOGIN FLOW - Handle Phone, OTP, 2FA messages
# ═══════════════════════════════════════════════════════

@app.on_message(filters.private & ~filters.command(
    ["start", "stats", "broadcast", "approve_pending", "set_welcome", "login", "logout", "addchat", "cancel"]
))
async def handle_login_flow(client: Client, message: Message):
    """Handle login flow messages (phone, OTP, 2FA password)"""
    user_id = message.from_user.id

    # Check if user is in login flow
    if user_id not in login_state:
        # Normal user activity tracking
        if message.from_user:
            db.add_user(user_id, message.from_user.first_name or "", message.from_user.username or "")
            db.set_user_blocked(user_id, False)
        return

    if not is_admin(user_id):
        return

    state = login_state[user_id]
    step = state.get("step")

    # ─── STEP 1: Phone Number ───
    if step == "phone":
        phone = message.text.strip()
        if not phone.startswith("+"):
            phone = "+" + phone

        status_msg = await message.reply_text("⏳ Phone number check ho raha hai...")

        try:
            # Create temporary client for login
            temp_client = Client(
                f"login_temp_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                in_memory=True,
            )
            await temp_client.connect()

            # Send OTP
            sent_code = await temp_client.send_code(phone)

            login_state[user_id] = {
                "step": "otp",
                "phone": phone,
                "client": temp_client,
                "phone_code_hash": sent_code.phone_code_hash,
            }

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel Login", callback_data="cancel_login")],
            ])

            await status_msg.edit_text(
                f"📱 <b>OTP bhej diya gaya hai!</b>\n\n"
                f"Telegram pe OTP aaya hoga.\n"
                f"OTP yahan bhejo (spaces ke saath bhi chal jayega):\n\n"
                f"Example: <code>1 2 3 4 5</code> ya <code>12345</code>\n\n"
                f"⚠️ OTP 2 minute mein expire ho jayega.",
                reply_markup=keyboard,
            )

        except Exception as e:
            login_state.pop(user_id, None)
            await status_msg.edit_text(
                f"❌ <b>Error!</b>\n\n<code>{str(e)[:200]}</code>\n\n"
                f"Phir se try karo: /login"
            )

    # ─── STEP 2: OTP ───
    elif step == "otp":
        otp = message.text.strip().replace(" ", "").replace("-", "")
        temp_client = state["client"]
        phone = state["phone"]
        phone_code_hash = state["phone_code_hash"]

        status_msg = await message.reply_text("⏳ OTP verify ho raha hai...")

        try:
            await temp_client.sign_in(
                phone_number=phone,
                phone_code_hash=phone_code_hash,
                phone_code=otp,
            )

            # Login successful! Export session
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()

            # Save session to database
            db.save_session("userbot_session", session_string)

            # Start userbot
            success = await start_userbot_from_session(session_string)

            login_state.pop(user_id, None)

            if success:
                me = await userbot.get_me()
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Home", callback_data="back_start")],
                ])
                await status_msg.edit_text(
                    f"✅ <b>Login Successful!</b>\n\n"
                    f"👤 Account: <b>{me.first_name}</b>\n"
                    f"🆔 ID: <code>{me.id}</code>\n\n"
                    f"Ab /approve_pending se pending requests approve ho sakti hain! 🎉",
                    reply_markup=keyboard,
                )
            else:
                await status_msg.edit_text(
                    "❌ Session start nahi ho saka. Phir se /login karo."
                )

        except SessionPasswordNeeded:
            # 2FA is enabled
            login_state[user_id]["step"] = "2fa"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel Login", callback_data="cancel_login")],
            ])

            await status_msg.edit_text(
                "🔒 <b>2FA Password Required!</b>\n\n"
                "Aapke account pe 2-Step Verification ON hai.\n"
                "Apna <b>2FA password</b> bhejo:\n\n"
                "⚠️ Password sirf verify ke liye use hoga, save nahi hoga.",
                reply_markup=keyboard,
            )

        except PhoneCodeInvalid:
            await status_msg.edit_text(
                "❌ <b>Wrong OTP!</b>\n\nSahi OTP dobara bhejo."
            )

        except PhoneCodeExpired:
            login_state.pop(user_id, None)
            try:
                await temp_client.disconnect()
            except Exception:
                pass
            await status_msg.edit_text(
                "❌ <b>OTP Expire ho gaya!</b>\n\nPhir se /login karo."
            )

        except Exception as e:
            login_state.pop(user_id, None)
            try:
                await temp_client.disconnect()
            except Exception:
                pass
            await status_msg.edit_text(
                f"❌ <b>Error!</b>\n\n<code>{str(e)[:200]}</code>\n\n/login se phir try karo."
            )

    # ─── STEP 3: 2FA Password ───
    elif step == "2fa":
        password = message.text.strip()
        temp_client = state["client"]

        # Delete password message for security
        try:
            await message.delete()
        except Exception:
            pass

        status_msg = await client.send_message(
            user_id, "⏳ 2FA password verify ho raha hai..."
        )

        try:
            await temp_client.check_password(password)

            # Login successful!
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()

            # Save and start
            db.save_session("userbot_session", session_string)
            success = await start_userbot_from_session(session_string)

            login_state.pop(user_id, None)

            if success:
                me = await userbot.get_me()
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Home", callback_data="back_start")],
                ])
                await status_msg.edit_text(
                    f"✅ <b>Login Successful!</b>\n\n"
                    f"👤 Account: <b>{me.first_name}</b>\n"
                    f"🆔 ID: <code>{me.id}</code>\n\n"
                    f"Ab /approve_pending kaam karega! 🎉",
                    reply_markup=keyboard,
                )
            else:
                await status_msg.edit_text(
                    "❌ Session start nahi ho saka. /login se phir try karo."
                )

        except PasswordHashInvalid:
            await status_msg.edit_text(
                "❌ <b>Wrong Password!</b>\n\nSahi password dobara bhejo."
            )

        except Exception as e:
            login_state.pop(user_id, None)
            try:
                await temp_client.disconnect()
            except Exception:
                pass
            await status_msg.edit_text(
                f"❌ <b>Error!</b>\n\n<code>{str(e)[:200]}</code>\n\n/login se phir try karo."
            )


# ═══════════════════════════════════════════════════════
#  PROCESS PENDING REQUESTS (Uses USERBOT)
# ═══════════════════════════════════════════════════════

async def process_pending_requests(bot_client: Client):
    """Approve pending requests using userbot"""
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
            async for request in userbot.get_chat_join_requests(chat_id):
                try:
                    await userbot.approve_chat_join_request(chat_id, request.user.id)
                    db.add_user(
                        request.user.id,
                        request.user.first_name or "",
                        request.user.username or "",
                    )
                    db.log_approved_request(request.user.id, chat_id)
                    approved_count += 1

                    try:
                        bot_me = await bot_client.get_me()
                        welcome_text = (
                            f"✅ <b>Request Approved!</b>\n\n"
                            f"🎉 <b>{request.user.first_name or 'User'}</b>, aapki request "
                            f"<b>{chat_title}</b> mein approve ho gayi!\n\nWelcome! 🥳"
                        )
                        keyboard = InlineKeyboardMarkup([
                            [InlineKeyboardButton("🤖 Bot Start Karo",
                                                  url=f"https://t.me/{bot_me.username}?start=welcome")],
                        ])
                        await bot_client.send_message(
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
                        await userbot.approve_chat_join_request(chat_id, request.user.id)
                        approved_count += 1
                    except Exception:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error approving {request.user.id}: {e}")

        except ChatAdminRequired:
            chat_results.append(f"❌ <b>{chat_title}</b>: Account admin nahi hai is chat mein!")
            continue
        except Exception as e:
            chat_results.append(f"❌ <b>{chat_title}</b>: {str(e)[:80]}")
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
#  CALLBACK QUERIES
# ═══════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^help$"))
async def help_callback(client: Client, callback: CallbackQuery):
    text = (
        "📖 <b>Bot Commands:</b>\n\n"
        "/start - Bot start karo\n"
        "/stats - Statistics dekho\n"
        "/broadcast - Sabko message bhejo (Admin)\n"
        "/approve_pending - Pending requests approve (Admin)\n"
        "/set_welcome - Welcome message set karo (Admin)\n"
        "/addchat - Chat register karo (Admin)\n"
        "/login - Account login karo (Admin)\n"
        "/logout - Account logout karo (Admin)\n\n"
        "📌 <b>Kaise kaam karta hai?</b>\n"
        "1️⃣ Bot ko channel/group mein add karo\n"
        "2️⃣ Bot ko Admin banao (invite_users)\n"
        "3️⃣ 'Request to Join' ON karo\n"
        "4️⃣ Naye requests auto approve hongi!\n\n"
        "⚠️ <b>Purani Pending Requests ke liye:</b>\n"
        "/login se account login karo, phir /approve_pending"
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
    await callback.answer("✅ Updated!")


@app.on_callback_query(filters.regex("^back_start$"))
async def back_start_callback(client: Client, callback: CallbackQuery):
    user = callback.from_user
    bot_me = await client.get_me()
    bot_username = bot_me.username

    if is_admin(user.id):
        login_status = "✅ Logged In" if is_logged_in() else "❌ Not Logged In"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "➕ Channel Mein Add Karo",
                url=f"https://t.me/{bot_username}?startchannel=true&admin=invite_users",
            )],
            [InlineKeyboardButton(
                "➕ Group Mein Add Karo",
                url=f"https://t.me/{bot_username}?startgroup=true&admin=invite_users",
            )],
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_info"),
                InlineKeyboardButton("📋 Approve Pending", callback_data="admin_approve_pending"),
            ],
            [InlineKeyboardButton(
                "🔓 Logout" if is_logged_in() else "🔐 Login Account",
                callback_data="admin_logout" if is_logged_in() else "admin_login_info",
            )],
        ])
        text = (
            f"👋 <b>Welcome Admin {user.first_name}!</b>\n\n"
            f"Main hoon <b>Request Approve Bot</b> 🤖\n\n"
            f"🔑 <b>Account:</b> {login_status}\n\n"
            f"⬇️ <b>Admin Panel</b>"
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "➕ Channel Mein Add Karo",
                url=f"https://t.me/{bot_username}?startchannel=true&admin=invite_users",
            )],
            [InlineKeyboardButton(
                "➕ Group Mein Add Karo",
                url=f"https://t.me/{bot_username}?startgroup=true&admin=invite_users",
            )],
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            ],
        ])
        text = (
            f"👋 <b>Assalamu Alaikum {user.first_name}!</b>\n\n"
            f"Main hoon <b>Request Approve Bot</b> 🤖\n\n"
            f"⬇️ Neeche button dabao aur mujhe add karo!"
        )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@app.on_callback_query(filters.regex("^admin_broadcast_info$"))
async def admin_broadcast_info(client: Client, callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return

    await callback.message.edit_text(
        "📢 <b>Broadcast Kaise Karein:</b>\n\n"
        "1️⃣ Koi message type karo\n"
        "2️⃣ Reply karo <code>/broadcast</code> likh ke\n\n"
        "✅ Sabhi users ko bhej dega.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
        ]),
    )
    await callback.answer()


@app.on_callback_query(filters.regex("^admin_approve_pending$"))
async def admin_approve_pending_btn(client: Client, callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return

    if not is_logged_in():
        await callback.answer()
        await callback.message.edit_text(
            "❌ <b>Account login nahi hai!</b>\n\n"
            "Pending approve ke liye pehle login karo:\n"
            "👉 /login\n\n"
            "Login ke baad ye feature kaam karega.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Login Karo", callback_data="admin_login_info")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
            ]),
        )
        return

    chats = db.get_all_chats()
    if not chats:
        await callback.answer()
        await callback.message.edit_text(
            "❌ <b>Koi chat nahi!</b>\n<code>/addchat @username</code>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
            ]),
        )
        return

    await callback.answer("⏳ Processing...")
    await callback.message.edit_text("⏳ <b>Pending requests check ho rahi hain...</b>")

    total_approved, total_errors, chat_results = await process_pending_requests(client)
    results_text = "\n".join(chat_results) if chat_results else "Koi result nahi."

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Phir Se Check", callback_data="admin_approve_pending")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
    ])

    await callback.message.edit_text(
        f"📋 <b>Pending Requests - Results:</b>\n\n"
        f"{results_text}\n\n"
        f"─────────────────\n"
        f"✅ Approved: <b>{total_approved}</b>\n"
        f"❌ Errors: <b>{total_errors}</b>",
        reply_markup=keyboard,
    )


@app.on_callback_query(filters.regex("^admin_login_info$"))
async def admin_login_info(client: Client, callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        "🔐 <b>Account Login</b>\n\n"
        "Pending requests approve karne ke liye aapka\n"
        "Telegram account login karna padega.\n\n"
        "👉 /login command use karo\n\n"
        "<b>Flow:</b>\n"
        "1️⃣ Phone number bhejo\n"
        "2️⃣ OTP aayega Telegram pe\n"
        "3️⃣ OTP yahan bhejo\n"
        "4️⃣ 2FA password (agar hai toh)\n"
        "5️⃣ Done! ✅\n\n"
        "⚠️ Aapka account sirf pending approve ke liye use hoga.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
        ]),
    )


@app.on_callback_query(filters.regex("^admin_logout$"))
async def admin_logout_btn(client: Client, callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        "🔓 <b>Logout Confirmation</b>\n\n"
        "Logout karne ke baad pending approve kaam nahi karega.\n"
        "Kya sure ho?",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Haan Logout", callback_data="confirm_logout"),
                InlineKeyboardButton("❌ Cancel", callback_data="back_start"),
            ],
        ]),
    )


@app.on_callback_query(filters.regex("^confirm_logout$"))
async def confirm_logout_callback(client: Client, callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return

    await stop_userbot()
    db.delete_session("userbot_session")

    await callback.answer("✅ Logged out!")
    await callback.message.edit_text(
        "✅ <b>Logout Successful!</b>\n\n"
        "Account disconnect ho gaya.\n"
        "Phir se login ke liye: /login",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Home", callback_data="back_start")],
        ]),
    )


@app.on_callback_query(filters.regex("^cancel_login$"))
async def cancel_login_callback(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id

    # Cleanup login state
    if user_id in login_state:
        temp_client = login_state[user_id].get("client")
        if temp_client:
            try:
                await temp_client.disconnect()
            except Exception:
                pass
        login_state.pop(user_id, None)

    await callback.answer("❌ Login cancelled!")
    await callback.message.edit_text(
        "❌ <b>Login cancelled.</b>\n\nPhir se try ke liye: /login",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Home", callback_data="back_start")],
        ]),
    )


# ═══════════════════════════════════════════════════════
#  AUTO APPROVE JOIN REQUESTS (Bot handles new requests)
# ═══════════════════════════════════════════════════════

@app.on_chat_join_request()
async def auto_approve_request(client: Client, join_request: ChatJoinRequest):
    user = join_request.from_user
    chat = join_request.chat

    try:
        chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
        db.add_chat(chat.id, chat.title or "", chat_type)

        await join_request.approve()

        db.add_user(user.id, user.first_name or "", user.username or "")
        db.log_approved_request(user.id, chat.id)

        logger.info(f"✅ Approved: {user.first_name} ({user.id}) in {chat.title}")

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
            await client.send_message(chat_id=user.id, text=welcome_text, reply_markup=keyboard)
        except Exception:
            pass

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await auto_approve_request(client, join_request)
    except ChatAdminRequired:
        logger.error(f"❌ No admin rights in {chat.title}")
    except Exception as e:
        logger.error(f"❌ Error: {e}")


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
            try:
                await message.reply_text(
                    f"✅ <b>Bot Active!</b>\n\n"
                    f"<b>{chat.title}</b> mein active hoon.\n"
                    f"📌 Admin banao + invite_users permission do."
                )
            except Exception:
                pass


@app.on_chat_member_updated()
async def chat_member_updated(client: Client, chat_member_updated):
    try:
        if chat_member_updated.new_chat_member and chat_member_updated.new_chat_member.user:
            bot_me = await client.get_me()
            if chat_member_updated.new_chat_member.user.id == bot_me.id:
                status = chat_member_updated.new_chat_member.status
                if status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.MEMBER]:
                    chat = chat_member_updated.chat
                    chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
                    db.add_chat(chat.id, chat.title or "", chat_type)
                elif status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
                    db.remove_chat(chat_member_updated.chat.id)
    except Exception as e:
        logger.error(f"Chat update error: {e}")


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

async def main():
    logger.info("🔧 Initializing database...")
    db.init_db()

    # Try to restore userbot session from database
    saved_session = db.get_session("userbot_session")
    if saved_session:
        logger.info("🔑 Found saved session, starting userbot...")
        success = await start_userbot_from_session(saved_session)
        if success:
            logger.info("✅ Userbot restored from saved session!")
        else:
            logger.warning("⚠️ Saved session invalid, need fresh login")
            db.delete_session("userbot_session")

    # Start bot
    logger.info("🚀 Starting Bot...")
    await app.start()
    bot_me = await app.get_me()
    logger.info(f"✅ Bot: @{bot_me.username}")
    logger.info(f"👤 Admin: {ADMIN_ID}")
    logger.info(f"🔑 Userbot: {'✅ Active' if is_logged_in() else '❌ Not logged in'}")

    logger.info("🟢 Bot is running!")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
