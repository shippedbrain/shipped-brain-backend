from pydantic import BaseModel
from typing import Optional

class ModelAcl(BaseModel):
    """
        Params
        ------
        model_name: str
                    Name of the model
        username: str
                  unique username
        can_write: bool
                  If True, user can update model card. Otherwise no
        can_publish: bool
                     If True user can publish new model version. Otherwise no
        max_predictions: int
                     Max number of predictions that user can make. If None, then unlimited
        is_admin: bool
                  If True, then user can do everything, even add new users to model's acl
    """
    model_name: str
    username: str
    can_write: bool = False
    can_publish: bool = False
    max_predictions: Optional[int] = None
    is_admin: bool = False
    can_edit_stage: bool = False
