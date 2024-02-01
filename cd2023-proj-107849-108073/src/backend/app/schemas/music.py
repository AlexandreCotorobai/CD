from pydantic import BaseModel
from typing import List

from .track import Track

class Music(BaseModel):
    music_id: int
    music_name: str
    music_band: str
    music_tracks: List[Track]
