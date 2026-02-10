'''■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
●●●●●●●●● CN OFFICIAL SMM PANEL v42.3 ●●●●●●
●●●●●●●●● BONUS & ADMIN CONTROLS ADDED ●●●●
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■'''

import telebot
import sqlite3
import requests
import json
import time
import random
import string
import threading
from flask import Flask
from telebot import types
from datetime import datetime, timedelta

# --- WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "CN SMM PANEL v42.3 ONLINE ⚡"

def run_web_server():
    app.run(host='0.0.0.0', port=10000)

# --- CONFIG ---
BOT_TOKEN = "8266090809:AAHh3U57YlZTWdtnVsg40I3JnI1iZphxal4"
ADMIN_ID = 7840042951
CHANNEL_USERNAME = "@CatalystMystery"
API_URL = "https://monadze.com/fgm/api.php"
SERVICE_ID = "30890"
MAX_QTY = 50 

bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE ---
def get_db():
    return sqlite3.connect('cn_panel_v4.db', check_same_thread=False)

def init_db():
    conn = get_db(); c = conn.cursor()
    # Table updated with last_bonus timestamp
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
def is_joined(user_id):
    try:
        s = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return s in ['member', 'administrator', 'creator']
    except: return False

def main_menu():
    m = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    m.add('👤 Profile', '🚀 Boost Members', '💰 Refer & Earn', '📊 Bot Stats', '🎁 Daily Bonus')
    return m

# --- START & VERIFY ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, credits, referred_by) VALUES (?, ?, ?)", (uid, 200, ref_id))
        if ref_id and ref_id != uid:
            c.execute("UPDATE users SET credits = credits + 151, ref_count = ref_count + 1 WHERE user_id=?", (ref_id,))
            try: bot.send_message(ref_id, "🎊 **Bonus!** Someone joined via your link. **+151 Credits** added.")
            except: pass
    conn.commit(); conn.close()

    flex_msg = (f"🛡️ **CN OFFICIAL SMM PANEL**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 **User:** catalyst | 🔑 **Pass:** mystery\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👋 Welcome, **{name}**!")
    
    if not is_joined(uid):
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/CatalystMystery"),
                                              types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_message(uid, flex_msg, reply_markup=kb)
    else:
        bot.send_message(uid, flex_msg, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):
    if is_joined(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "✅ Verified!", reply_markup=main_menu())
    else: bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True)

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['admin'])
def admin_report(message):
    if message.from_user.id != ADMIN_ID: return
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    t_users = c.fetchone()[0]
    c.execute("SELECT total_req, total_sent FROM stats WHERE id=1")
    t_req, t_sent = c.fetchone()
    c.execute("SELECT user_id, ref_count FROM users ORDER BY ref_count DESC LIMIT 10")
    top_ref = c.fetchall()
    conn.close()

    rep = (f"👑 **CN ADMIN CONTROL**\n"
           f"━━━━━━━━━━━━━━━━━━\n"
           f"👥 Total Users: `{t_users}`\n"
           f"📦 Total Requests: `{t_req}`\n"
           f"👥 Total Members Sent: `{t_sent}`\n\n"
           f"🏆 **Top 10 Referrers:**\n")
    for i, u in enumerate(top_ref, 1):
        rep += f"{i}. `{u[0]}` — {u[1]} Refers\n"
    bot.send_message(ADMIN_ID, rep, parse_mode="Markdown")

@bot.message_handler(commands=['adminsend'])
def admin_send(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id = int(args[1])
        amount = int(args[2])
        
        conn = get_db(); c = conn.cursor()
        c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, target_id))
        conn.commit(); conn.close()
        
        bot.send_message(ADMIN_ID, f"✅ **Success!** Sent {amount} credits to `{target_id}`.")
        bot.send_message(target_id, f"🎁 **Admin Gift!** You received `{amount}` credits from the System Admin.")
    except:
        bot.send_message(ADMIN_ID, "❌ Format: `/adminsend [userid] [amount]`")

# --- CORE LOGIC ---
@bot.message_handler(func=lambda m: True)
def handle_menu(m):
    uid = m.from_user.id
    if not is_joined(uid): return

    if m.text == '🎁 Daily Bonus':
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT last_bonus FROM users WHERE user_id=?", (uid,))
        last_b_str = c.fetchone()[0]
        last_b = datetime.strptime(last_b_str, '%Y-%m-%d %H:%M:%S')
        
        if datetime.now() > last_b + timedelta(days=1):
            reward = random.randint(10, 100)
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("UPDATE users SET credits = credits + ?, last_bonus = ? WHERE user_id=?", (reward, now_str, uid))
            conn.commit()
            bot.send_message(uid, f"🎊 **Daily Bonus Claimed!**\nYou received `{reward}` credits. Come back tomorrow!")
        else:
            wait_time = (last_b + timedelta(days=1)) - datetime.now()
            hours = int(wait_time.total_seconds() // 3600)
            bot.send_message(uid, f"⌛ **Wait Bhai!**\nYou already claimed today. Next bonus in `{hours}` hours.")
        conn.close()

    elif m.text == '👤 Profile':
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT credits, ref_count, total_boosted FROM users WHERE user_id=?", (uid,))
        d = c.fetchone(); conn.close()
        bot.send_message(uid, f"👤 **PROFILE**\n━━━━━━━━━\n💰 Credits: `{d[0]}`\n👫 Refers: `{d[1]}`\n📦 Total Boosted: `{d[2]}`")

    elif m.text == '🚀 Boost Members':
        bot.send_message(uid, "📤 **Enter Channel Link:**")
        bot.register_next_step_handler(m, process_link)

    elif m.text == '💰 Refer & Earn':
        bot_user = bot.get_me().username
        bot.send_message(uid, f"🎁 **Referral Program**\nEarn 151 Credits per invite!\n\n🔗 `https://t.me/{bot_user}?start={uid}`")

    elif m.text == '📊 Bot Stats':
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT total_sent FROM stats WHERE id=1")
        total_s = c.fetchone()[0]; conn.close()
        bot.send_message(uid, f"📊 **SMM LIVE STATS**\nTotal Members Boosted: `{total_s}`")

# --- PROCESSORS ---
def process_link(m):
    if "t.me/" not in m.text: return bot.send_message(m.chat.id, "❌ Invalid Link.")
    link = m.text.strip()
    bot.send_message(m.chat.id, "🔢 **Enter Amount:**")
    bot.register_next_step_handler(m, lambda msg: process_qty(msg, link))

def process_qty(m, link):
    uid = m.from_user.id
    clean_qty = "".join(filter(str.isdigit, m.text))
    if not clean_qty: return bot.send_message(uid, "❌ Numbers only.")
    
    qty = int(clean_qty)
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT credits FROM users WHERE user_id=?", (uid,))
    bal = c.fetchone()[0]
    
    if bal < qty:
        conn.close(); return bot.send_message(uid, "❌ Low Credits.")

    c.execute("UPDATE users SET credits = credits - ?, total_boosted = total_boosted + ? WHERE user_id=?", (qty, qty, uid))
    c.execute("UPDATE stats SET total_req = total_req + 1, total_sent = total_sent + ? WHERE id=1", (qty,))
    conn.commit(); conn.close()

    bot.send_message(uid, f"📡 **CN Cloud Strike Initiated!** Sending {qty} members...")
    threading.Thread(target=boost_engine, args=(uid, link, qty)).start()

def boost_engine(uid, link, total):
    rem = total
    while rem > 0:
        batch = min(rem, MAX_QTY)
        node_link = f"{link}{'&' if '?' in link else '?'}cn_node={random.randint(100,999)}"
        payload = {"link": node_link, "service": SERVICE_ID, "quantity": str(batch)}
        try:
            res = requests.post(API_URL, data=json.dumps(payload), timeout=25)
            if "order" in res.json():
                bot.send_message(uid, f"✅ **Batch OK!** Order ID: `{res.json()['order']}`")
        except: pass
        rem -= batch
        if rem > 0: time.sleep(4)
    bot.send_message(uid, "🏁 **ALL REQUESTS COMPLETED!**")

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.polling(none_stop=True)
