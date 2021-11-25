from aiogram import Bot, Dispatcher, executor
import asyncio
from config import BOT_TOKEN
import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage


storage = MemoryStorage()

logging.basicConfig(filename="logging.log",
                    level=logging.INFO,
                    format='%(name)s %(levelname)s %(name)s %(asctime)s   '
                           '%(message)s ',
                    datefmt='%I:%M:%S')

loop = asyncio.get_event_loop()
bot = Bot(BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, loop=loop, storage=storage)


if __name__ == '__main__':
    from handlers import dp
    executor.start_polling(dp, skip_updates=True)
