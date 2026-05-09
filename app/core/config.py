"""Application configuration. All env-driven settings live here."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "VehicleRentalAPI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./vehicle_rental.db"

    # Security
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # OTP
    OTP_EXPIRE_MINUTES: int = 5
    OTP_LENGTH: int = 6
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 30

    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Redis
    REDIS_URL: str = ""

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Pricing
    DEFAULT_BIKE_HOURLY_RATE: float = 40
    DEFAULT_CAR_HOURLY_RATE: float = 150
    DEFAULT_AUTO_HOURLY_RATE: float = 80
    DEFAULT_SECURITY_DEPOSIT: float = 2000
    GST_PERCENT: float = 18

    # Maps
    GOOGLE_MAPS_API_KEY: str = ""

    # Admin bootstrap
    ADMIN_EMAIL: str = "admin@vehiclerental.com"
    ADMIN_PASSWORD: str = "Admin@12345"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def use_twilio(self) -> bool:
        return bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN and self.TWILIO_PHONE_NUMBER)

    @property
    def use_redis(self) -> bool:
        return bool(self.REDIS_URL)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
