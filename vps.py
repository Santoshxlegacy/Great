import os
import subprocess
from telegram import Update, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ApplicationBuilder,
    ContextTypes,
)

# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
TELEGRAM_BOT_TOKEN = '7667316589:AAHv8vQsYKvDxi5uMHjgXimeTDpdY23W93Y'

# Replace with your Telegram user ID for security
AUTHORIZED_USER_ID = 1342302666  # Replace with your Telegram user ID

# Store session information
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Hello! I am your VPS management bot.\n\n'
        'Commands:\n'
        '/ls - List files in the directory\n'
        '/download <filename> - Download a file\n'
        '/terminal - Enter terminal mode\n'
        '/exit - Exit terminal mode\n\n'
        'Send a file to upload it to the VPS.'
    )

async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    files = os.listdir('.')
    if files:
        file_list = '\n'.join(files)
        await update.message.reply_text(f'Files in VPS:\n{file_list}')
    else:
        await update.message.reply_text('No files found in the directory.')

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Usage: /download <filename>')
        return

    filename = args[0]
    if os.path.isfile(filename):
        await update.message.reply_document(document=open(filename, 'rb'))
    else:
        await update.message.reply_text(f'File not found: {filename}')

async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.document:
        file = update.message.document
        file_name = file.file_name
        file_path = os.path.join('.', file_name)

        # Download the file to the current directory
        file_object = await file.get_file()
        await file_object.download_to_drive(file_path)

        await update.message.reply_text(f'File uploaded successfully: {file_name}')
    else:
        await update.message.reply_text('Please send a valid document file.')

async def terminal_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Unauthorized access!")
        return

    user_id = update.effective_user.id
    if user_id in user_sessions:
        await update.message.reply_text("You are already in terminal mode.")
    else:
        user_sessions[user_id] = True
        await update.message.reply_text(
            "You are now in terminal mode. Type your commands below.\n"
            "Use /exit to leave terminal mode."
        )

async def terminal_exec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text("You are not in terminal mode. Use /terminal to enter terminal mode.")
        return

    command = update.message.text
    try:
        # Run the command and capture the output
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        output = result.stdout + result.stderr
        if len(output) == 0:
            output = "Command executed successfully with no output."
        await update.message.reply_text(f"{output}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def terminal_exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("You have exited terminal mode.")
    else:
        await update.message.reply_text("You are not in terminal mode.")

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ls", ls))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CommandHandler("terminal", terminal_start))
    application.add_handler(CommandHandler("exit", terminal_exit))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, terminal_exec))
    application.add_handler(MessageHandler(filters.Document.ALL, upload_file))

    application.run_polling()

if __name__ == '__main__':
    main()
  
