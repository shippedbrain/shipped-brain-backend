from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel

class ModelCommentAdd(BaseModel):
    comment: str

class ModelCommentList(BaseModel):
    id: int
    comment: str
    model_name: str
    created_at: datetime
    username: str
    name: str
    user_photo: Union[str, None]
