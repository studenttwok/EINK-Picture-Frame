import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import epd
import sys

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def media(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.document:
        file_id = update.message.document.file_id
        file_path = './photos/' + update.message.document.file_unique_id + ".jpg"
        new_file = await context.bot.get_file(file_id)
        await new_file.download_to_drive(custom_path=file_path)

        epd.display(file_path)

    elif update.message.photo:
        files = update.message.photo
        #for file in files:
        file = files[-1]
        file_id = file.file_id
        new_file = await context.bot.get_file(file_id)
        file_path = './photos/' + file.file_unique_id + ".jpg"
        await new_file.download_to_drive(custom_path=file_path)

        epd.display(file_path)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Receive the photo")

def telegram_client(token):
    application = ApplicationBuilder().token(token).build()

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    media_handler = MessageHandler((filters.PHOTO | filters.Document.JPG), media)
    start_handler = CommandHandler('start', start)

    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(media_handler)

    application.run_polling()




if __name__ == '__main__':

    if (len(sys.argv) != 2):
        print("Usage: python telegram.py Token")
    else:
        token = sys.argv[1]
        telegram_client(token)
