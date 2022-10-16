from pydantic import BaseModel
from datetime import datetime

class PasswordResetBase(BaseModel):
    id: int
    user_id: int
    user_email: str
    reset_token: str
    created_at: datetime

    class Config:
        orm_mode = True

class PasswordResetCreate(BaseModel):
    user_email: str

    class Config:
        orm_mode = True