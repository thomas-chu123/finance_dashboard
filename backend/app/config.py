from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

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

    # AI Briefing
    brave_search_api_key: str = ""
    gemini_api_key: str = ""
    # AI_SUMMARY 選擇摘要提供商：BRAVE_GEMINI（預設）| TAVILY | SEARXNG_OLLAMA
    ai_summary: str = "BRAVE_GEMINI"
    tavily_search_api_key: str = ""

    # AI Briefing — SearXNG + Ollama Direct 路徑（v3）
    searxng_base_url: str = "https://search.skynetapp.org"
    ollama_base_url: str = "http://192.168.0.26:11434"
    ollama_model: str = "gpt-oss:20b"
    ollama_simple_prompt_first: bool = True
    ollama_disable_thinking: bool = True

    # FinMind API
    finmind_api: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    oauth_encryption_key: str = ""  # 32-character key for token encryption

    # App
    app_base_url: str = "http://localhost:5173"
    backend_base_url: str = "http://localhost:8005"
    environment: str = "development"  # 'development' | 'staging' | 'production'
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
