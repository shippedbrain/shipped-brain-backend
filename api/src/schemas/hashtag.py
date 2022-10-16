from pydantic import BaseModel
from typing import Optional

class HashtagBase(BaseModel):
    id: int
    key: str
    value: str

    class Config:
        orm_mode = True

class HashtagCreateBase(BaseModel):
    key: str
    value: str

    class Config:
        orm_mode = True

class HashtagUpdateBase(BaseModel):
    id: Optional[int]
    key: str
    value: str

    class Config:
        orm_mode = True