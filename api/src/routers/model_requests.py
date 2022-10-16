from fastapi import APIRouter, Response, Depends
from models.result import Result
from models.model_request import ModelRequest
from services.model_request_service import ModelRequestService
from services.user_service import UserService
import schemas.model_request as ModelRequestSchema
import util.validation as Validation
import schemas.user as UserSchema
import middleware.auth as AuthMiddleware
import libs.format as Format

router = APIRouter()

# Create model request
@router.post('/model-requests', status_code = 200)
def create_model_request(
    model_request: ModelRequestSchema.ModelRequestCreate, 
    response: Response, 
    current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    ''' Create model request
    '''

    # Set current user's ID in model request
    model_request.requested_by = current_user.data.id

    # Validate model request title
    if model_request.title is None:
        result = Result(
            Result.FAIL,
            'Please provide a title for your model request',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Validate model request description
    if model_request.description is None:
        result = Result(
            Result.FAIL,
            'Please provide a description for your model request',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Trim whitespaces
    model_request.title = Validation.trim_whitespaces(model_request.title)

    # Create model request
    result = ModelRequestService.create_model_request(model_request)

    # Check if model request wasn't created
    if result.is_fail():
        response.status_code = result.get_status_code()

    return result.to_dict()

# Get model requests
@router.get('/model-requests', status_code = 200)
def get_model_requests(response: Response, status: str = '', search_query: str = ''):
    ''' Get model requests
    '''

    # Validate status to filter by
    if status and status not in ModelRequest.VALID_STATUS_LIST:
        result = Result(
            Result.FAIL,
            'Invalid model request status',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result

    model_requests_query = ModelRequestService.get_model_requests(status, search_query)
    results = []

    if model_requests_query.is_fail():
        response.status_code = model_requests_query.get_status_code()
        return model_requests_query.to_dict()

    for model_request in model_requests_query.data:
        result = Format.format_model_request(model_request)

        # Get user who requested model
        requested_user = UserService.get_user_by_id(model_request.requested_by)

        if requested_user.is_success():
            result['user_requested_by'] = Format.format_user(requested_user.data)

        # Get user who fulfilled model
        if result['fulfilled_by']:
            fulfilled_user = UserService.get_user_by_id(model_request.fulfilled_by)

            if fulfilled_user.is_success():
                result['user_fulfilled_by'] = Format.format_user(fulfilled_user.data)

        # Check if request was made in the last 24 hours
        result['is_recent'] = ModelRequest().is_recent_request(model_request.created_at)

        results.append(result)

    return Result(
        Result.SUCCESS,
        'Successfully retrieved model requests',
        results
    ).to_dict()

# Get model request
@router.get('/model-requests/{model_request_id}', status_code = 200)
def get_model_request(model_request_id: int, response: Response):
    '''
        Get model request by ID
    '''

    model_request_data = ModelRequestService.get_model_request(model_request_id)
    result = None

    if model_request_data.is_fail():
        response.status_code = model_request_data.get_status_code()
        return model_request_data.to_dict()

    result = Format.format_model_request(model_request_data.data)

    # Get user who requested model
    requested_user = UserService.get_user_by_id(result['requested_by'])

    if requested_user.is_success():
        result['user_requested_by'] = Format.format_user(requested_user.data)

    # Get user who fulfilled model
    if result['fulfilled_by']:
        fulfilled_user = UserService.get_user_by_id(result['fulfilled_by'])

        if fulfilled_user.is_success():
            result['user_fulfilled_by'] = Format.format_user(fulfilled_user.data)

    # Check if request was made in the last 24 hours
    result['is_recent'] = ModelRequest().is_recent_request(result['created_at'])

    return Result(
        Result.SUCCESS,
        'Successfully retrieved model request',
        result
    ).to_dict()