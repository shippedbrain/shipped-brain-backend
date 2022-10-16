from services.api_call_service import ApiCallService
from models.result import Result
from fastapi import status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import schemas.token as TokenSchema
from services.user_service import UserService
import os

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv('SECRET_KEY'), algorithm=os.getenv('ALGORITHM'))

    return encoded_jwt, to_encode['exp']


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Result:
    '''
        Gets currenly authenticated user
    '''

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )

    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')])
        username: str = payload.get('sub')

        if username is None:
            raise credentials_exception

        token_data = TokenSchema.TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = UserService.get_user_by_username(username=token_data.username)

    if user.data is None:
        raise credentials_exception

    # Get nr of user's models
    models_count = UserService.count_user_models(username=user.data.username)
    user.data.models_count = None if models_count.is_fail() else models_count.data

    # Get nr of user's model versions
    model_versions_count = UserService.count_user_model_versions(username=user.data.username)
    user.data.model_versions_count = None if model_versions_count.is_fail() else model_versions_count.data

    # Get nr of used api calls
    api_calls_count = ApiCallService.get_user_calls_count(user_id=user.data.id)
    user.data.api_calls_count = None if api_calls_count.is_fail() else api_calls_count.data

    return user
