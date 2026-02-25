import asyncio
import logging
import os
import time

from pyrogram import Client, filters, enums, idle
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

# ─── USERBOT (set after login) ───
userbot = None

# ─── LOGIN STATE ───
login_state = {}


# ═══════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def is_logged_in() -> bool:
    return userbot is not None


async def start_userbot_from_session(session_string: str) -> bool:
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

    if len(message.text.split()) > 1 and "welcome" in message.text.split()[1]:
        await message.reply_text(
            f"🎉 <b>Welcome {user.first_name}!</b>\n\n"
            f"Aap successfully register ho gaye hain is bot mein.\n"
            f"Ab aapko future updates aur broadcasts milenge! ✅"
        )
        return

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
            f"🔹 Mujhe Channel ya Group mein add karo\n"
            f"🔹 Main automatically join requests approve karunga\n"
            f"🔹 Approve hone ke baad welcome message bhi bhejunga\n\n"
            f"🔑 <b>Account Status:</b> {login_status}\n\n"
            f"⬇️ <b>Admin Panel neeche hai</b>"
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
            f"🔹 Mujhe Channel ya Group mein add karo\n"
            f"🔹 Main automatically join requests approve karunga\n"
            f"🔹 Approve hone ke baad welcome message bhi bhejunga\n\n"
            f"⬇️ Neeche button dabao aur mujhe add karo!"
        )

    await message.reply_text(text, reply_markup=keyboard)


# ═══════════════════════════════════════════════════════
#  /login COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("login") & filters.private)
async def login_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin login kar sakta hai!")
        return

    if is_logged_in():
        await message.reply_text("✅ Already logged in! Pehle /logout karo.")
        return

    login_state[message.from_user.id] = {"step": "phone"}

    await message.reply_text(
        "🔐 <b>Account Login</b>\n\n"
        "Apna <b>phone number</b> bhejo (with country code):\n\n"
        "Example: <code>+919876543210</code>\n\n"
        "⚠️ Sirf pending requests approve ke liye use hoga.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")],
        ]),
    )


# ═══════════════════════════════════════════════════════
#  /logout COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("logout") & filters.private)
async def logout_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin!")
        return

    if not is_logged_in():
        await message.reply_text("❌ Koi account logged in nahi hai!")
        return

    await message.reply_text(
        "🔓 <b>Logout Confirmation</b>\n\nLogout karne ke baad pending approve nahi hoga.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Haan Logout", callback_data="confirm_logout"),
                InlineKeyboardButton("❌ Cancel", callback_data="back_start"),
            ],
        ]),
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

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="status")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
    ]))


# ═══════════════════════════════════════════════════════
#  /addchat COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("addchat") & filters.private)
async def addchat_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin!")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply_text(
            "📝 <code>/addchat @channelusername</code>\n"
            "<code>/addchat -1001234567890</code>"
        )
        return

    status_msg = await message.reply_text("⏳ ...")

    try:
        chat = await client.get_chat(parts[1])
        chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
        db.add_chat(chat.id, chat.title or "", chat_type)
        await status_msg.edit_text(
            f"✅ <b>Added!</b>\n📛 <b>{chat.title}</b>\n🆔 <code>{chat.id}</code>"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: <code>{str(e)[:100]}</code>")


# ═══════════════════════════════════════════════════════
#  /broadcast COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin!")
        return

    if not message.reply_to_message:
        await message.reply_text(
            "📢 <b>Broadcast:</b>\n\n"
            "1️⃣ Message type karo\n"
            "2️⃣ Reply karo <code>/broadcast</code>"
        )
        return

    users = db.get_all_users()
    total = len(users)
    if total == 0:
        await message.reply_text("❌ Koi user nahi!")
        return

    status_msg = await message.reply_text(f"📢 Broadcasting... 👥 {total}")

    success = failed = blocked = 0

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
                    f"📢 Broadcasting...\n✅ {success} | 🚫 {blocked} | ❌ {failed} | {success+failed+blocked}/{total}"
                )
            except Exception:
                pass
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"📢 <b>Broadcast Complete!</b>\n\n"
        f"✅ Sent: <b>{success}</b>\n🚫 Blocked: <b>{blocked}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n📊 Total: <b>{total}</b>"
    )


# ═══════════════════════════════════════════════════════
#  /approve_pending COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("approve_pending") & filters.private)
async def approve_pending_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin!")
        return

    if not is_logged_in():
        await message.reply_text("❌ Pehle /login karo!")
        return

    chats = db.get_all_chats()
    if not chats:
        await message.reply_text("❌ Koi chat nahi! /addchat use karo.")
        return

    status_msg = await message.reply_text("⏳ <b>Checking pending requests...</b>")
    total_approved, total_errors, chat_results = await process_pending_requests(client)
    results_text = "\n".join(chat_results) if chat_results else "Koi result nahi."

    await status_msg.edit_text(
        f"📋 <b>Pending Requests:</b>\n\n{results_text}\n\n"
        f"─────────────────\n✅ Approved: <b>{total_approved}</b>\n❌ Errors: <b>{total_errors}</b>"
    )


# ═══════════════════════════════════════════════════════
#  /set_welcome COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("set_welcome") & filters.private)
async def set_welcome_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Sirf admin!")
        return

    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <code>/set_welcome 🎉 Welcome {first_name}! Aap {chat_title} mein join ho gaye!</code>"
        )
        return

    global WELCOME_MSG
    WELCOME_MSG = message.text.split(None, 1)[1]
    await message.reply_text(f"✅ <b>Updated!</b>\n\nPreview:\n{WELCOME_MSG}")


# ═══════════════════════════════════════════════════════
#  /cancel COMMAND
# ═══════════════════════════════════════════════════════

@app.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in login_state:
        temp_client = login_state[user_id].get("client")
        if temp_client:
            try:
                await temp_client.disconnect()
            except Exception:
                pass
        login_state.pop(user_id, None)
        await message.reply_text("❌ Login cancelled.")
    else:
        await message.reply_text("Koi active process nahi hai.")


# ═══════════════════════════════════════════════════════
#  LOGIN FLOW HANDLER - Phone, OTP, 2FA
# ═══════════════════════════════════════════════════════

@app.on_message(filters.private & filters.text & ~filters.command(
    ["start", "stats", "broadcast", "approve_pending", "set_welcome",
     "login", "logout", "addchat", "cancel"]
), group=0)
async def handle_login_flow(client: Client, message: Message):
    user_id = message.from_user.id

    if user_id not in login_state:
        # Not in login flow - just track user
        if message.from_user:
            db.add_user(user_id, message.from_user.first_name or "", message.from_user.username or "")
            db.set_user_blocked(user_id, False)
        return

    if not is_admin(user_id):
        return

    state = login_state[user_id]
    step = state.get("step")

    # ─── PHONE NUMBER ───
    if step == "phone":
        phone = message.text.strip()
        if not phone.startswith("+"):
            phone = "+" + phone

        status_msg = await message.reply_text("⏳ Sending OTP...")

        try:
            temp_client = Client(
                f"login_{user_id}_{int(time.time())}",
                api_id=API_ID,
                api_hash=API_HASH,
                in_memory=True,
            )
            await temp_client.connect()
            sent_code = await temp_client.send_code(phone)

            login_state[user_id] = {
                "step": "otp",
                "phone": phone,
                "client": temp_client,
                "phone_code_hash": sent_code.phone_code_hash,
            }

            await status_msg.edit_text(
                "📱 <b>OTP bhej diya!</b>\n\n"
                "Telegram pe OTP aaya hoga.\n"
                "OTP yahan bhejo:\n\n"
                "Example: <code>1 2 3 4 5</code> ya <code>12345</code>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")],
                ]),
            )

        except Exception as e:
            login_state.pop(user_id, None)
            await status_msg.edit_text(f"❌ Error: <code>{str(e)[:200]}</code>\n\n/login se phir try karo.")

    # ─── OTP ───
    elif step == "otp":
        otp = message.text.strip().replace(" ", "").replace("-", "")
        temp_client = state["client"]
        phone = state["phone"]
        phone_code_hash = state["phone_code_hash"]

        status_msg = await message.reply_text("⏳ Verifying OTP...")

        try:
            await temp_client.sign_in(
                phone_number=phone,
                phone_code_hash=phone_code_hash,
                phone_code=otp,
            )

            # Success!
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()

            db.save_session("userbot_session", session_string)
            success = await start_userbot_from_session(session_string)
            login_state.pop(user_id, None)

            if success:
                me = await userbot.get_me()
                await status_msg.edit_text(
                    f"✅ <b>Login Successful!</b>\n\n"
                    f"👤 <b>{me.first_name}</b> (ID: <code>{me.id}</code>)\n\n"
                    f"Ab /approve_pending kaam karega! 🎉",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Home", callback_data="back_start")],
                    ]),
                )
            else:
                await status_msg.edit_text("❌ Session start fail. /login se phir try karo.")

        except SessionPasswordNeeded:
            login_state[user_id]["step"] = "2fa"
            await status_msg.edit_text(
                "🔒 <b>2FA Password Required!</b>\n\n"
                "Apna <b>2FA password</b> bhejo:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")],
                ]),
            )

        except PhoneCodeInvalid:
            await status_msg.edit_text("❌ <b>Wrong OTP!</b> Sahi OTP dobara bhejo.")

        except PhoneCodeExpired:
            login_state.pop(user_id, None)
            try:
                await temp_client.disconnect()
            except Exception:
                pass
            await status_msg.edit_text("❌ <b>OTP Expired!</b> /login se phir try karo.")

        except Exception as e:
            login_state.pop(user_id, None)
            try:
                await temp_client.disconnect()
            except Exception:
                pass
            await status_msg.edit_text(f"❌ Error: <code>{str(e)[:200]}</code>\n\n/login se phir try karo.")

    # ─── 2FA PASSWORD ───
    elif step == "2fa":
        password = message.text.strip()
        temp_client = state["client"]

        try:
            await message.delete()
        except Exception:
            pass

        status_msg = await client.send_message(user_id, "⏳ Verifying 2FA...")

        try:
            await temp_client.check_password(password)

            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()

            db.save_session("userbot_session", session_string)
            success = await start_userbot_from_session(session_string)
            login_state.pop(user_id, None)

            if success:
                me = await userbot.get_me()
                await status_msg.edit_text(
                    f"✅ <b>Login Successful!</b>\n\n"
                    f"👤 <b>{me.first_name}</b> (ID: <code>{me.id}</code>)\n\n"
                    f"Ab /approve_pending kaam karega! 🎉",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Home", callback_data="back_start")],
                    ]),
                )
            else:
                await status_msg.edit_text("❌ Session start fail. /login se phir try karo.")

        except PasswordHashInvalid:
            await status_msg.edit_text("❌ <b>Wrong Password!</b> Sahi password dobara bhejo.")

        except Exception as e:
            login_state.pop(user_id, None)
            try:
                await temp_client.disconnect()
            except Exception:
                pass
            await status_msg.edit_text(f"❌ Error: <code>{str(e)[:200]}</code>\n\n/login se phir try karo.")


# ═══════════════════════════════════════════════════════
#  PROCESS PENDING REQUESTS (USERBOT)
# ═══════════════════════════════════════════════════════

async def process_pending_requests(bot_client: Client):
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
                    db.add_user(request.user.id, request.user.first_name or "", request.user.username or "")
                    db.log_approved_request(request.user.id, chat_id)
                    approved_count += 1

                    try:
                        bot_me = await bot_client.get_me()
                        await bot_client.send_message(
                            chat_id=request.user.id,
                            text=f"✅ <b>Request Approved!</b>\n\n🎉 <b>{request.user.first_name or 'User'}</b>, "
                                 f"aapki request <b>{chat_title}</b> mein approve ho gayi!\n\nWelcome! 🥳",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("🤖 Bot Start Karo",
                                                      url=f"https://t.me/{bot_me.username}?start=welcome")],
                            ]),
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

        except ChatAdminRequired:
            chat_results.append(f"❌ <b>{chat_title}</b>: Account admin nahi hai!")
            continue
        except Exception as e:
            chat_results.append(f"❌ <b>{chat_title}</b>: {str(e)[:80]}")
            continue

        total_approved += approved_count
        total_errors += error_count

        if approved_count > 0 or error_count > 0:
            chat_results.append(f"✅ <b>{chat_title}</b>: {approved_count} approved, {error_count} failed")
        else:
            chat_results.append(f"📭 <b>{chat_title}</b>: Koi pending request nahi")

    return total_approved, total_errors, chat_results


# ═══════════════════════════════════════════════════════
#  CALLBACKS
# ═══════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^help$"))
async def help_cb(client, callback):
    await callback.message.edit_text(
        "📖 <b>Commands:</b>\n\n"
        "/start - Bot start\n/stats - Statistics\n"
        "/broadcast - Broadcast (Admin)\n/approve_pending - Pending approve (Admin)\n"
        "/set_welcome - Welcome msg (Admin)\n/addchat - Chat add (Admin)\n"
        "/login - Account login (Admin)\n/logout - Account logout (Admin)\n\n"
        "📌 <b>Steps:</b>\n"
        "1️⃣ Bot add karo channel/group mein\n"
        "2️⃣ Admin banao (invite_users)\n"
        "3️⃣ Request to Join ON karo\n"
        "4️⃣ Auto approve chalu!\n\n"
        "⚠️ Purani pending ke liye /login → /approve_pending",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]),
    )
    await callback.answer()


@app.on_callback_query(filters.regex("^status$"))
async def status_cb(client, callback):
    active = db.get_user_count()
    blocked = db.get_blocked_count()
    total = db.get_total_user_count()
    chats = db.get_chat_count()
    approved = db.get_total_approved()

    await callback.message.edit_text(
        f"📊 <b>Statistics:</b>\n\n👥 Total: <b>{total}</b>\n✅ Active: <b>{active}</b>\n"
        f"🚫 Blocked: <b>{blocked}</b>\n💬 Chats: <b>{chats}</b>\n📋 Approved: <b>{approved}</b>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="status")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
        ]),
    )
    await callback.answer("✅ Updated!")


@app.on_callback_query(filters.regex("^back_start$"))
async def back_start_cb(client, callback):
    user = callback.from_user
    bot_me = await client.get_me()
    bot_username = bot_me.username

    if is_admin(user.id):
        login_status = "✅ Logged In" if is_logged_in() else "❌ Not Logged In"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Channel Add", url=f"https://t.me/{bot_username}?startchannel=true&admin=invite_users")],
            [InlineKeyboardButton("➕ Group Add", url=f"https://t.me/{bot_username}?startgroup=true&admin=invite_users")],
            [InlineKeyboardButton("📊 Status", callback_data="status"), InlineKeyboardButton("ℹ️ Help", callback_data="help")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_info"), InlineKeyboardButton("📋 Approve", callback_data="admin_approve_pending")],
            [InlineKeyboardButton("🔓 Logout" if is_logged_in() else "🔐 Login", callback_data="admin_logout" if is_logged_in() else "admin_login_info")],
        ])
        text = f"👋 <b>Admin {user.first_name}!</b>\n\n🤖 Request Approve Bot\n🔑 Account: {login_status}\n\n⬇️ Admin Panel"
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Channel Add", url=f"https://t.me/{bot_username}?startchannel=true&admin=invite_users")],
            [InlineKeyboardButton("➕ Group Add", url=f"https://t.me/{bot_username}?startgroup=true&admin=invite_users")],
            [InlineKeyboardButton("📊 Status", callback_data="status"), InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        ])
        text = f"👋 <b>Assalamu Alaikum {user.first_name}!</b>\n\n🤖 Request Approve Bot\n⬇️ Add karo!"

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@app.on_callback_query(filters.regex("^admin_broadcast_info$"))
async def broadcast_info_cb(client, callback):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return
    await callback.message.edit_text(
        "📢 <b>Broadcast:</b>\n\n1️⃣ Message likho\n2️⃣ Reply karo <code>/broadcast</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]),
    )
    await callback.answer()


@app.on_callback_query(filters.regex("^admin_approve_pending$"))
async def approve_pending_cb(client, callback):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return

    if not is_logged_in():
        await callback.answer()
        await callback.message.edit_text(
            "❌ <b>Account login nahi!</b>\n\n👉 /login karo pehle.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Login", callback_data="admin_login_info")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
            ]),
        )
        return

    chats = db.get_all_chats()
    if not chats:
        await callback.answer()
        await callback.message.edit_text(
            "❌ Koi chat nahi! <code>/addchat @username</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]),
        )
        return

    await callback.answer("⏳ Processing...")
    await callback.message.edit_text("⏳ <b>Checking...</b>")

    total_approved, total_errors, chat_results = await process_pending_requests(client)
    results_text = "\n".join(chat_results) if chat_results else "Koi result nahi."

    await callback.message.edit_text(
        f"📋 <b>Results:</b>\n\n{results_text}\n\n"
        f"─────────────────\n✅ Approved: <b>{total_approved}</b>\n❌ Errors: <b>{total_errors}</b>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Phir Check", callback_data="admin_approve_pending")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_start")],
        ]),
    )


@app.on_callback_query(filters.regex("^admin_login_info$"))
async def login_info_cb(client, callback):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        "🔐 <b>Account Login</b>\n\n"
        "👉 /login command use karo\n\n"
        "1️⃣ Phone number bhejo\n2️⃣ OTP bhejo\n3️⃣ 2FA (agar hai)\n4️⃣ Done! ✅",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]),
    )


@app.on_callback_query(filters.regex("^admin_logout$"))
async def logout_cb(client, callback):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        "🔓 <b>Logout?</b>\n\nPending approve band ho jayega.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Haan", callback_data="confirm_logout"), InlineKeyboardButton("❌ Nahi", callback_data="back_start")],
        ]),
    )


@app.on_callback_query(filters.regex("^confirm_logout$"))
async def confirm_logout_cb(client, callback):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only!", show_alert=True)
        return
    await stop_userbot()
    db.delete_session("userbot_session")
    await callback.answer("✅ Logged out!")
    await callback.message.edit_text(
        "✅ <b>Logout Done!</b>\n\nPhir login: /login",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Home", callback_data="back_start")]]),
    )


@app.on_callback_query(filters.regex("^cancel_login$"))
async def cancel_login_cb(client, callback):
    user_id = callback.from_user.id
    if user_id in login_state:
        temp = login_state[user_id].get("client")
        if temp:
            try:
                await temp.disconnect()
            except Exception:
                pass
        login_state.pop(user_id, None)
    await callback.answer("❌ Cancelled!")
    await callback.message.edit_text(
        "❌ Login cancelled. /login se phir try karo.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Home", callback_data="back_start")]]),
    )


# ═══════════════════════════════════════════════════════
#  AUTO APPROVE JOIN REQUESTS
# ═══════════════════════════════════════════════════════

@app.on_chat_join_request()
async def auto_approve(client, join_request: ChatJoinRequest):
    user = join_request.from_user
    chat = join_request.chat

    try:
        chat_type = chat.type.value if hasattr(chat.type, 'value') else str(chat.type)
        db.add_chat(chat.id, chat.title or "", chat_type)
        await join_request.approve()
        db.add_user(user.id, user.first_name or "", user.username or "")
        db.log_approved_request(user.id, chat.id)

        try:
            bot_me = await client.get_me()
            await client.send_message(
                chat_id=user.id,
                text=WELCOME_MSG.format(first_name=user.first_name or "User", chat_title=chat.title or "Chat"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 Bot Start", url=f"https://t.me/{bot_me.username}?start=welcome")],
                ]),
            )
        except Exception:
            pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await auto_approve(client, join_request)
    except Exception as e:
        logger.error(f"❌ {e}")


# ═══════════════════════════════════════════════════════
#  BOT ADDED/REMOVED
# ═══════════════════════════════════════════════════════

@app.on_message(filters.new_chat_members)
async def bot_added(client, message):
    bot_me = await client.get_me()
    for m in message.new_chat_members:
        if m.id == bot_me.id:
            chat = message.chat
            db.add_chat(chat.id, chat.title or "", chat.type.value if hasattr(chat.type, 'value') else str(chat.type))
            try:
                await message.reply_text(f"✅ <b>Active!</b> {chat.title}\n📌 Admin banao + invite_users do.")
            except Exception:
                pass


@app.on_chat_member_updated()
async def member_updated(client, update):
    try:
        if update.new_chat_member and update.new_chat_member.user:
            bot_me = await client.get_me()
            if update.new_chat_member.user.id == bot_me.id:
                s = update.new_chat_member.status
                if s in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.MEMBER]:
                    c = update.chat
                    db.add_chat(c.id, c.title or "", c.type.value if hasattr(c.type, 'value') else str(c.type))
                elif s in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
                    db.remove_chat(update.chat.id)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════
#  MAIN - Using pyrogram.idle() properly
# ═══════════════════════════════════════════════════════

async def main():
    logger.info("🔧 Initializing database...")
    db.init_db()

    # Restore saved session
    saved_session = db.get_session("userbot_session")
    if saved_session:
        logger.info("🔑 Restoring saved session...")
        success = await start_userbot_from_session(saved_session)
        if not success:
            logger.warning("⚠️ Saved session invalid")
            db.delete_session("userbot_session")

    # Start bot
    await app.start()
    bot_me = await app.get_me()
    logger.info(f"✅ Bot: @{bot_me.username}")
    logger.info(f"👤 Admin: {ADMIN_ID}")
    logger.info(f"🔑 Userbot: {'✅ Active' if is_logged_in() else '❌ Not logged in'}")
    logger.info("🟢 Bot is running!")

    # ★ This is the fix - pyrogram.idle() properly keeps bot alive ★
    await idle()

    # Cleanup on stop
    if userbot:
        await userbot.stop()
    await app.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
