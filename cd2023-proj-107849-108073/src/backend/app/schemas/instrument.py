from pydantic import BaseModel

class Instrument(BaseModel):
    name: str
    track: str
