# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Interviewer MVP"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()

    def __init__(self):
        # Normalize scheme for SQLAlchemy
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)

        # If using Neon, SSL is typically required.
        # If sslmode isn't present, append sslmode=require.
        if self.DATABASE_URL and "neon.tech" in self.DATABASE_URL and "sslmode=" not in self.DATABASE_URL:
            separator = "&" if "?" in self.DATABASE_URL else "?"
            self.DATABASE_URL = f"{self.DATABASE_URL}{separator}sslmode=require"

        # Fail loudly on Render if DATABASE_URL is missing
        if os.getenv("RENDER") == "true" and not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is missing on Render. Set it in Render → Web Service → Environment."
            )

settings = Settings()
