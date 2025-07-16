import os
import time

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import re
import logging

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv

load_dotenv()

VOTE_THRESHOLD = 1
votes = {}  # {voting_msg_id: {"reported_user_id": int, "ban": int, "noban": int, "voters": set()}}


def transliterate(text: str):
    converted_text = (
        text.replace('a', 'а')
            .replace('o', 'о').replace('p', 'р').replace('0', 'о').
            replace('t', 'т').replace('b', 'б').replace('ο', 'о').
            replace('6', 'б').replace('\u00ad', '').replace(' ', '')
    )
    return converted_text


def contains_non_cyrillic_or_latin(text: str) -> bool:
    allowed_pattern = r'^[a-zA-Zа-яА-ЯёЁ0-9\t !"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~—]*$'
    return not bool(re.match(allowed_pattern, text))


def contains_korean_and_arbeit_macht_frei(text: str) -> bool:
    return contains_non_cyrillic_or_latin(text) or \
           bool(re.search(r'\b(работа|подработка|заработок)\b', transliterate(text.lower())))


async def detect_spam_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('spam detector')
    msg = update.message
    if not msg or not msg.reply_to_message or "#spam" not in (msg.text or "").lower():
        logging.info("this message is not a reply or no #spam tag in it, skip")
        return

    reported_msg = msg.reply_to_message
    reported_user = msg.reply_to_message.from_user
    chat_id = msg.chat.id
    if not reported_user or reported_user.id == msg.from_user.id:
        logging.info("you cant report yourself")
        return

    # Build voting keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚫 Ban (0)", callback_data="vote:ban"),
            InlineKeyboardButton("🙅 No Ban (0)", callback_data="vote:noban")
        ]
    ])

    voting_msg = await msg.reply_text(
        f"Vote to ban user @{reported_user.username or reported_user.full_name} (ID: {reported_user.id})",
        reply_markup=keyboard
    )

    # Initialize vote tracking
    votes[voting_msg.message_id] = {
        "reported_user_id": reported_user.id,
        "ban": 0,
        "noban": 0,
        "voters": set(),
        "last_msg_id": reported_msg.message_id
    }


async def handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg_id = query.message.message_id
    user_id = query.from_user.id

    if msg_id not in votes:
        await query.answer("Voting session expired or invalid.")
        return

    vote_data = votes[msg_id]
    if user_id in vote_data["voters"]:
        await query.answer("You've already voted.")
        return

    # Count vote
    vote_type = query.data.split(":")[1]
    vote_data["voters"].add(user_id)
    vote_data[vote_type] += 1

    # Update message text
    new_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🚫 Ban ({vote_data['ban']})", callback_data="vote:ban"),
            InlineKeyboardButton(f"🙅 No Ban ({vote_data['noban']})", callback_data="vote:noban")
        ]
    ])
    await query.edit_message_reply_markup(reply_markup=new_markup)

    # Step 3: Check if threshold reached
    if vote_data["ban"] >= VOTE_THRESHOLD or vote_data["noban"] >= VOTE_THRESHOLD:
        reported_user_id = vote_data["reported_user_id"]
        del votes[msg_id]  # Clean up

        try:
            await query.message.delete()
        except:
            pass  # Ignore if already deleted

        if vote_data["ban"] >= VOTE_THRESHOLD:
            try:
                await context.bot.delete_message(query.message.chat_id, vote_data["last_msg_id"])
                await context.bot.ban_chat_member(query.message.chat_id, reported_user_id)
            except Exception as e:
                logging.error(f"❗️Failed to ban user {reported_user_id}: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('korean filter')
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    msg = update.message or update.edited_message
    if not msg or not (msg.reply_to_message and msg.reply_to_message.forward_from_chat):
        logging.info('not a comment or empty comment')
        return
    message_text = msg.text or msg.caption or ""
    logging.info(message_text)
    if contains_korean_and_arbeit_macht_frei(message_text):
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
                  until_date=int(time.time()) + 30)
            logging.info(f"Muted user {user.username or user_id} for Korean message or rabota stuff.")

        except Exception as e:
            logging.error(f"Error checking admin status or banning: {e}")


def main():
    BOT_TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_spam_report), group=1)
    app.add_handler(CallbackQueryHandler(handle_vote, pattern=r"^vote:"), group=1)
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
