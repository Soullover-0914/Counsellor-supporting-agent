from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Counselling Support Agent"
    app_version: str = "1.0.0"
    environment: str = "development"

    gemini_api_key: str = ""

    database_url: str = "sqlite+aiosqlite:///./counselling.db"

    # Authentication security
    auth_secret_key: str = ""

    # SQLCipher database encryption
    database_encryption_key: str = ""

    # Production security
    token_expiry_seconds: int = 3600

    # Public login URL included in student approval emails
    app_login_url: str = "http://127.0.0.1:5173/login"

    # SMTP / email (secrets via environment only)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = ""
    smtp_from_name: str = "Agent 66 Counselling Support"

    # Centralised institutional role recipients (non-secret)
    email_admin: str = "231fa04543@gmail.com"
    email_hod: str = "rsaketh033@gmail.com"
    email_faculty: str = "jyothiswaroopgolla@gmail.com"
    email_counsellor: str = "231fa04b14@gmail.com"
    email_mentor: str = "jyothiswaroop0914@gmail.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
