'''
Telegram bot: youtube downloader, tiktok video downloader, image compresor!
'''
from urllib.request import urlopen
from hashlib import md5
from pathlib import Path
from PIL import Image
from pytube import YouTube
from telebot import TeleBot, types
from telebot.types import (ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton,
                           InlineKeyboardButton, InlineKeyboardMarkup)
from requests import post,get
from bs4 import BeautifulSoup
from config import Token


bot = TeleBot(Token)

BTN = {
    'download_btn': InlineKeyboardButton(text="Donwload a new video",
                                         callback_data="/download"),
    'usage_btn': InlineKeyboardButton(text="How can i usage this bot?",
                                      callback_data="/help"),
    'compress' : InlineKeyboardButton(text="Compress a photo",
                                      callback_data="/compress")
}


@bot.message_handler(commands=['start'])
def cmd_start(message, btn=BTN):
    ''' returns a bot message usage
        args:
        message(message(from telegramApi)) -> all info in json from message'''

    # buttons
    markup = ReplyKeyboardRemove()
    keyboard_markup = InlineKeyboardMarkup().add(
        btn['download_btn']).add(btn['compress']).add(btn['usage_btn'])

    # welcome message
    bot.reply_to(message,
                 "<b>Welcome to @video_downloaderio_bot</b>",
                 parse_mode="html", reply_markup = markup)

    # printing the download & help option.
    bot.send_message(message.chat.id,
                     '<b>This bot can download videos from Tiktok & Youtube in high quality</b>\n\n',
                     parse_mode="html", reply_markup=keyboard_markup,)


@bot.callback_query_handler(func=lambda call: call.data)
def display_option(call: types.CallbackQuery):
    ''' prints a message depending on user choice

        args:
        call((type) from telegramApi) -> all info in json from callback'''

    if call.data == '/help':
        cmd_help(call)

    if call.data == '/download':
        cmd_download(call)

    if call.data == '/compress':
        cmd_compress(call)


@bot.message_handler(commands=['help'])
def cmd_help(message, btn=BTN):
    """displays a help message
    args:
    message(message(from telegramApi)) -> all info in json from message"""

    help_message = "this bot allows you to download videos from YouTube and TikTok in"\
        "high quality. Send me the link and I will download it for you\n\n"\
        "<b>List of commands:</b>\n\n"\
        "/start  ->  displays a welcome message\n"\
        "/help  ->  get this message\n"\
        "/download  ->  download a new video\n"\
        "/compress  ->  compress a image"\
        "\n\n"\
        "choose:"

    keyboard_markup = InlineKeyboardMarkup().add(btn['download_btn'])

    bot.send_message(message.from_user.id,
                     help_message,
                     parse_mode='html',
                     reply_markup=keyboard_markup)


@bot.message_handler(commands=['download'])
def cmd_download(message):
    """This function allows you to download a new video.
    args:
    message(message(from telegramApi)) -> all info in json from message"""
    bot.send_message(message.chat.id, 'call /start to exit')

    download_message = "<b>Where do you want to download the video from?:</b>"
    youtube_btn = KeyboardButton('YouTube')
    tiktok_btn = KeyboardButton('Tiktok')
    keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True,
                                          one_time_keyboard=True,
                                          input_field_placeholder='Press a button:'
                                          ).add(youtube_btn, tiktok_btn)
    msg = bot.send_message(message.from_user.id,
                           download_message,
                           reply_markup=keyboard_markup,
                           parse_mode='html')
    bot.register_next_step_handler(msg, call_downloader)


@bot.message_handler(commands=['compress'])
def cmd_compress(message):
    '''this function allow you to compress a photo'''

    compress_msg = "<b>Send me the image you want to compress:</b>"
    msg = bot.send_message(message.from_user.id, compress_msg, parse_mode='html')
    bot.send_message(message.from_user.id, 'call /start to exit')
    bot.register_next_step_handler(msg, img_compressor)


def call_downloader(message):
    if message.content_type == 'text' and message.text == '/start':
        markup = ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Exiting...", reply_markup = markup)
        return
    '''handles calling download functions'''
    if message.text in ('YouTube', 'Tiktok'):
        markup = ReplyKeyboardRemove()
        example_msg = 'send me the link of the video\n'\
            f'example: <code>https://{message.text.lower()}.com/watch?v=dQw4w9WgXcQ</code>'
        msg = bot.send_message(message.chat.id,
                               example_msg,
                               reply_markup=markup,
                               parse_mode='html')

        if message.text == 'YouTube':
            bot.register_next_step_handler(msg, youtube_downloader)

        elif message.text == 'Tiktok':
            bot.register_next_step_handler(msg, tiktok_downloader)

    else:
        msg = bot.send_message(message.chat.id,
                               'Error: invalid option\n'
                               '<b>Where do you want to download the video from?:</b>',
                               parse_mode='html')
        bot.register_next_step_handler(msg, call_downloader)


def youtube_downloader(message):
    '''download videos from youtube with pytube'''
    if message.content_type == 'text' and message.text == '/start':
        bot.send_message(message.chat.id, "Exiting...")
        return
    id_chat = message.chat.id
    if message.text.startswith('https://youtube.com') or message.text.startswith('https://youtu.be'):
        bot.send_chat_action(id_chat, "record_video")
        converting = bot.send_message(id_chat, "Wait... converting the video")
        try:
            video = YouTube(message.text.replace(" ", ""))
            download = video.streams.get_highest_resolution()
            download.download('./videos')
            video_path = Path(f'./videos/{video.title.replace(".", "")}.mp4')
            if video_path.exists():
                bot.send_chat_action(message.chat.id, "upload_video")
                bot.send_video(message.chat.id, video=open(
                    video_path, 'rb'), supports_streaming=True)
                bot.delete_message(message.chat.id, converting.message_id)
                video_path.unlink()
            else:
                bot.send_message(message.chat.id, 'archive error, try again')

        except:
            bot.delete_message(id_chat, converting.message_id)
            error = bot.send_message(
                id_chat, 'wrong link, <b>send me the link again:</b>', parse_mode='html')
            bot.register_next_step_handler(error, youtube_downloader)   
    else:
        msg = bot.send_message(
            message.chat.id, 'error is not a youtube link\nsend me the link again')
        bot.register_next_step_handler(msg, youtube_downloader)



def tiktok_downloader(message):
    if message.content_type == 'text' and message.text == '/start':
        bot.send_message(message.chat.id, "Exiting...")
        return
    '''download a tiktok video from ssstik.io'''
    if message.text.startswith('https://tiktok.com') or message.text.startswith('https://vm.tiktok.com'):
        cookies = {
            '__cflb': '0H28v8EEysMCvTTqtu4Ydr4bADFLp2DZXKaaWtgnLwF',
        }

        headers = {
            'authority': 'ssstik.io',
            'accept': '*/*',
            'accept-language': 'es-ES,es;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            # 'cookie': '__cflb=0H28v8EEysMCvTTqtu4Ydr4bADFLp2DZXKaaWtgnLwF',
            'hx-current-url': 'https://ssstik.io/es',
            'hx-request': 'true',
            'hx-target': 'target',
            'hx-trigger': '_gcaptcha_pt',
            'origin': 'https://ssstik.io',
            'referer': 'https://ssstik.io/es',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Brave";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        }

        params = {
            'url': 'dl',
        }

        data = {
            'id': message.text.replace(" ", ""),
            'locale': 'es',
            'tt': 'Y1pZRGY1',
        }
        bot.send_chat_action(message.chat.id, "record_video")
        converting = bot.send_message(
            message.chat.id, 'Wait... converting the video')

        try:
            response = post('https://ssstik.io/abc', params=params,
                            cookies=cookies, headers=headers, data=data)
            downloadSoup = BeautifulSoup(response.text, "html.parser")
            print('pasasmos al parser')
            downloadLink = downloadSoup.a['href']
            mp4File = urlopen(downloadLink)
            print('urlopen')
            name = md5(data['id'].encode())
            video_path = f'./videos/{name.hexdigest()}.mp4'
            print('pasamos las asignaciones')

            with open(video_path, 'wb') as output:
                while True:
                    data = mp4File.read(4096)
                    if data:
                        output.write(data)
                    else:
                        break

            if Path(video_path).exists():
                bot.send_chat_action(message.chat.id, "upload_video")
                bot.send_video(message.chat.id, video=open(
                    video_path, 'rb'), supports_streaming=True)
                bot.delete_message(message.chat.id, converting.message_id)
                Path(video_path).unlink()
            else:
                bot.send_message(message.chat.id, 'archive error, try again')
        except:
            error = bot.send_message(
                message.chat.id, 'wrong link, <b>send me the link again:</b>', parse_mode='html')
            bot.register_next_step_handler(error, tiktok_downloader)

    else:
        msg = bot.send_message(
            message.chat.id, 'error is not a tiktok link\nsend me the link again')
        bot.register_next_step_handler(msg, tiktok_downloader)

def img_compressor(message):
    '''verify that it is a photo and apply the compression logic'''
    if message.content_type == 'text' and message.text == '/start':
        bot.send_message(message.chat.id, "Exiting...")
        return
            
    if message.content_type =='photo':
        file_bot = bot.get_file(message.photo[-1].file_id) 
        filePath = f'./photo/{message.message_id}.jpg'
        path = Path(filePath)
        data = get(f'http://api.telegram.org/file/bot{Token}/{file_bot.file_path}')
        print(file_bot.file_path)
        with open(path, 'wb') as file:
            file.write(data.content)

        image = Image.open(filePath)
        quality = 50
        compressed_filename = f"./photo/lite_{message.message_id}.jpg"
        image.save(compressed_filename, optimize=True, quality=quality)
        path.unlink()
        
        bot.send_chat_action(message.chat.id, 'upload_photo')
        bot.send_photo(message.chat.id, open(f"./photo/lite_{message.message_id}.jpg", "rb"))

        Path(f"./photo/lite_{message.message_id}.jpg").unlink()

        bot.send_message(message.chat.id, 'your compressed image is here')

    else:
        error = bot.send_message(message.chat.id, 'wrong archive type <b>send me the image again</b>', parse_mode='html')
        bot.register_next_step_handler(error, img_compressor)

if __name__ == '__main__':
    bot.set_my_commands([
        types.BotCommand("/start","Get the welcome message"),
        types.BotCommand("/help","How to use the bot"),
        types.BotCommand("/download", "download videos from youtube or tiktok"),
        types.BotCommand("/compress", "compress a photo to reduce its weight")
        ])
    print('starting the bot!')
    bot.infinity_polling()
