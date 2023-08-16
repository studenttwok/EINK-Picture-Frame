import logging
from telegram import Update, InputMediaPhoto, MessageEntity, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import epd
import sys
import os
import time
import unicodedata
import re

### Settings
storageFolder = "./photos"
######

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def list_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_list = os.listdir(storageFolder)

    keyboards = []
    for file in file_list:
        show_command = "/show " + file
        remove_command = "/remove " + file
        keyboards.append([show_command, remove_command])
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(storageFolder+"/"+file, "rb"), caption=show_command)

    if len(file_list) == 0:
        await update.message.reply_text("No photos yet. Start by sending me a photo.", reply_markup = None)
        return

    reply = ReplyKeyboardMarkup(keyboards, one_time_keyboard=True, input_field_placeholder="Which photo to display?")
    await update.message.reply_text("Which photo to display?", reply_markup=reply)

async def show_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("ERROR: Please supply filename as argument")
        return

    filename = context.args[0]
    filename = filename.replace("/","")
    filename = filename.replace("\\","")

    # check if the file exists
    filePath = storageFolder + "/" + filename
    if not os.path.isfile(filePath):
        await update.message.reply_text("ERROR: File not exists")
        return

    # show the photo
    await update.message.reply_text("Loading....")
    epd.display(filePath)
    await update.message.reply_text("Photo is displayed")

async def remove_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("ERROR: Please supply filename as argument")
        return

    filename = context.args[0]
    filename = filename.replace("/","")
    filename = filename.replace("\\","")

    # check if the file exists
    filePath = storageFolder + "/" + filename
    if not os.path.isfile(filePath):
        await update.message.reply_text("ERROR: File not exists")
        return

    # show the photo
    os.remove(filePath)
    await update.message.reply_text("Photo is removed successfully")

async def clear_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Screen is clearing...!")
    epd.clear_screen()
    await update.message.reply_text("Screen is cleared!")

async def refresh_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Screen is refreshing...")
    epd.refresh_screen()
    await update.message.reply_text("Screen is refreshed!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)



async def media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = ""
    new_file = None
    if update.message.document:
        #new_filename = update.message.document.file_unique_id + ".jpg"
        new_filename = str(int(time.time()*1000)) + ".jpg"

        if update.message.caption != None:
            caption = update.message.caption
            caption = caption.replace(".", "")
            caption = caption.replace("/", "")
            caption = caption.replace("\\", "")
            caption = unicodedata.normalize('NFKD', caption).encode('ascii', 'ignore').decode('ascii')
            caption = re.sub(r'[^\w\s-]', '', caption.lower())
            caption = re.sub(r'[-\s]+', '-', caption).strip('-_')
            if len(caption) > 0:
                new_filename = caption + ".jpg"

        file_id = update.message.document.file_id
        file_path = storageFolder + '/' + new_filename
        new_file = await context.bot.get_file(file_id)

    elif update.message.photo:
        #new_filename = file.file_unique_id+".jpg"
        new_filename = str(int(time.time()*1000)) + ".jpg"

        if update.message.caption != None:
            caption = update.message.caption
            caption = caption.replace(".", "")
            caption = caption.replace("/", "")
            caption = caption.replace("\\", "")
            caption = unicodedata.normalize('NFKD', caption).encode('ascii', 'ignore').decode('ascii')
            caption = re.sub(r'[^\w\s-]', '', caption.lower())
            caption = re.sub(r'[-\s]+', '-', caption).strip('-_')
            if len(caption) > 0:
                new_filename = caption + ".jpg"

        files = update.message.photo
        file = files[-1]
        file_id = file.file_id
        new_file = await context.bot.get_file(file_id)
        file_path = storageFolder + '/' + new_filename

    if new_file == None or file_path == "":
        await update.message.reply_text("ERROR: File not uploaded")
        return

    await new_file.download_to_drive(custom_path=file_path)
    await update.message.reply_text("Sending to EPD....")
    epd.display(file_path)
    await update.message.reply_text("Photo is displayed!")
    #await context.bot.send_message(chat_id=update.effective_chat.id, text="Photo displayed")

def telegram_client(token):
    application = ApplicationBuilder().token(token).build()

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    media_handler = MessageHandler((filters.PHOTO | filters.Document.JPG), media)
    start_handler = CommandHandler('start', start)
    list_handler = CommandHandler('list', list_images)
    show_handler = CommandHandler('show', show_image)
    remove_handler = CommandHandler('remove', remove_image)
    clear_screen_handler = CommandHandler('clear', clear_screen)
    refresh_screen_handler = CommandHandler('refresh', refresh_screen)

    # command
    application.add_handler(start_handler)
    application.add_handler(list_handler)
    application.add_handler(show_handler)
    application.add_handler(remove_handler)
    application.add_handler(clear_screen_handler)
    application.add_handler(refresh_screen_handler)

    # content handler
    application.add_handler(echo_handler)
    application.add_handler(media_handler)


    application.run_polling()




if __name__ == '__main__':

    if (len(sys.argv) != 2):
        print("Usage: python telegram.py Token")
    else:
        token = sys.argv[1]
        telegram_client(token)
