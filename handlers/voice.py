from aiofiles import os

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Voice, FSInputFile

from openai import AsyncOpenAI, OpenAI

from pydub import AudioSegment

import dotenv

from config_reader import config


def get_assistant_id() -> str:
    if config.create_openai_assistant:
        assistant = OpenAI(api_key=config.openai_api_key.get_secret_value()).beta.assistants.create(
            name=config.openai_assistant_name,
            instructions=config.openai_assistant_instructions,
            model=config.openai_assistant_model
        )

        dotenv_file = dotenv.find_dotenv()
        dotenv.load_dotenv(dotenv_file)
        dotenv.set_key(dotenv_file, "OPENAI_ASSISTANT_ID", assistant.id)
        dotenv.set_key(dotenv_file, "CREATE_OPENAI_ASSISTANT", "False")

        return assistant.id
    else:
        return config.openai_assistant_id


client = AsyncOpenAI(api_key=config.openai_api_key.get_secret_value())
assistant_id = get_assistant_id()
router = Router()


def convert_ogg_to_mp3(file_path_ogg: str, file_path_mp3: str):
    AudioSegment.from_ogg(file_path_ogg).export(file_path_mp3, format="mp3")


async def save_voice_to_file(voice: Voice, bot: Bot) -> str:
    file_path = f"{config.audio_files_folder}/{voice.file_id}.ogg"
    await bot.download(voice, file_path)
    return file_path


async def get_text_from_voice(file_path: str) -> str:
    with open(file_path, "rb") as voice_file:
        transcription = await client.audio.transcriptions.create(
            model=config.openai_stt_model,
            file=voice_file
        )
    await os.remove(file_path)
    return transcription.text


async def get_response_for_text(text: str, state: FSMContext, message_timestamp: int):
    state_data = await state.get_data()

    if (("last_message_timestamp" in state_data)
            and ((message_timestamp - state_data["last_message_timestamp"]) <= config.thread_lifetime_sec)):
        thread_id = state_data["thread_id"]
    else:
        thread = await client.beta.threads.create()
        thread_id = thread.id
        await state.update_data(thread_id=thread_id)

    message = await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text
    )
    user_message_id = message.id

    run = await client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    raw_messages = await client.beta.threads.messages.list(
        thread_id=thread_id,
        order="asc",
        after=user_message_id
    )

    messages = [{"id": raw_message.id, "text": raw_message.content[0].text.value} for raw_message in raw_messages.data]
    return messages, thread_id


async def parse_messages_to_voices(messages, thread_id: str):
    files_paths = []
    for message in messages:
        file_path = f"{config.audio_files_folder}/{thread_id}_{message['id']}.mp3"
        files_paths.append(file_path)
        response = await client.audio.speech.create(
            model=config.openai_tts_model,
            voice=config.openai_tts_voice,
            input=message["text"]
        )
        response.stream_to_file(file_path)
    return files_paths


@router.message(F.voice)
async def voice_handler(message: Message, bot: Bot, state: FSMContext):
    voice_file_path = await save_voice_to_file(message.voice, bot)
    voice_text = await get_text_from_voice(voice_file_path)
    message_timestamp = int(message.date.timestamp())
    response_messages, thread_id = await get_response_for_text(voice_text, state, message_timestamp)
    response_files_paths = await parse_messages_to_voices(response_messages, thread_id)
    for response_file_path in response_files_paths:
        await message.answer_voice(FSInputFile(response_file_path))
        await os.remove(response_file_path)
    await state.update_data(last_message_timestamp=message_timestamp)
