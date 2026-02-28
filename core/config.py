from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field


class Settings(BaseSettings):
    whisper_host: str = Field(default="0.0.0.0")
    whisper_port: int = Field(default=8001)

    llm_host: str = Field(default="0.0.0.0")
    llm_port: int = Field(default=8002)
    ollama_api_url: AnyHttpUrl = Field(default="http://127.0.0.1:11434")

    tts_host: str = Field(default="0.0.0.0")
    tts_port: int = Field(default=8003)
    piper_api_url: AnyHttpUrl = Field(default="http://127.0.0.1:59125")

    intent_host: str = Field(default="0.0.0.0")
    intent_port: int = Field(default=8004)
    intent_model_path: str = Field(default="models/intent.onnx")

    log_level: str = Field(default="INFO")

    class Config:
        env_prefix = "AI_ASSISTANT_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
