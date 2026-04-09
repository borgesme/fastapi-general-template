from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "FastAPI Project"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fastapi_project"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_retention_days: int = 14
    output_log: bool = True  # 开发环境是否写日志文件（生产环境强制写入）


settings = Settings()
