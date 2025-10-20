from pydantic import BaseModel
from enum import Enum

class AccessLevel(Enum):
    free = "free"
    premium = "premium"

class FirestoreMetadata(BaseModel):
    id: str
    title: str
    level: str
    language: str
    wordCount: int
    readingTime: str
    tags: list[str]
    accessLevel: AccessLevel

class FirestoreUploader:
    def __init__(self):
        pass

    def upload(self, file_path: str) -> str:
        pass