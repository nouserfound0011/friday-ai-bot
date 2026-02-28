import os
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes
)
from groq import Groq

# Load environment variables
load_dotenv()

telegram_token = os.getenv("TELEGRAM_TOKEN")
groq_key = os.getenv("GROQ_API_KEY")

# Create AI client
client = Groq(api_key=groq_key)

# Memory storage
user_memory = {}

# START command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm Friday 🤖\n"
        "Your AI assistant.\n\n"
        "Ask me anything!\n\n"
        "Commands:\n"
        "/help - Show help\n"
        "/clear - Reset conversation"
    )

# HELP command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this message\n"
        "/clear - Reset conversation memory\n\n"
        "Just send a message and I'll reply!"
    )

# CLEAR MEMORY
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_memory[user_id] = []
    await update.message.reply_text("Conversation memory cleared.")

# HANDLE USER MESSAGES
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    user_message = update.message.text

    # Log message in terminal
    print(update.message.from_user.username, ":", user_message)

    # Typing animation
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    # Initialize memory
    if user_id not in user_memory:
        user_memory[user_id] = [
            {
                "role": "system",
                "content": "You are Friday, a friendly and intelligent AI assistant similar to ChatGPT. Be helpful, clear, and natural."
            }
        ]

    # Add user message
    user_memory[user_id].append({
        "role": "user",
        "content": user_message
    })

    # AI request
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=user_memory[user_id]
    )

    bot_reply = response.choices[0].message.content

    # Save assistant reply
    user_memory[user_id].append({
        "role": "assistant",
        "content": bot_reply
    })

    # Limit memory
    if len(user_memory[user_id]) > 20:
        user_memory[user_id] = user_memory[user_id][-20:]

    # Long message protection
    if len(bot_reply) > 4000:
        for i in range(0, len(bot_reply), 4000):
            await update.message.reply_text(bot_reply[i:i+4000])
    else:
        await update.message.reply_text(bot_reply)

# Build Telegram app
app = ApplicationBuilder().token(telegram_token).build()

# Commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("clear", clear))

# Message handler
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

print("Friday AI Assistant running...")

# Run bot
app.run_polling()