# 🚀 Fly.io pe Telegram Bot Deploy Karne Ka Complete Guide

---

## 📁 Folder Structure (4 Files Chahiye)

```
telegram-bot/
├── bot.py              ← Bot code
├── requirements.txt    ← Python packages
├── Dockerfile          ← Docker config
└── fly.toml            ← Fly.io config
```

Yeh saari 4 files maine de di hain. Bas download karo aur ek folder mein rakho.

---

## 🔧 Step-by-Step Guide

### Step 1: Fly CLI Install Karo

**Windows (PowerShell admin mode mein kholke):**
```
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

**Mac:**
```
brew install flyctl
```

**Linux:**
```
curl -L https://fly.io/install.sh | sh
```

Check karo install hua ya nahi:
```
fly version
```

---

### Step 2: Signup Karo

```
fly auth signup
```

- Browser khulega
- GitHub ya Email se sign up karo
- ⚠️ Agar credit card maange toh skip karo aur Render.com use karo

---

### Step 3: Project Folder Mein Jao

Terminal/CMD kholke apne folder mein jao:

```
cd telegram-bot
```

(Jahan tumne 4 files rakhi hain)

---

### Step 4: App Launch Karo

```
fly launch
```

Yeh kuch sawal puchega:

```
? Choose an app name: telegram-approve-bot     ← Koi bhi naam do
? Choose a region: sin (Singapore)             ← Nearest select karo
? Would you like to set up a Postgresql database? No
? Would you like to set up an Upstash Redis database? No
? Would you like to deploy now? No             ← Abhi No bolo!
```

---

### Step 5: Bot Token Secret Mein Set Karo

```
fly secrets set BOT_TOKEN=tumhara_bot_token_yahan
```

Example:
```
fly secrets set BOT_TOKEN=7123456789:AAHxyz123abc456def789ghi
```

⚠️ Token ke around quotes MAT lagao!

---

### Step 6: Deploy Karo 🚀

```
fly deploy
```

- Yeh 2-3 minute lagega
- Docker image build hoga
- Bot deploy ho jayega

Output aisa dikhega:
```
==> Building image
...
==> Pushing image
...
==> Creating release
--> v1 deployed successfully
```

---

### Step 7: Check Karo Bot Chal Raha Hai

```
fly status
```

Output:
```
App: telegram-approve-bot
Status: running          ← ✅ Yeh dikhna chahiye
```

Logs dekhne ke liye:
```
fly logs
```

---

## 🛠️ Useful Commands

| Command | Kya Karta Hai |
|---------|--------------|
| `fly status` | Bot ka status dekho |
| `fly logs` | Live logs dekho |
| `fly secrets list` | Set ki hui secrets dekho |
| `fly secrets set BOT_TOKEN=xxx` | Token update karo |
| `fly deploy` | Naya code deploy karo |
| `fly apps restart` | Bot restart karo |
| `fly apps destroy telegram-approve-bot` | App delete karo |
| `fly scale count 1` | 1 instance chalaao |

---

## ❓ Common Issues & Fixes

### ❌ "Error: could not find a running machine"
```
fly scale count 1
fly deploy
```

### ❌ "Out of memory"
```
fly scale memory 512
```

### ❌ "Unauthorized" bot error
- @BotFather se naya token lo
- `fly secrets set BOT_TOKEN=naya_token`
- `fly deploy`

### ❌ Token change karna hai
```
fly secrets set BOT_TOKEN=naya_token_yahan
```
(Automatically redeploy ho jayega)

### ❌ Credit card maang raha hai
- Fly.io ka free tier ab card maangta hai (charge nahi karta)
- Agar card nahi dena toh **Render.com** use karo

---

## 💡 Tips

1. **Logs hamesha check karo** issue hone pe: `fly logs`
2. **Token kabhi code mein mat likho** — hamesha `fly secrets` use karo
3. **Region Singapore (sin)** rakho — Asia ke liye fast hai
4. Bot update karna ho toh `bot.py` edit karo aur `fly deploy` chala do

---

*Guide complete! Koi issue aaye toh pooch lo! 💪*
