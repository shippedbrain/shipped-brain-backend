'''
File upload server

This server implements the model deployment and project upload feature. This prevents the main API from blocking.  
'''
from fastapi import APIRouter, Depends, Response
from services.model_upload_service import ModelUploadService
from services.user_service import UserService
from models.result import Result
from models.model_upload import ModelUpload
import middleware.auth as AuthMiddleware

router = APIRouter()

# Get model uploads of user
@router.get('/uploads/user/{username}', status_code = 200)
def get_user_model_uploads(username: str, response: Response, status: str = None, current_user = Depends(AuthMiddleware.get_current_user)):
    '''
        Get user's uploads with optional status
    '''

    status = None if status == '' else status

    # Check if status parameter is valid
    if status and not ModelUpload.is_valid_status(status):
        result = Result(
            Result.FAIL,
            'Status is not valid',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    user = UserService.get_user_by_username(username)

    if user.is_fail():
        result = Result(
            Result.FAIL,
            'Username not found',
            Result.NOT_FOUND
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    results = ModelUploadService.list(user_id = user.data.id, status = status)

    if results.is_fail():
        response.status_code = results.get_status_code()

    return results.to_dict()

# Get model upload by ID
@router.get('/uploads/{model_upload_id}', status_code = 200)
def get_model_upload_by_id(model_upload_id: int, response: Response, current_user = Depends(AuthMiddleware.get_current_user)):
    '''
        Get model upload by ID
    '''

    result = ModelUploadService.get_by_id(model_upload_id)

    if result.is_fail():
        response.status_code = result.get_status_code()

    return result.to_dict()