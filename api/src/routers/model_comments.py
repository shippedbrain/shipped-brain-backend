from services.user_service import UserService
from models.result import Result
from fastapi import APIRouter, Depends, Response, BackgroundTasks
from services.mlflow_service import MLflowService
from services.model_comment_service import ModelCommentService
from services.user_photo_service import UserPhotoService
from libs.email_lib import Email
import util.validation as Validation
import schemas.user as UserSchema
import schemas.model_comment as ModelCommentSchema
import middleware.auth as AuthMiddleware

router = APIRouter()

# Add comment
@router.post('/models/{model_name}/comments', status_code=200)
def add_comment(model_name: str, model_comment: ModelCommentSchema.ModelCommentAdd, response: Response, background_tasks: BackgroundTasks, current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    # Check if model exists
    model = MLflowService.get_model(model_name)

    if model.is_fail():
        response.status_code = model.get_status_code()
        return model.to_dict()

    model_comment.comment = Validation.trim_whitespaces(text=model_comment.comment)

    # Add comment
    result = ModelCommentService.add_comment(model_name=model_name, user_id=current_user.data.id, comment=model_comment.comment)

    if result.is_fail():
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Send email if comment was not made by model's owner
    if model.data.tags['user_id'] is not None and model.data.tags['user_id'] != current_user.data.username:
        try:
            # Get model owner's data
            model_owner = UserService.get_user_by_username(model.data.tags['user_id'])

            if model_owner.is_success():
                background_tasks.add_task(
                    Email().send_new_model_comment_email,
                    model_owner.data.email,
                    model_owner.data.name,
                    model_name,
                    current_user.data.name,
                    model_comment.comment
                )
        except:
            pass

    return result.to_dict()

# Get comments
@router.get('/models/{model_name}/comments', status_code=200)
def get_model_comments(model_name, response: Response, count_only: bool = False, page_number: int = 1, results_per_page: int = 10):
    # Check if model exists
    model = MLflowService.get_model(model_name)

    if model.is_fail():
        response.status_code = model.get_status_code()
        return model.to_dict()

    # Get comments
    model_comments = ModelCommentService.get_model_comments(
        model_name=model_name,
        count_only=count_only,
        page_number=page_number,
        results_per_page=results_per_page
    )

    if model_comments.is_fail():
        response.status_code = model_comments.get_status_code()

    # Return results straight away when count_only equals True
    if count_only:
        return model_comments.to_dict()

    results = []

    # Get and format comments' data
    for model_comment in model_comments.data:
        # Get commenter
        user = UserService.get_user_by_id(model_comment.user_id)
        username: str = ''
        name: str = ''

        if user.is_success():
            username = user.data.username
            name = user.data.name
            user_photo = None

            try:
                user_photo = UserPhotoService.get_user_photo(username)
            except:
                user_photo = None

        # Format model comment
        model_comment_dict = ModelCommentSchema.ModelCommentList(
            id=model_comment.id,
            comment=model_comment.comment,
            model_name=model_comment.model_name,
            created_at=model_comment.created_at,
            username=username,
            name=name,
            user_photo=user_photo
        )

        results.append(model_comment_dict)

    return Result(
        Result.SUCCESS,
        model_comments.message,
        results
    ).to_dict()

# Delete comment
@router.delete('/models/{model_name}/comments/{comment_id}', status_code=200)
def delete_comment(model_name: str, comment_id: int, response: Response, current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    # Check if model exists
    model = MLflowService.get_model(model_name)

    if model.is_fail():
        response.status_code = model.get_status_code()
        return model.to_dict()

    # Check if comment exists
    model_comment = ModelCommentService.get_comment(comment_id)

    if model_comment.is_fail():
        response.status_code = model_comment.get_status_code()
        return model_comment.to_dict()

    # Get commenter data
    commenter = UserService.get_user_by_id(model_comment.data.user_id)

    if commenter.is_fail():
        response.status_code = commenter.get_status_code()
        return commenter.to_dict()

    # Check if current user has permission to delete comment. Comment can only be deleted by commenter
    if commenter.data.username != current_user.data.username:
        result = Result(
            Result.FAIL,
            'You do not have permissions to delete this comment',
            Result.UNAUTHORIZED
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    deleted_comment = ModelCommentService.delete_comment(comment_id)

    if deleted_comment.is_fail():
        response.status_code = deleted_comment.get_status_code()

    return deleted_comment.to_dict()
