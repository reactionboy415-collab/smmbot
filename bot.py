'''■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
●●●●●●●●● CN OFFICIAL SMM PANEL v41 ●●●●●●
●●●●●●●●● POWERED BY @dex4dev       ●●●●●●
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

# --- WEB SERVER (RENDER EXPOSURE) ---
app = Flask(__name__)
@app.route('/')
def home(): return "CN SMM PANEL IS ONLINE ⚡"

def run_web_server():
    app.run(host='0.0.0.0', port=10000)

# --- CONFIGURATION ---
BOT_TOKEN = "8266090809:AAF4B3NFzkuT-_8zvvH33fumUg64VG8Scew"
ADMIN_ID = 7840042951
CHANNEL_USERNAME = "@CatalystMystery"
API_URL = "https://monadze.com/fgm/api.php"
SERVICE_ID = "30890"
MAX_QTY = 50 

bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('cn_panel.db', check_same_thread=False)
    c = conn.cursor()
    # Users table with referral count and total ordered members
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, credits INTEGER, referred_by INTEGER, 
                  ref_count INTEGER DEFAULT 0, total_ordered INTEGER DEFAULT 0)''')
    # Stats table for global tracking
    c.execute('''CREATE TABLE IF NOT EXISTS stats 
                 (id INTEGER PRIMARY KEY, total_orders INTEGER DEFAULT 0, 
                  total_members_delivered INTEGER DEFAULT 0)''')
    c.execute("INSERT OR IGNORE INTO stats (id, total_orders, total_members_delivered) VALUES (1, 0, 0)")
    conn.commit()
    conn.close()

init_db()

# --- UTILS ---
def get_unique_node(link):
    node = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    sep = "&" if "?" in link else "?"
    return f"{link}{sep}cn_node={node}"

def is_joined(user_id):
    try:
        s = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return s in ['member', 'administrator', 'creator']
    except: return False

# --- KEYBOARDS ---
def main_menu():
    m = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    m.add('👤 Profile', '🚀 Boost Members', '💰 Refer & Earn', '📊 Bot Stats')
    return m

# --- START HANDLER ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    ref_id = message.text.split()[1] if len(message.text.split()) > 1 and message.text.split()[1].isdigit() else None
    
    conn = sqlite3.connect('cn_panel.db'); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = c.fetchone()

    if not user:
        c.execute("INSERT INTO users (user_id, credits, referred_by) VALUES (?, ?, ?)", (uid, 200, ref_id))
        conn.commit()
        if ref_id and int(ref_id) != uid:
            c.execute("UPDATE users SET credits = credits + 151, ref_count = ref_count + 1 WHERE user_id=?", (ref_id,))
            conn.commit()
            try: bot.send_message(ref_id, f"🎊 **Referral Success!**\nNew user joined. **+151 Credits** added to your account!")
            except: pass
    conn.close()

    flex_msg = (f"🛡️ **CN OFFICIAL SMM PANEL**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Username:** `catalyst` (Encrypted)\n"
                f"🔑 **Password:** `********` (Verified)\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👋 Welcome, **{name}**! Your access is being verified via Catalyst Cloud.")
    
    if not is_joined(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/CatalystMystery"))
        kb.add(types.InlineKeyboardButton("✅ Verify Identity", callback_data="verify"))
        bot.send_message(uid, flex_msg, parse_mode="Markdown")
        bot.send_message(uid, "⚠️ **Security Check:** Join the official channel to bypass the firewall.", reply_markup=kb)
    else:
        bot.send_message(uid, flex_msg, parse_mode="Markdown")
        bot.send_message(uid, "✅ **Access Granted!** Choose an option from the menu.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):
    if is_joined(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "✅ **Verification Successful!** Welcome to CN SMM Panel.", reply_markup=main_menu())
    else: bot.answer_callback_query(call.id, "❌ Verification Failed! Join the channel first.", show_alert=True)

# --- ADMIN PANEL COMMAND ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    
    conn = sqlite3.connect('cn_panel.db'); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT total_orders, total_members_delivered FROM stats WHERE id=1")
    s_data = c.fetchone()
    c.execute("SELECT user_id, ref_count FROM users ORDER BY ref_count DESC LIMIT 10")
    top_refs = c.fetchall()
    conn.close()

    admin_msg = (f"👑 **CN ADMIN DASHBOARD**\n"
                 f"━━━━━━━━━━━━━━━━━━\n"
                 f"👥 **Total Users:** `{total_users}`\n"
                 f"📦 **Total Requests:** `{s_data[0]}`\n"
                 f"👥 **Total Members Sent:** `{s_data[1]}`\n\n"
                 f"🏆 **Top 10 Referral Kings:**\n")
    
    for i, user in enumerate(top_refs, 1):
        admin_msg += f"{i}. User ID: `{user[0]}` - **{user[1]} Refers**\n"
    
    admin_msg += "━━━━━━━━━━━━━━━━━━"
    bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")

# --- MAIN MENU HANDLERS ---
@bot.message_handler(func=lambda m: True)
def handle_menu(m):
    uid = m.from_user.id
    if not is_joined(uid): return
    
    if m.text == '👤 Profile':
        conn = sqlite3.connect('cn_panel.db'); c = conn.cursor()
        c.execute("SELECT credits, ref_count, total_ordered FROM users WHERE user_id=?", (uid,))
        data = c.fetchone(); conn.close()
        profile_msg = (f"👤 **CN PANEL ACCOUNT**\n"
                       f"━━━━━━━━━━━━━━━━━━\n"
                       f"🆔 **User ID:** `{uid}`\n"
                       f"💰 **Credits:** `{data[0]}`\n"
                       f"👫 **Refers:** `{data[1]}`\n"
                       f"📦 **Total Boosted:** `{data[2]}` Members\n"
                       f"━━━━━━━━━━━━━━━━━━")
        bot.send_message(uid, profile_msg, parse_mode="Markdown")

    elif m.text == '💰 Refer & Earn':
        bot_user = bot.get_me().username
        bot.send_message(uid, f"🎁 **Referral Program**\nEarn **151 Credits** per friend!\n\n🔗 `https://t.me/{bot_user}?start={uid}`", parse_mode="Markdown")

    elif m.text == '🚀 Boost Members':
        bot.send_message(uid, "📤 **Enter Channel Link:**")
        bot.register_next_step_handler(m, get_link)

    elif m.text == '📊 Bot Stats':
        conn = sqlite3.connect('cn_panel.db'); c = conn.cursor()
        c.execute("SELECT total_members_delivered FROM stats WHERE id=1")
        total_m = c.fetchone()[0]; conn.close()
        bot.send_message(uid, f"📊 **LIVE STATS**\n\n✅ Total Members Boosted: `{total_m}`\n🚀 Node Speed: Instant\n📡 Status: Connected", parse_mode="Markdown")

# --- ORDER EXECUTION ---
def get_link(m):
    if "t.me/" not in m.text: return bot.send_message(m.chat.id, "❌ Invalid URL Provided.")
    link = m.text
    bot.send_message(m.chat.id, "🔢 **Enter Amount:**\n(Min 10 | Max per batch 50)")
    bot.register_next_step_handler(m, lambda msg: execute_cn_order(msg, link))

def execute_cn_order(m, link):
    uid = m.from_user.id
    try:
        qty = int(m.text)
        if qty < 10: return bot.send_message(uid, "❌ Minimum 10 members required.")
        
        conn = sqlite3.connect('cn_panel.db'); c = conn.cursor()
        c.execute("SELECT credits FROM users WHERE user_id=?", (uid,))
        bal = c.fetchone()[0]
        if bal < qty:
            conn.close(); return bot.send_message(uid, "❌ Insufficient credits.")
        
        c.execute("UPDATE users SET credits = credits - ?, total_ordered = total_ordered + ? WHERE user_id=?", (qty, qty, uid))
        c.execute("UPDATE stats SET total_orders = total_orders + 1, total_members_delivered = total_members_delivered + ? WHERE id=1", (qty,))
        conn.commit(); conn.close()

        bot.send_message(uid, f"📡 **CN Cloud Strike Initiated...**\nProcessing {qty} members via secure nodes.")

        remaining = qty
        while remaining > 0:
            batch = min(remaining, MAX_QTY)
            unique_link = get_unique_node(link)
            payload = {"link": unique_link, "service": SERVICE_ID, "quantity": str(batch)}
            headers = {"Content-Type": "text/plain;charset=UTF-8", "Origin": "https://smm8.com"}
            try:
                res = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=25)
                res_json = res.json()
                if "order" in res_json:
                    bot.send_message(uid, f"✅ **Batch OK!**\nNode ID: `{res_json['order']}`\nSent: {batch}")
                else:
                    bot.send_message(uid, f"⚠️ **Server Notice:** `{res_json.get('error', 'Limit reached')}`")
            except: pass
            remaining -= batch
            if remaining > 0: time.sleep(3)

        bot.send_message(uid, f"🏁 **CN PANEL: MISSION SUCCESS**\nAll requests processed. Enjoy your members! 🔥")
    except: bot.send_message(uid, "❌ Numbers only.")

if __name__ == "__main__":
    threading.Thread(target=run_web_server).start()
    bot.polling(none_stop=True)
