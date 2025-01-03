import os
from dataclasses import dataclass, fields
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv


load_dotenv()


class MongoDBClient:
    _client = None

    @classmethod
    def get_client(cls, db_url):
        if cls._client is None:
            cls._client = AsyncIOMotorClient(db_url)
        return cls._client


@dataclass
class Settings:
    """
    Settings class for the application
    """

    openai_api_key: str
    db_url: str
    db_client: Any
    db_name: str
    db: Any = None
    agent_db: Any = None

    # collections
    def __post_init__(self):
        self.db = self.db_client[self.db_name]

    def check_settings_completeness(self) -> float:
        """Checks how many settings are filled out and returns the percentage."""
        total_fields = len(fields(self))
        filled_fields = sum(
            1 for field in fields(self) if getattr(self, field.name) is not None
        )
        completeness_percentage = (filled_fields / total_fields) * 100
        return completeness_percentage


settings = Settings(
    db_url=os.getenv("MONGO_DB_URL"),
    db_client=MongoDBClient.get_client(os.getenv("MONGO_DB_URL")),
    db_name=os.getenv("DBNAME", "jazon_changelog"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)
