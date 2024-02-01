from pydantic import BaseModel
from typing import List

from .instrument import Instrument

class Progress(BaseModel):
   progress: int
   instruments: List[Instrument]
   final: str


