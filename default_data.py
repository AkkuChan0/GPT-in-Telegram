import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

load_dotenv()

token = os.environ["TELEGRAM_BOT_TOKEN"]

bot = Bot(token=token)
dp = Dispatcher(bot, loop=asyncio.get_event_loop(), storage=MemoryStorage())
