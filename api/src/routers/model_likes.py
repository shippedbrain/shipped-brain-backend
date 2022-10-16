import middleware.auth as AuthMiddleware
import schemas.user as UserSchema
from fastapi import APIRouter, Depends, Response, BackgroundTasks
from libs.email_lib import Email
from models.result import Result
from services.mlflow_service import MLflowService
from services.model_like_service import ModelLikeService
from services.user_service import UserService

router = APIRouter()

# Add/Remove model like
@router.post('/model-likes/{model_name}', status_code = 200)
def toggle_like(model_name: str, response: Response, background_tasks: BackgroundTasks, current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    # Check if model exists
    model = MLflowService.get_model(model_name = model_name)

    if model.is_fail():
        response.status_code = model.get_status_code()
        return model.to_dict()

    # Check if user already liked model
    model_like = ModelLikeService.get_like(model_name = model_name, user_id = current_user.data.id)

    if model_like.is_fail():
        response.status_code = model_like.get_status_code()
        return model_like.to_dict()

    result: Result = None

    # Add like if it wasn't found
    if model_like.data is None:
        result = ModelLikeService.add_like(model_name = model_name, user_id = current_user.data.id)

        if result.is_fail():
            response.status_code = result.get_status_code()
            return result.to_dict()

        # Get model owner
        model_owner = UserService.get_user_by_username(username = model.data.tags["user_id"])

        if model_owner.is_success():
            # Send email to model owner
            background_tasks.add_task(
                Email().send_new_model_like_email,
                model_owner.data.name,
                model_owner.data.email,
                model_name
            )

    else: # Remove like if it was found
        result = ModelLikeService.remove_like(model_name = model_name, user_id = current_user.data.id)

        if result.is_fail():
            response.status_code = result.get_status_code()

    return result.to_dict()

# Get model likes
@router.get('/model-likes/{model_name}', status_code = 200)
def get_model_likes(model_name: str, response: Response, username: str = '', count_only: bool = False):
    results = ModelLikeService.get_model_likes(model_name = model_name, count_only = count_only)
    has_liked_model: bool = False

    if results.is_fail():
        response.status_code = results.get_status_code()
        return results.to_dict()

    # If logged in, check if user liked model
    if username:
        user = UserService.get_user_by_username(username = username)

        if user.is_success():
            user_like = ModelLikeService.get_like(model_name = model_name, user_id = user.data.id)

            if user_like.is_success() and user_like.data is not None:
                has_liked_model = True

    results.data = {
        'likes': results.data,
        'has_liked_model': has_liked_model
    }

    return results.to_dict()

# Get user's model likes
@router.get('/users/{username}/model-likes', status_code = 200)
def get_user_likes(username: str, response: Response, current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    # Check if user has permissions to get likes
    if username != current_user.data.username:
        result = Result(
            Result.FAIL,
            "You don't have permissions to see this user's model likes",
            Result.UNAUTHORIZED
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    results = ModelLikeService.get_user_model_likes(user_id = current_user.data.id)

    if results.is_fail():
        response.status_code = results.get_status_code()

    return results.to_dict()