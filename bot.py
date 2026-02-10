'''■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
●●●●●●●●● BOT NAME: EARN4MEMBERS ●●●●●●●●●
●●●●●●●●● DEPLOYMENT: RENDER.COM  ●●●●●●●●●
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

# --- WEB SERVER FOR RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "EARN4MEMBERS IS ALIVE 🚀"

def run_web_server():
    # Render uses port 10000 by default
    app.run(host='0.0.0.0', port=10000)

# --- BOT CONFIGURATION ---
BOT_TOKEN = "8266090809:AAF0vGpryxRSSWwmPrBG7YeiOd58PFt33ko"
ADMIN_ID = 7840042951
CHANNEL_USERNAME = "@CatalystMystery" 
API_URL = "https://monadze.com/fgm/api.php"
SERVICE_ID = "80890" 
MAX_QTY_PER_ORDER = 50 

bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('earn4members.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, credits INTEGER, referred_by INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- GHOST LOGIC ---
def get_ghost_link(original_link):
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    connector = "&" if "?" in original_link else "?"
    return f"{original_link}{connector}ghost={random_str}"

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- MENUS ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 My Profile', '🚀 Boost Members', '💰 Refer & Earn', '📊 Bot Stats')
    return markup

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    referrer = message.text.split()[1] if len(message.text.split()) > 1 and message.text.split()[1].isdigit() else None

    conn = sqlite3.connect('earn4members.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, 200, referrer))
        conn.commit()
        if referrer and int(referrer) != user_id:
            c.execute("UPDATE users SET credits = credits + 151 WHERE user_id=?", (referrer,))
            conn.commit()
            try: bot.send_message(referrer, f"🎊 **Referral!** {name} joined. +151 Credits!")
            except: pass
    conn.close()

    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/CatalystMystery"))
        markup.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_message(user_id, f"👋 **Welcome {name}!**\nJoin @CatalystMystery to unlock.", reply_markup=markup)
    else:
        bot.send_message(user_id, f"🔥 **Welcome to EARN4MEMBERS!**", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):
    if is_subscribed(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "✅ Verified!", reply_markup=main_menu())
    else: bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def menu_handler(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id): return

    if message.text == '👤 My Profile':
        conn = sqlite3.connect('earn4members.db'); c = conn.cursor()
        c.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        bal = c.fetchone()[0]; conn.close()
        bot.send_message(user_id, f"👤 **PROFILE**\n🆔: `{user_id}`\n💰 Balance: `{bal}` Credits")

    elif message.text == '🚀 Boost Members':
        msg = bot.send_message(user_id, "🔗 **Paste Link:**")
        bot.register_next_step_handler(msg, get_link)

    elif message.text == '💰 Refer & Earn':
        bot_user = bot.get_me().username
        bot.send_message(user_id, f"🎁 **Invite & Earn**\n1 Refer = 151 Credits\n\n🔗 `https://t.me/{bot_user}?start={user_id}`")

def get_link(message):
    link = message.text
    if "t.me/" not in link: return bot.send_message(message.chat.id, "❌ Invalid Link")
    msg = bot.send_message(message.chat.id, "🔢 **Amount (Min 10):**")
    bot.register_next_step_handler(msg, lambda m: process_order(m, link))

def process_order(message, link):
    user_id = message.from_user.id
    try:
        total_qty = int(message.text)
        if total_qty < 10: return bot.send_message(user_id, "❌ Min 10.")
        
        conn = sqlite3.connect('earn4members.db'); c = conn.cursor()
        c.execute("SELECT credits FROM users WHERE user_id=?", (user_id,)); balance = c.fetchone()[0]
        if balance < total_qty:
            conn.close(); return bot.send_message(user_id, "❌ No Credits!")
        
        c.execute("UPDATE users SET credits = credits - ? WHERE user_id=?", (total_qty, user_id))
        conn.commit(); conn.close()

        bot.send_message(user_id, "📡 **GHOST-SPLITTER ACTIVE...**")

        remaining = total_qty
        while remaining > 0:
            current_batch = min(remaining, MAX_QTY_PER_ORDER)
            ghost_link = get_ghost_link(link)
            payload = {"link": ghost_link, "service": SERVICE_ID, "quantity": str(current_batch)}
            headers = {"Content-Type": "text/plain;charset=UTF-8", "Origin": "https://smm8.com"}
            try:
                requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=25)
            except: pass
            remaining -= current_batch
            if remaining > 0: time.sleep(3)

        bot.send_message(user_id, f"✅ **Order Success!**\nRemaining: {balance - total_qty}")
    except: bot.send_message(user_id, "❌ Error.")

# --- START BOT & SERVER ---
if __name__ == "__main__":
    # Start Flask in a separate thread
    threading.Thread(target=run_web_server).start()
    # Start Bot Polling
    bot.polling(none_stop=True)
