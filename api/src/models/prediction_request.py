from typing import List, Any, Optional
from pydantic import BaseModel

# TODO move to schemas
class PredictionRequest(BaseModel):
    columns: List[str]
    data: List[List[Any]]