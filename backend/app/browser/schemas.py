from typing import Literal
from pydantic import BaseModel, Field, HttpUrl

class OpenUrlRequest(BaseModel):
    url: HttpUrl

class YouTubeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)

class BrowserActionRequest(BaseModel):
    action: Literal["pause", "resume"]
