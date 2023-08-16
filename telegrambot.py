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


# cache a list for photo showing
carousel_photo_list = []
currentPhotoIdx = -1
carousel_task = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def start_carousel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # get the gilee
    global carousel_photo_list, currentPhotoIdx, carousel_task

    carousel_photo_list = os.listdir(storageFolder)
    interval = 60
    if len(context.args) == 1:
        interval = int(context.args[0])

    if len(carousel_photo_list) == 0:
        await update.message.reply_text("No photos yet. Start by sending me a photo.", reply_markup = None)
        return

    if interval < 30 or interval > 86400:
        await update.message.reply_text("Interval must between 30 to 86400 seconds", reply_markup = None)
        return


    currentPhotoIdx = 0
    await update.message.reply_text("Carousel is going to start", reply_markup = None)

    # set the task
    if carousel_task != None:
        carousel_task.schedule_removal()

    carousel_task = context.job_queue.run_repeating(callback_update_carousel, interval=interval, first=10)


async def callback_update_carousel(context: ContextTypes.DEFAULT_TYPE):
    # Beep the person who called this alarm:
    #await context.bot.send_message(chat_id=context.job.chat_id, text=f'BEEP {context.job.data}!')
    global carousel_photo_list, currentPhotoIdx, carousel_task
    #print(carousel_photo_list)
    if len(carousel_photo_list) == 0:
        # do nothing...
        return

    if currentPhotoIdx >= len(carousel_photo_list):
        currentPhotoIdx = 0 # reset back

    file_path = storageFolder + "/" + carousel_photo_list[currentPhotoIdx]
    # check if the photo exists
    if not os.path.isfile(file_path):
        # skip to next, and try again in next iternation
        currentPhotoIdx += 1
        return

    epd.display(file_path)
    currentPhotoIdx += 1

async def stop_carousel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global carousel_photo_list, currentPhotoIdx, carousel_task

    if carousel_task == None:
        await update.message.reply_text("Carousel is not running", reply_markup = None)
        return

    carousel_task.schedule_removal()
    carousel_task = None
    currentPhotoIdx = -1
    await update.message.reply_text("Carousel is going to stop", reply_markup = None)




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

    # update 
    global carousel_photo_list
    carousel_photo_list = os.listdir(storageFolder)
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

    # update
    global carousel_photo_list
    carousel_photo_list = os.listdir(storageFolder)

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
    start_carousel_handler = CommandHandler('start_carousel', start_carousel)
    stop_carousel_handler = CommandHandler('stop_carousel', stop_carousel)

    # command
    application.add_handler(start_handler)
    application.add_handler(list_handler)
    application.add_handler(show_handler)
    application.add_handler(remove_handler)
    application.add_handler(clear_screen_handler)
    application.add_handler(refresh_screen_handler)
    application.add_handler(start_carousel_handler)
    application.add_handler(stop_carousel_handler)

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
