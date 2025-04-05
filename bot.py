from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
from flask import Flask
import threading

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("ForwardBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_settings = {}
SETTINGS_FILE = "user_settings.json"

def load_settings():
    global user_settings
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            user_settings = json.load(f)

def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(user_settings, f, indent=4)

@bot.on_message(filters.command("start"))
async def start(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Help", callback_data="help"), InlineKeyboardButton("About", callback_data="about")]
    ])
    await message.reply_text("👋 Welcome! Use /setsource and /setdestination to configure your channels.", reply_markup=keyboard)

@bot.on_callback_query()
async def callback_query_handler(client, callback_query):
    if callback_query.data == "help":
        await callback_query.message.edit_text(
            "**How to Use:**\n\n"
            "1. Add this bot to both source and destination channels.\n"
            "2. Make the bot an Admin in both channels.\n"
            "3. Use the following commands:\n"
            "`/setsource <channel_id>` - Set the source channel\n"
            "`/setdestination <channel_id>` - Set the destination channel\n"
            "\nMake sure channel IDs are in numeric format (with -100 prefix)."
        )
    elif callback_query.data == "about":
        await callback_query.message.edit_text("**Creator:** [Prime Nayem](https://t.me/Prime_Nayem)", disable_web_page_preview=True)

@bot.on_message(filters.command("setsource"))
async def set_source(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setsource <channel_id>")
    
    channel_id = int(message.command[1])
    user_id = str(message.from_user.id)

    try:
        member = await bot.get_chat_member(channel_id, "me")
        if not (member.status in ["administrator", "creator"]):
            return await message.reply_text("⚠️ বট ওই চ্যানেলে অ্যাডমিন না। আগে অ্যাডমিন করুন।")
    except Exception:
        return await message.reply_text("❌ চ্যানেল আইডি ভুল অথবা বট ওই চ্যানেলে নেই।")

    user_settings[user_id] = user_settings.get(user_id, {})
    user_settings[user_id]["source"] = str(channel_id)
    save_settings()
    await message.reply_text("✅ Source চ্যানেল সেট হয়েছে!")

@bot.on_message(filters.command("setdestination"))
async def set_destination(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setdestination <channel_id>")
    
    channel_id = int(message.command[1])
    user_id = str(message.from_user.id)

    try:
        member = await bot.get_chat_member(channel_id, "me")
        if not (member.status in ["administrator", "creator"]):
            return await message.reply_text("⚠️ বট ওই চ্যানেলে পোস্ট করতে পারবে না। আগে বটকে এডমিন বানান।")
    except Exception:
        return await message.reply_text("❌ চ্যানেল আইডি ভুল অথবা বট ওই চ্যানেলে অ্যাডেড নেই।")

    user_settings[user_id] = user_settings.get(user_id, {})
    user_settings[user_id]["destination"] = str(channel_id)
    save_settings()
    await message.reply_text("✅ Destination চ্যানেল সেট হয়েছে!")

@bot.on_message(filters.channel)
async def forward_messages(client, message: Message):
    for user_id, settings in user_settings.items():
        if "source" in settings and "destination" in settings:
            if str(message.chat.id) == settings["source"]:
                try:
                    await bot.copy_message(chat_id=settings["destination"], from_chat_id=message.chat.id, message_id=message.message_id)
                except Exception:
                    pass

# Flask setup
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    load_settings()
    threading.Thread(target=run_flask).start()  # Run Flask in background
    bot.run()
    
