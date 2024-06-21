from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer("Hello! This bot receives voice messages, converts them into text, "
                         "receives answers to questions asked and voices the answers. "
                         "Send bot a voice message and he will answer it!")


@router.message()
async def default_handler(message: Message):
    await message.answer("Bot only processes voice messages. "
                         "Please send bot a voice message and he will answer it!")
