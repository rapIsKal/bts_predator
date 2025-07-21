import os
import time

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
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
    "подработ",
    "заработ",
    "работа",
    "зарабатыва",
]


def contains_non_cyrillic_or_latin(text: str) -> bool:
    allowed_pattern = r'^[a-zA-Zа-яА-ЯёЁ0-9\t\n !"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~—]*$'
    return not bool(re.match(allowed_pattern, text))


def rub_filter(text:str) -> bool:
    return bool(SPAM_PATTERN.search(text))


def contains_korean_and_arbeit_macht_frei(text: str) -> bool:
    return contains_non_cyrillic_or_latin(text) or \
           rub_filter(text.lower()) \
           or any([x in transliterate(text.lower()) for x in SPAM_WORDS])


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
            await context.bot.delete_message(chat_id, update.message.message_id)
            permissions = ChatPermissions(
                **{"can_add_web_page_previews":False,
                "can_change_info":False,
                "can_invite_users":False,
                "can_manage_topics":False,
                "can_pin_messages":False,
                "can_send_audios":True,
                "can_send_documents":False,
                "can_send_messages":False,
                "can_send_other_messages":False,
                "can_send_photos":False,
                "can_send_polls":False,
                "can_send_video_notes":False,
                "can_send_videos":False,
                "can_send_voice_notes":False}
            )
            await context.bot.restrict_chat_member(chat_id, user_id, permissions=permissions,
                  until_date=int(time.time()) + 60)
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
