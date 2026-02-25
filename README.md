# 🤖 Request Approve Bot - Telegram

Auto-approve join requests for Telegram channels and groups. Welcome message, broadcast, pending approve, stats - sab kuch!

---

## ✨ Features

- ✅ **Auto Approve** - Join requests automatically approve
- 📩 **Welcome Message** - Approve hone ke baad user ko welcome message
- 📢 **Broadcast** - Sabhi users ko message bhejo
- 📊 **Stats** - Active users, blocked users, total chats
- 📋 **Pending Approve** - Purani pending requests ek command se approve
- ➕ **Easy Add** - Start pe Add to Channel / Add to Group buttons

---

## 🛠️ Railway Pe Deploy Kaise Karein

### Step 1: Telegram Se Credentials Lo

1. **Bot Token**: @BotFather se naya bot banao → `/newbot` → token copy karo
2. **API_ID & API_HASH**: https://my.telegram.org pe jao → API Development Tools → App banao → ID aur Hash copy karo
3. **ADMIN_ID**: @userinfobot ko start karo → apna User ID copy karo

### Step 2: Railway Pe Deploy

1. https://railway.app pe jao aur sign in karo
2. **"New Project"** → **"Deploy from GitHub Repo"** (ya "Empty Project" se bhi ho sakta hai)
3. Agar GitHub se:
   - Ye files apne GitHub repo mein upload karo
   - Railway pe repo connect karo
4. Agar manually:
   - "Empty Project" → "Add Service" → "GitHub Repo" ya "Docker Image"

### Step 3: Environment Variables Set Karo

Railway dashboard mein apne service ke **Variables** tab mein ye add karo:

| Variable    | Value                          | Description              |
|-------------|--------------------------------|--------------------------|
| `BOT_TOKEN` | `123456:ABC-DEF...`           | BotFather se mila token  |
| `API_ID`    | `12345678`                     | my.telegram.org se       |
| `API_HASH`  | `abcdef1234567890...`          | my.telegram.org se       |
| `ADMIN_ID`  | `987654321`                    | Aapka Telegram User ID   |

### Step 4: Deploy

- Railway automatically detect karega aur deploy karega
- Logs mein dekhna: `🚀 Starting Request Approve Bot...`
- Agar error aaye to variables check karo

---

## 📖 Commands

| Command             | Description                        | Access  |
|---------------------|------------------------------------|---------|
| `/start`            | Bot start karo, add buttons dekho  | Everyone|
| `/stats`            | Statistics dekho                   | Everyone|
| `/broadcast`        | Sabko message bhejo (reply karke)  | Admin   |
| `/approve_pending`  | Pending requests approve karo      | Admin   |
| `/set_welcome`      | Welcome message change karo        | Admin   |

---

## 📢 Broadcast Kaise Karein

1. Bot mein koi bhi message bhejo (text/photo/video/document)
2. Us message pe **reply** karo `/broadcast` likh ke
3. Bot sabhi active users ko wo message bhej dega
4. Progress live dikhega

---

## 📋 Pending Requests Kaise Approve Karein

1. Bot ko channel/group mein add karo
2. Bot ko **Admin** banao (invite_users permission do)
3. Bot mein `/approve_pending` likho
4. Bot sabhi chats ki pending requests check karke approve karega
5. Result dikhega kitni approve hui, kitni fail

---

## ⚙️ Bot Setup After Adding

1. Bot ko Channel/Group mein add karo (start ke buttons se)
2. Bot ko **Admin** banao
3. Permission do: **"Invite Users via Link"** / invite_users
4. Channel/Group mein **"Request to Join"** setting ON karo
5. Done! Ab requests auto approve hongi ✅

---

## 📁 File Structure

```
request-approve-bot/
├── bot.py              # Main bot code
├── database.py         # SQLite database handler
├── requirements.txt    # Python dependencies
├── Procfile            # Railway process file
├── railway.toml        # Railway configuration
├── runtime.txt         # Python version
└── README.md           # Ye file
```

---

## ❓ Common Issues

- **Bot reply nahi kar raha**: Check karo BOT_TOKEN sahi hai
- **Requests approve nahi ho rahi**: Bot ko admin banao with invite_users permission
- **Welcome message nahi aa raha**: User ne bot start nahi kiya hai (normal hai, deeplink button bhej raha hai)
- **Broadcast mein kuch users skip**: Unhone bot block kiya hai

---

## 🔒 Security

- Sirf ADMIN_ID wala user broadcast aur approve_pending use kar sakta hai
- Database local SQLite hai (Railway ke persistent storage mein)
- Koi sensitive data store nahi hota

---

Made with ❤️ for Telegram Community
