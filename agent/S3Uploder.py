from pydantic import BaseModel

PREMIUM_AGENT_STORIES_BUCKET = "agent-stories-premium"
FREE_AGENT_STORIES_BUCKET = "agent-stories-free"

class AudioPaths(BaseModel):
    mp3_path: str
    timings_path: str

class Audio(BaseModel):
    es_ES_male: AudioPaths
    es_MX_male: AudioPaths
    es_ES_female: AudioPaths
    es_MX_female: AudioPaths

class S3Content(BaseModel):
    images: list[str]
    audio: Audio

class S3Uploder:
    def __init__(self):
        pass

    def upload(self, file_path: str) -> str:
        pass