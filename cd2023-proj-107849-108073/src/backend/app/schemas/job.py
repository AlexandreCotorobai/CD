from pydantic import BaseModel
from typing import List, Union

class Job(BaseModel):
    job_id: int
    size: int
    time: int
    music_id: int
    track_id: Union[int, List[int]]