import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Interviewer MVP"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:supercharger@localhost:5432/ai_interviewer",
    )
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


settings = Settings()
