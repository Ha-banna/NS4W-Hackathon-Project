from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MONGODB_URI: str
    MONGODB_DB: str
    
    API_DOMAIN: str
    API_BASE_PATH: str

    WEBSITE_DOMAIN: str
    WEBSITE_BASE_PATH: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()