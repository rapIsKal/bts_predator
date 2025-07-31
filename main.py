import logging
import os
import re

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (ApplicationBuilder, ContextTypes, MessageHandler,
                          filters)

logging.basicConfig(level=logging.INFO)

load_dotenv()

SPAM_PATTERN = re.compile(
    r"(?:\d+[.,]?\d*\s*(?:р|руб|rub|₽|k)|\d+\s*(?:тыс|k)\s*(?:р|руб|₽)?)",
    re.IGNORECASE
)

EMOJI_REGEX = re.compile(
    r'[\U0001F600-\U0001F64F' 
    r'\U0001F300-\U0001F5FF'  
    r'\U0001F680-\U0001F6FF'  
    r'\U0001F1E0-\U0001F1FF'  
    r'\U00002700-\U000027BF' 
    r'\U0001F900-\U0001F9FF' 
    r'\U00002600-\U000026FF'  
    r']',
    flags=re.UNICODE
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

FORBIDDEN_MONEY_EMOJIS = {
    "💰",
    "💴",
    "💵",
    "💶",
    "💷",
    "💸",
    "🪙",
}


def contains_forbidden_emoji(text: str) -> bool:
    return any(char in FORBIDDEN_MONEY_EMOJIS for char in text)


def contains_non_cyrillic_or_latin(text: str) -> bool:
    allowed_pattern = r'^[a-zA-Zа-яА-ЯёЁ0-9\t\n !"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~—]*$'
    text_without_emojis = EMOJI_REGEX.sub('', text)
    emoji_count = len(EMOJI_REGEX.findall(text))
    print(emoji_count)
    return not bool(re.match(allowed_pattern, text_without_emojis)) or contains_forbidden_emoji(text)


def rub_filter(text:str) -> bool:
    return bool(SPAM_PATTERN.search(text))


def arbeit_spam_filter(text: str) -> bool:
    return ("работ" in text and not any(x in text for x in ["проработ", "переработ", "разработ"])) or \
           any(x in text for x in SPAM_WORDS)


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
            logging.info('member status: %s', member.status)
            if member.status in ['administrator', 'creator', 'member']:
                logging.info("Skipped banning chat member: %s", user.username or user_id)
                return
            if user.id == 1087968824:  # GroupAnonymousBot
                logging.info("We don't ban GroupAnonymousBot")
                return
            try:
                await context.bot.delete_message(chat_id, update.message.message_id)
            except Exception as e:
                logging.info("Error deleting message %s: %s", update.message.message_id, e)
            await context.bot.ban_chat_member(chat_id, user_id)
            logging.info("Muted user  %s for Korean message or rabota stuff", user.username or user_id)

        except Exception as e:
            logging.error("Error checking admin status or banning: %s", e)


def main():
    BOT_TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message), group=0)
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
