from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Application
    app_name: str = "Dimora CRM"
    app_env: str = "development"
    debug: bool = True
    sentry_dsn: Optional[str] = None
    secret_key: str = "change-me-in-production"
    api_v1_prefix: str = "/api/v1"

    # Admin User
    admin_email: str = "admin@dimora.com"
    admin_password: str = "Admin@123"

    # Database
    database_url: str = "postgresql+asyncpg://dimora:dimora_secret@localhost:5432/dimora_crm"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "jwt-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # AWS S3 / MinIO
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "dimora-files"
    s3_endpoint_url: Optional[str] = "http://localhost:9000"

    # WhatsApp
    whatsapp_api_url: str = "https://graph.facebook.com/v18.0"
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_verify_token: str = ""

    # Facebook
    facebook_app_secret: str = ""
    facebook_verify_token: str = ""

    # Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/integrations/google/callback"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # SMTP (transactional email: reminders, task assignment). Use App Password for Gmail.
    smtp_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Dimora CRM"
    email_notify_leads_on_meeting: bool = False

    @field_validator("smtp_enabled", "email_notify_leads_on_meeting", mode="before")
    @classmethod
    def _coerce_bool(cls, v):
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("true", "1", "yes", "on"):
                return True
            if s in ("false", "0", "no", "off", ""):
                return False
        return v

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
