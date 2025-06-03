import os

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import re
import logging

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv

load_dotenv()


def contains_korean(text: str) -> bool:
    return bool(re.search(r"[ㄱ-ㅎㅏ-ㅣ가-힣]", text))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    msg = update.message or update.edited_message
    if not msg:
        return
    message_text = msg.text or ""
    if contains_korean(message_text):
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            logging.info(f'member status: {member.status}')
            if member.status in ['administrator', 'creator']:
                logging.info(f"Skipped banning admin: {user.username or user_id}")
                return

            await context.bot.delete_message(chat_id, update.message.message_id)
            if user.id == 1087968824:  # GroupAnonymousBot
                logging.info(f"We don't ban GroupAnonymousBot")
                return
            await context.bot.ban_chat_member(chat_id, user_id)
            logging.info(f"Banned user {user.username or user_id} for Korean message.")

        except Exception as e:
            logging.error(f"Error checking admin status or banning: {e}")


def main():
    BOT_TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
