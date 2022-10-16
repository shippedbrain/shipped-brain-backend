from pydantic import BaseModel
from datetime import datetime

class ApiCallBase(BaseModel):
    id: int
    user_id: int
    model_name: str
    model_version: int
    call_time: datetime

class ApiCallCreate(BaseModel):
    user_id: str
    model_name: str
    model_version: str

    class Config:
        orm_mode = True