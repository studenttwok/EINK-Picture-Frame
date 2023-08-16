# Intro
I bought an expensive E-Paper Device (EPD). How can I make the investment worthwhile?

Without enough time to build a dedicated  Human Machine Interface, I used Telegram as the communication interface.
Commands can be sent as text messages, and image data can be sent as photo messages. Building a telegram bot and manipulating the image is easy in Python, but the control library is available in C only. I spent time implementing some methods in Python, and the result was satisfactory.

# Demo Video
[![Watch the video](https://i.ytimg.com/vi/TADT6oSMmqE/hqdefault.jpg)](https://youtu.be/TADT6oSMmqE)
[![Watch the video](https://i.ytimg.com/vi/bvpBKvaGccw/hqdefault.jpg)](https://youtu.be/bvpBKvaGccw)

# Requirment:
* Waveshare 7.8inch HD e-Paper HAT (IT8951)
* Raspberry Pi (Tested with Raspberry Pi Zero W)
* Python3

# Install Dependency and storage folder:
Connect your EPD to your RPi with the HAT and adapter before plugging in the power chord.

In the terminal of your RPi, clone this repo using git clone command.

In the Repo folder, execute the following lines:

    pip install -r requirements.txt
    mkdir photos
    sudo rasp-config

In rasp-config, select "3 Interface Options" -> "I4 SPI", and enable it

# Offline drawing on EDP
    python3 main.py pic/800x600.bmp
Feel free to explore the functions in main.py and create your program

# Telegram Bot
Create your telegram bot by using the @BotFather bot in Telegram, obtain the api TOKEN
Start the bot with the following command

    python3 telegrambot.py TOKEN

Display the image by sending it as Photo or Document message to this bot.

The bot will save the images in photos folder, and you can show them again in the future without the need or resending it again.

You can refresh or clear the screen as well.

Finally, you can use carousel mode to change the displayed photo automatically.

Feel free to use telegrambot.py and epd.py as the starting point and create your bot.


# Telegram Bot command list
    list - List Images
    show [filename]- Show image
    remove [filename]- Remove the image
    clear - Clear Screen
    refresh - Refresh the screen
    start_carousel [Interval in Second]- Start Carousel
    stop_carousel - Stop Carousel

# Future Development
I create this POC hobby project in my time. This program code is imperfect (Naming convention and task scheduling, etc.) and can only be used in production with suitable modification. I may improve it when I have more time. If you would like to contribute, PR is welcome.

Modifications (like buffer size and refresh mode) can be made to support the below Waveshare EPD:

        "6inch e-Paper HAT(800,600)"
        "6inch HD e-Paper HAT(1448,1072)"
        "6inch HD touch e-Paper HAT(1448,1072)"
        "9.7inch e-Paper HAT(1200,825)"
        "7.8inch e-Paper HAT(1872,1404)"
        "10.3inch e-Paper HAT(1872,1404)"
        
They have the same communication protocol and the same HAT.


# Libraries
* RPi.GPIO - https://pypi.org/project/RPi.GPIO/
* SPIDev - https://pypi.org/project/spidev/
* Pillow - https://pillow.readthedocs.io/en/stable/
* python-telegram-bot - https://python-telegram-bot.org/

# Reference:
* https://www.waveshare.com/wiki/7.8inch_e-Paper_HAT
* https://github.com/kleini/it8951/tree/master (Code of pack_pixels())


