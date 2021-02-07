import asyncio
import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode

from config import TOKEN
from lang_middleware import setup_middleware


logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO)

# from aiogram.contrib.middlewares.logging import LoggingMiddleware
# dp.middleware.setup(LoggingMiddleware())

storage = MemoryStorage()

bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN_V2)
dp = Dispatcher(bot, storage=storage)

i18n = setup_middleware(dp)
_ = i18n.gettext
