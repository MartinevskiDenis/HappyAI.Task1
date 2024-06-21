from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    openai_api_key: SecretStr
    openai_stt_model: str
    openai_tts_model: str
    openai_tts_voice: str
    openai_assistant_name: str
    openai_assistant_instructions: str
    openai_assistant_model: str
    openai_assistant_id: str
    create_openai_assistant: bool
    audio_files_folder: str
    thread_lifetime_sec: int

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


config = Settings()
