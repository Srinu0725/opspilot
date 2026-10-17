import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str
    environment: str
    google_api_key: str | None
    database_url: str

    def __init__(self):
        self.app_name = os.getenv("APP_NAME", "OpsPilot")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")

        self.database_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://opspilot:opspilot@localhost:5434/opspilot",
)


settings = Settings()