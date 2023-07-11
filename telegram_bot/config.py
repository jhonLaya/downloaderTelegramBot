'''
Config of telegram bot
'''

from os import environ
from dotenv import load_dotenv

load_dotenv()

Token = environ['TELEGRAM_TOKEN']

print(Token)
