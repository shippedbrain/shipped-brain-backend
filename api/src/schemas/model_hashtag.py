from pydantic import BaseModel

class ModelHashtagBase(BaseModel):
    hashtag_id: int
    model_name: str
    model_version: int