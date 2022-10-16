from typing import Optional, Dict, Any, List, Union

from pydantic import BaseModel


class User(BaseModel):
    name: str
    username: str
    photo: Optional[str] = None


class Likes(BaseModel):
    count: int
    has_liked_model: bool

class MlModelPage(BaseModel):
    name: str
    version: Optional[int] = 0
    metrics: Optional[Union[Dict[str, Any], str]] = None
    parameters: Optional[Union[Dict[str, Any], str]] = None
    tags: Optional[Dict[str, Any]]
    likes: Likes
    comment_count: int
    signature: Optional[Union[dict, str]] = None
    input_example: Optional[Union[dict, str]] = None
    api_calls: int
    description: str
    user: User
    creation_time: int
    last_update_time: int
    hashtags: List[Any]
    github_repo: Optional[str] = None
    github_repo_files_url: Optional[str] = None
    github_repo_readme_url: Optional[str] = None
    model_card: Optional[str] = None
    cover_photo: Optional[str] = None


class MlModelListing(BaseModel):
    name: str
    version: int
    hashtags: List[Any]
    tags: Optional[Dict[str, Any]] = None
    user: User
    likes: Likes
    comment_count: int
    api_calls: int
    description: str
    creation_time: int
    last_update_time: int
    cover_photo: Optional[str] = None

class MlModelCreate(BaseModel):
    name: str
    description: Optional[str]
    metrics: Optional[Union[dict, str]]
    parameters: Optional[Union[dict, str]]
    github_repo: Optional[str]
    input_example: Optional[Union[dict, str]]
    signature: Optional[Union[dict, str]]

class MlModelEdit(BaseModel):
    description: Optional[str]
    metrics: Optional[Union[dict, str]]
    parameters: Optional[Union[dict, str]]
    github_repo: Optional[str]
    input_example: Optional[Union[dict, str]]
    signature: Optional[Union[dict, str]]

class MlModelMetricsSet(BaseModel):
    metrics: str

class MlModelGitHubSet(BaseModel):
    url: str

class MlModelParametersSet(BaseModel):
    parameters: str

class MlModelInputExampleSet(BaseModel):
    input_example: str

class MlModelSignatureSet(BaseModel):
    signature: str