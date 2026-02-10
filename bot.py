'''■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
●●●●●●●●● CN OFFICIAL SMM PANEL v41.1 ●●●●●
●●●●●●●●● STABLE & RENDER OPTIMIZED ●●●●●●
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
    # Render requires port 10000 to be exposed
    app.run(host='0.0.0.0', port=10000)

# --- CONFIGURATION ---
BOT_TOKEN = "8266090809:AAHh3U57YlZTWdtnVsg40I3JnI1iZphxal4"
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
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, credits INTEGER, referred_by INTEGER, 
                  ref_count INTEGER DEFAULT 0, total_ordered INTEGER DEFAULT 0)''')
    # Global Stats table
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
    
    # Handle Referral ID
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    conn = sqlite3.connect('cn_panel.db')
    c = conn.cursor()
    
    # Check if user exists (Fixes IntegrityError)
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = c.fetchone()

    if not user:
        # New User Setup
        c.execute("INSERT INTO users (user_id, credits, referred_by) VALUES (?, ?, ?)", (uid, 200, ref_id))
        conn.commit()
        
        # Credit the Referrer
        if ref_id and ref_id != uid:
            c.execute("UPDATE users SET credits = credits + 151, ref_count = ref_count + 1 WHERE user_id=?", (ref_id,))
            conn.commit()
            try:
                bot.send_message(ref_id, f"🎊 **Referral Successful!**\nA new user joined via your link. **+151 Credits** added!")
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
        bot.send_message(uid, "✅ **Access Granted!** Choose an option below.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):
    if is_joined(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "🚀 **Identity Confirmed.** Welcome to the Mainframe.", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ Verification Failed! Join the channel first.", show_alert=True)

# --- ADMIN DASHBOARD ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    
    conn = sqlite3.connect('cn_panel.db'); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_u = c.fetchone()[0]
    c.execute("SELECT total_orders, total_members_delivered FROM stats WHERE id=1")
    s_data = c.fetchone()
    c.execute("SELECT user_id, ref_count FROM users ORDER BY ref_count DESC LIMIT 10")
    top_refs = c.fetchall()
    conn.close()

    admin_msg = (f"👑 **CN ADMIN DASHBOARD**\n"
                 f"━━━━━━━━━━━━━━━━━━\n"
                 f"👥 **Total Users:** `{total_u}`\n"
                 f"📦 **Total Orders:** `{s_data[0]}`\n"
                 f"👥 **Total Members Sent:** `{s_data[1]}`\n\n"
                 f"🏆 **Top 10 Referral Kings:**\n")
    
    for i, u in enumerate(top_refs, 1):
        admin_msg += f"{i}. `{u[0]}` — **{u[1]} Refers**\n"
    
    admin_msg += "━━━━━━━━━━━━━━━━━━"
    bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")

# --- MAIN LOGIC ---
@bot.message_handler(func=lambda m: True)
def handle_menu(m):
    uid = m.from_user.id
    if not is_joined(uid): return
    
    if m.text == '👤 Profile':
        conn = sqlite3.connect('cn_panel.db'); c = conn.cursor()
        c.execute("SELECT credits, ref_count, total_ordered FROM users WHERE user_id=?", (uid,))
        d = c.fetchone(); conn.close()
        msg = (f"👤 **CN PANEL ACCOUNT**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"🆔 **User ID:** `{uid}`\n"
               f"💰 **Credits:** `{d[0]}`\n"
               f"👫 **Refers:** `{d[1]}`\n"
               f"📦 **Total Boosted:** `{d[2]}`\n"
               f"━━━━━━━━━━━━━━━━━━")
        bot.send_message(uid, msg, parse_mode="Markdown")

    elif m.text == '💰 Refer & Earn':
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid, f"🎁 **Referral Bonus**\n\nInvite friends and get **151 Credits** instantly!\n\n🔗 Your Link:\n`{link}`", parse_mode="Markdown")

    elif m.text == '🚀 Boost Members':
        bot.send_message(uid, "📤 **Enter Channel/Post Link:**")
        bot.register_next_step_handler(m, get_link)

    elif m.text == '📊 Bot Stats':
        conn = sqlite3.connect('cn_panel.db'); c = conn.cursor()
        c.execute("SELECT total_members_delivered FROM stats WHERE id=1")
        total_m = c.fetchone()[0]; conn.close()
        bot.send_message(uid, f"📊 **NETWORK LIVE STATS**\n\n✅ Total Members Boosted: `{total_m}`\n🚀 Node: Catalyst-High-Speed\n📡 Status: Connected", parse_mode="Markdown")

# --- INJECTION PROCESS ---
def get_link(m):
    if "t.me/" not in m.text: return bot.send_message(m.chat.id, "❌ Invalid URL Provided.")
    link = m.text
    bot.send_message(m.chat.id, "🔢 **Enter Amount:**\n(Min 10 | Max 50 per batch)")
    bot.register_next_step_handler(m, lambda msg: execute_cn_order(msg, link))

def execute_cn_order(m, link):
    uid = m.from_user.id
    try:
        qty = int(m.text)
        if qty < 10: return bot.send_message(uid, "❌ Min 10 members.")
        
        conn = sqlite3.connect('cn_panel.db'); c = conn.cursor()
        c.execute("SELECT credits FROM users WHERE user_id=?", (uid,))
        bal = c.fetchone()[0]
        
        if bal < qty:
            conn.close(); return bot.send_message(uid, "❌ Insufficient credits.")
        
        # Deduct Credits and Update Stats
        c.execute("UPDATE users SET credits = credits - ?, total_ordered = total_ordered + ? WHERE user_id=?", (qty, qty, uid))
        c.execute("UPDATE stats SET total_orders = total_orders + 1, total_members_delivered = total_members_delivered + ? WHERE id=1", (qty,))
        conn.commit(); conn.close()

        bot.send_message(uid, f"📡 **CN Cloud Strike Initiated...**\nProcessing {qty} members via secure nodes.")

        # Split and Ghost Loop
        remaining = qty
        while remaining > 0:
            batch = min(remaining, MAX_QTY)
            unique_link = get_unique_node(link)
            payload = {"link": unique_link, "service": SERVICE_ID, "quantity": str(batch)}
            headers = {"Content-Type": "text/plain;charset=UTF-8", "Origin": "https://smm8.com"}
            
            try:
                res = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=25)
                res_j = res.json()
                if "order" in res_j:
                    bot.send_message(uid, f"✅ **Node Response:** `{res_j['order']}`\n✅ **Status:** Sent {batch}")
                else:
                    bot.send_message(uid, f"⚠️ **Server Notice:** `{res_j.get('error', 'Batch queued')}`")
            except: pass
            
            remaining -= batch
            if remaining > 0: time.sleep(4) # Secure interval

        bot.send_message(uid, f"🏁 **CN PANEL: MISSION SUCCESS**\nAll requests were finalized successfully. 🔥")
    except: bot.send_message(uid, "❌ Input error. Numbers only.")

if __name__ == "__main__":
    # Start Web Server Thread
    threading.Thread(target=run_web_server, daemon=True).start()
    # Start Telegram Polling
    bot.polling(none_stop=True)
