import os

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import re
import logging

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv

load_dotenv()

SPAM_PATTERN = re.compile(
    r"(?:\d+[.,]?\d*\s*(?:р|руб|rub|₽|k)|\d+\s*(?:тыс|k)\s*(?:р|руб|₽)?)",
    re.IGNORECASE
)


def transliterate(text: str):
    converted_text = (
        text.replace('a', 'а')
            .replace('o', 'о').replace('p', 'р').replace('0', 'о').
            replace('t', 'т').replace('b', 'б').replace('ο', 'о').
            replace('6', 'б').replace('\u00ad', '').replace(' ', '')
    )
    return converted_text


SPAM_WORDS = [
    "темк",
    "зарабат",
]


def contains_non_cyrillic_or_latin(text: str) -> bool:
    allowed_pattern = r'^[a-zA-Zа-яА-ЯёЁ0-9\t\n !"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~—]*$'
    return not bool(re.match(allowed_pattern, text))


def rub_filter(text:str) -> bool:
    return bool(SPAM_PATTERN.search(text))


def arbeit_spam_filter(text: str) -> bool:
    return ("работ" in text and not any([x in text for x in ["проработ", "переработ", "разработ"]])) or \
           any([x in text for x in SPAM_WORDS])


def contains_korean_and_arbeit_macht_frei(text: str) -> bool:
    return contains_non_cyrillic_or_latin(text) or \
           rub_filter(text.lower()) \
           or arbeit_spam_filter(transliterate(text.lower()))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    msg = update.message or update.edited_message
    if not msg or not (msg.reply_to_message and msg.reply_to_message.forward_origin):
        logging.info('not a comment or empty comment')
        return
    message_text = msg.text or msg.caption or ""
    logging.info(message_text)
    if contains_korean_and_arbeit_macht_frei(message_text):
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            logging.info(f'member status: {member.status}')
            if member.status in ['administrator', 'creator', 'member']:
                logging.info(f"Skipped banning chat member: {user.username or user_id}")
                return
            if user.id == 1087968824:  # GroupAnonymousBot
                logging.info(f"We don't ban GroupAnonymousBot")
                return
            try:
                await context.bot.delete_message(chat_id, update.message.message_id)
            except Exception as e:
                logging.info(f"Error deleting message {update.message.message_id}: {e}")
            await context.bot.ban_chat_member(chat_id, user_id)
            logging.info(f"Muted user {user.username or user_id} for Korean message or rabota stuff.")

        except Exception as e:
            logging.error(f"Error checking admin status or banning: {e}")


def main():
    BOT_TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message), group=0)
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
