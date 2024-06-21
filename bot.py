import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers import default, voice
from config_reader import config


async def main():
    bot = Bot(token=config.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(voice.router, default.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    if not os.path.exists(config.audio_files_folder):
        os.makedirs(config.audio_files_folder)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
