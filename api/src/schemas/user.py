from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Login(BaseModel):
    email: str
    password: str

class UserBase(BaseModel):
    id: int
    name: str
    username: str
    email: str
    description: str
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    name: str
    username: str
    email: str
    description: Optional[str]
    password: str

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    name: Optional[str]
    username: str
    email: Optional[str]
    description: Optional[str]

class UserUpdatePassword(BaseModel):
    new_password: Optional[str]
    new_password_confirm: Optional[str]

class UserDelete(BaseModel):
    id: int

    class Config:
        orm_mode = True

class PasswordResetSchema(BaseModel):
    password: str

    class Config:
        orm_model = True
