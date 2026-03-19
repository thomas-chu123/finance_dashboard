from pathlib import Path

# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""

    # SMTP Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_from_name: str = "投資通知系統"

    # LINE Message API
    line_channel_access_token: str = ""
    line_channel_secret: str = ""
    line_bot_user_id: str = ""

    # App
    app_base_url: str = "http://localhost:5173"
    backend_base_url: str = "http://localhost:8005"
    debug: bool = False
    secret_key: str = "your-secret-key-change-in-production"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
