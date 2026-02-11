import telebot
import sqlite3
import requests
import json
import time
import random
import threading
import os
import base64
from flask import Flask
from telebot import types
from datetime import datetime, timedelta

# --- CONFIGURATION (STRICT) ---
BOT_TOKEN = "8266090809:AAHh3U57YlZTWdtnVsg40I3JnI1iZphxal4"
ADMIN_ID = 7840042951
CHANNEL_USERNAME = "@CatalystMystery"
API_URL = "https://monadze.com/fgm/api.php"
SERVICE_ID = "30890"

# --- GITHUB PERSISTENCE ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = "reactionboy415-collab/smmbot"
DB_FILE_NAME = "cn_panel.db"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# --- GITHUB SYNC ENGINE ---
def sync_db(mode="download"):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{DB_FILE_NAME}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    if mode == "download":
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                content = base64.b64decode(res.json()['content'])
                with open(DB_FILE_NAME, 'wb') as f: f.write(content)
                print("✅ [GITHUB] Database Downloaded")
            else: print("⚠️ [GITHUB] No DB found, creating fresh.")
        except: print("❌ [GITHUB] Sync Failed")
            
    elif mode == "upload":
        try:
            if not os.path.exists(DB_FILE_NAME): return
            res = requests.get(url, headers=headers)
            sha = res.json()['sha'] if res.status_code == 200 else None
            with open(DB_FILE_NAME, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            data = {"message": f"Sync {datetime.now()}", "content": content, "branch": "main"}
            if sha: data["sha"] = sha
            requests.put(url, headers=headers, data=json.dumps(data))
            print("☁️ [GITHUB] Backup Successful")
        except: print("❌ [GITHUB] Upload Failed")

# --- DATABASE ENGINE ---
def get_db(): return sqlite3.connect(DB_FILE_NAME, check_same_thread=False)

def init_db():
    sync_db("download")
    conn = get_db(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, credits INTEGER, referred_by INTEGER, 
                  ref_count INTEGER DEFAULT 0, total_boosted INTEGER DEFAULT 0, 
                  last_bonus TEXT DEFAULT '2000-01-01 00:00:00')''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats 
                 (id INTEGER PRIMARY KEY, total_req INTEGER DEFAULT 0, total_sent INTEGER DEFAULT 0)''')
    c.execute("INSERT OR IGNORE INTO stats VALUES (1, 0, 0)")
    conn.commit(); conn.close()

init_db()

# --- UTILS ---
def is_joined(uid):
    try:
        s = bot.get_chat_member(CHANNEL_USERNAME, uid).status
        return s in ['member', 'administrator', 'creator']
    except: return False

def main_kb():
    m = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    m.add('👤 Profile', '🚀 Boost Members', '💰 Refer & Earn', '📊 Bot Stats', '🎁 Daily Bonus')
    return m

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    u_count = c.fetchone()[0]
    c.execute("SELECT total_req, total_sent FROM stats WHERE id=1")
    t_req, t_sent = c.fetchone()
    conn.close()
    
    rep = (f"👑 **CN ADMIN CONTROL**\n"
           f"━━━━━━━━━━━━━━━━━━\n"
           f"👥 Total Users: `{u_count}`\n"
           f"📦 Total Requests: `{t_req}`\n"
           f"👥 Total Members: `{t_sent}`\n\n"
           f"Commands:\n"
           f"• `/broadcast [msg]`\n"
           f"• `/adminsend [id] [amt]`")
    bot.reply_to(message, rep)

@bot.message_handler(commands=['broadcast'])
def b_cast(message):
    if message.from_user.id != ADMIN_ID: return
    txt = message.text.replace("/broadcast", "").strip()
    if not txt: return bot.send_message(ADMIN_ID, "❌ Format: `/broadcast Hello` ")
    conn = get_db(); users = conn.execute("SELECT user_id FROM users").fetchall(); conn.close()
    bot.send_message(ADMIN_ID, f"🚀 Sending to {len(users)} users...")
    for u in users:
        try: bot.send_message(u[0], txt); time.sleep(0.1)
        except: continue
    bot.send_message(ADMIN_ID, "✅ Broadcast Done")

@bot.message_handler(commands=['adminsend'])
def a_send(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        conn = get_db(); c = conn.cursor()
        c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amt, tid))
        conn.commit(); conn.close()
        bot.send_message(tid, f"🎁 Admin sent you `{amt}` credits!")
        bot.send_message(ADMIN_ID, f"✅ Sent {amt} credits to {tid}")
        threading.Thread(target=sync_db, args=("upload",)).start()
    except: bot.send_message(ADMIN_ID, "❌ Format: `/adminsend id amt`")

# --- USER HANDLERS ---
@bot.message_handler(commands=['start'])
def welcome(message):
    uid = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    conn = get_db(); c = conn.cursor()
    if not c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone():
        c.execute("INSERT INTO users (user_id, credits, referred_by) VALUES (?, 200, ?)", (uid, ref_id))
        if ref_id and ref_id != uid:
            c.execute("UPDATE users SET credits = credits + 151, ref_count = ref_count + 1 WHERE user_id=?", (ref_id,))
            try: bot.send_message(ref_id, "🎊 **Bonus!** Your friend joined. **+151 Credits** added.")
            except: pass
        conn.commit()
        threading.Thread(target=sync_db, args=("upload",)).start()
    conn.close()

    if not is_joined(uid):
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")).add(types.InlineKeyboardButton("✅ Verify", callback_data="v"))
        bot.send_message(uid, "🛡️ **CN PANEL ACCESS**\nJoin our channel to unlock the bot.", reply_markup=kb)
    else: bot.send_message(uid, "🔥 **Welcome to CN SMM!**", reply_markup=main_kb())

@bot.callback_query_handler(func=lambda c: c.data == "v")
def verify(call):
    if is_joined(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "✅ Verified!", reply_markup=main_kb())
    else: bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)

@bot.message_handler(func=lambda m: True)
def menu_logic(m):
    uid = m.from_user.id
    if not is_joined(uid): return

    if m.text == '🎁 Daily Bonus':
        conn = get_db(); c = conn.cursor()
        user_data = c.execute("SELECT last_bonus FROM users WHERE user_id=?", (uid,)).fetchone()
        last_b = datetime.strptime(user_data[0], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > last_b + timedelta(days=1):
            reward = random.randint(10, 200)
            c.execute("UPDATE users SET credits = credits + ?, last_bonus = ? WHERE user_id=?", (reward, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), uid))
            conn.commit(); bot.send_message(uid, f"🎁 **Bonus Claimed!** You received `{reward}` credits.")
            threading.Thread(target=sync_db, args=("upload",)).start()
        else:
            diff = (last_b + timedelta(days=1)) - datetime.now()
            bot.send_message(uid, f"⌛ Wait `{int(diff.total_seconds()//3600)}` hours for your next bonus.")
        conn.close()

    elif m.text == '👤 Profile':
        conn = get_db(); d = conn.execute("SELECT credits, ref_count, total_boosted FROM users WHERE user_id=?", (uid,)).fetchone(); conn.close()
        bot.send_message(uid, f"👤 **USER PROFILE**\n━━━━━━━━━━\n💰 Balance: `{d[0]}`\n👫 Refers: `{d[1]}`\n📦 Total Boosted: `{d[2]}`")

    elif m.text == '📊 Bot Stats':
        conn = get_db(); s = conn.execute("SELECT total_sent FROM stats WHERE id=1").fetchone()[0]; conn.close()
        bot.send_message(uid, f"📊 **CN GLOBAL STATS**\nTotal Delivered: `{s}`\nStorage: GitHub Secure Cloud ✅")

    elif m.text == '💰 Refer & Earn':
        bot.send_message(uid, f"🎁 Share with friends!\nGet **151 Credits** per referral.\n\n🔗 `https://t.me/{bot.get_me().username}?start={uid}`")

    elif m.text == '🚀 Boost Members':
        bot.send_message(uid, "📤 **Step 1: Send Channel Link**\nExample: `https://t.me/CatalystMystery` ")
        bot.register_next_step_handler(m, get_qty)

# --- ENGINE ---
def get_qty(m):
    if "t.me/" not in m.text: return bot.send_message(m.chat.id, "❌ Invalid link.")
    link = m.text.strip()
    bot.send_message(m.chat.id, "🔢 **Step 2: Enter Amount**\n(Numbers only, min 10)")
    bot.register_next_step_handler(m, lambda msg: process_order(msg, link))

def process_order(m, link):
    uid = m.from_user.id
    qty_str = "".join(filter(str.isdigit, m.text))
    if not qty_str: return bot.send_message(uid, "❌ Numbers only!")
    qty = int(qty_str)
    
    conn = get_db(); c = conn.cursor()
    bal = c.execute("SELECT credits FROM users WHERE user_id=?", (uid,)).fetchone()[0]
    if bal < qty: conn.close(); return bot.send_message(uid, "❌ Insufficient credits.")
    
    c.execute("UPDATE users SET credits = credits - ?, total_boosted = total_boosted + ? WHERE user_id=?", (qty, qty, uid))
    c.execute("UPDATE stats SET total_req = total_req + 1, total_sent = total_sent + ? WHERE id=1", (qty,))
    conn.commit(); conn.close()
    
    bot.send_message(uid, f"📡 **Strike Initiated!** Queued `{qty}` members.")
    threading.Thread(target=engine, args=(uid, link, qty)).start()
    threading.Thread(target=sync_db, args=("upload",)).start()

def engine(uid, link, total):
    rem = total
    while rem > 0:
        batch = min(rem, 20)
        try:
            requests.post(API_URL, data=json.dumps({"link": f"{link}?p={random.randint(1,99)}", "service": SERVICE_ID, "quantity": str(batch)}), timeout=12)
        except: pass
        rem -= batch
        time.sleep(6)
    bot.send_message(uid, "🏁 **CN MISSION COMPLETE!** All members delivered.")

# --- SERVER ---
@app.route('/')
def h(): return "CN SMM v45.1 ACTIVE"

if __name__ == "__main__":
    # Persistence thread (every 10 mins)
    def backup_loop():
        while True:
            time.sleep(600)
            sync_db("upload")
    
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    threading.Thread(target=backup_loop, daemon=True).start()
    print("🚀 Bot Started Successfully!")
    bot.polling(none_stop=True)
