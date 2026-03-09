from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://cie_user:cie_password@localhost:5432/cie_evaluator"
    SECRET_KEY: str = "your-secret-key-change-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@cie-evaluator.com"
    FRONTEND_URL: str = "http://localhost:3000"

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "qwen"  # "openai" or "anthropic" or "qwen"
    AI_MODEL: str = "qwen3.5-plus"
    QWEN_API_KEY: Optional[str] = None
    QWEN_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    
    RESEND_API_KEY: Optional[str] = None
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "uploads"
    AI_RATE_LIMIT_PER_MINUTE: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
