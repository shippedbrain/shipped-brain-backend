from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ModelRequest(BaseModel):
    id: int
    requested_by: int
    title: str
    description: str
    input_data: str
    output_data: str
    prize: str
    fulfilled_by: int
    fulfilled_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ModelRequestCreate(BaseModel):
    requested_by: Optional[int]
    title: str
    description: str
    input_data: Optional[str]
    output_data: Optional[str]
    prize: Optional[str]

    class Config:
        orm_model = True