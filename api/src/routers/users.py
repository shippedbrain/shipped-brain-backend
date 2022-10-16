from services.user_photo_service import UserPhotoService
from fastapi import APIRouter, Response, Request, Depends
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from models.result import Result
from services.user_service import UserService
from services.mlflow_service import MLflowService
from services.api_call_service import ApiCallService
from services.hashtag_service import HashtagService
from services.social_network_service import SocialNetworkService
from services.model_like_service import ModelLikeService
from services.image_upload_service import ImageUploadService
from services.model_comment_service import ModelCommentService
from libs.email_lib import Email
import schemas.user as UserSchema
import schemas.hashtag as HashtagSchema
import middleware.auth as AuthMiddleware
import libs.format as Format
import util.validation as Validation
import schemas.ml_model as ml_model_schema
import libs.utilities as utilities

router = APIRouter()

# Create user
@router.post('/users', status_code=200)
def create_user(user: UserSchema.UserCreate, response: Response):
    not_acceptable_result = Result(
        Result.FAIL,
        '',
        Result.NOT_ACCEPTABLE
    )

    # Account validation
    user_exists = UserService.check_if_user_exists(username=user.username, email=user.email)

    if user_exists.is_fail():
        response.status_code = user_exists.get_status_code()
        return user_exists.to_dict()

    if user_exists.data['user_exists']:
        result = Result(
            Result.FAIL,
            'Account already exists',
            Result.FORBIDDEN
        )

        response.status_code = result.get_status_code()
        return result.to_dict()

    # Name validation
    if user.name is None:
        not_acceptable_result.message = 'Name is not valid'
        response.status_code = not_acceptable_result.get_status_code()
        return not_acceptable_result.to_dict()

    # Username validation
    if Validation.has_whitespaces(user.username):
        not_acceptable_result.message = 'Username cannot contain whitespaces'
        response.status_code = not_acceptable_result.get_status_code()
        return not_acceptable_result.to_dict()

    # Email validation
    if Validation.has_whitespaces(user.email) or not Validation.is_email_valid(user.email):
        not_acceptable_result.message = 'Email is not valid'
        response.status_code = not_acceptable_result.get_status_code()
        return not_acceptable_result.to_dict()

    # Password validation
    if Validation.has_whitespaces(user.password) or not Validation.is_password_valid(user.password):
        not_acceptable_result.message = f"Password is not valid. Please unsure it doesn't contain whitespaces and is at least {Validation.USER_PASSWORD_MIN_LENGTH} characters long"
        response.status_code = not_acceptable_result.get_status_code()
        return not_acceptable_result.to_dict()

    result = UserService.create_user(user)

    # Check if user was created
    if result.is_fail():
        response.status_code = result.get_status_code()
        return result.to_dict()

    user_id = result.data['created_user'].id
    result.data = Format.format_user(result.data['created_user'])

    # TODO should we do this?
    # create user mlflow experiment - this guarantees that experiment id (artifact path) == user.id
    # experiment_id = mlflow.create_experiment(user.name)

    # Send email confirming account was created
    try:
        Email().send_account_created_email(user_name=result.data['name'], user_email=result.data['email'])
    except:
        print('[EMAIL EXCEPTION]: An error ocurred while sending welcome email')

    return result.to_dict()


# Get user by username
@router.get('/users/{username}')
async def get_user(username: str, response: Response, request: Request):
    user_query = UserService.get_user_by_username(username=username)

    if user_query.is_fail():
        response.status_code = user_query.get_status_code()
        return user_query.to_dict()

    result = Format.format_user(user_query.data)

    try:
        result['photo'] = UserPhotoService.get_user_photo(username)
    except:
        result['photo'] = None

    result['models'] = []

    user_models_result = MLflowService.get_user_models(username)

    if user_models_result.is_fail():
        response.status_code = user_models_result.get_status_code()
        return user_models_result.to_dict()

    for registered_model in user_models_result.data:
        # Get hashtags
        hashtags_result = HashtagService.get_model_hashtags(model_name=registered_model.name)
        hashtags = hashtags_result.data if hashtags_result.is_success() else []
        print("[DEBUG] hashtags_result.is_success():", hashtags_result.is_success())

        # Get API calls
        api_calls_result = ApiCallService.get_model_count(model_name=registered_model.name)
        api_calls = api_calls_result.data['count'] if api_calls_result.is_success() else 0
        print("[DEBUG] api_calls_result.is_success():", api_calls_result.is_success())

        # Get likes
        user_id = None

        # Check if authorization header exists
        if 'Authorization' in request.headers:
            # Get current user
            current_user = await AuthMiddleware.get_current_user(
                str(request.headers['Authorization']).replace('Bearer ', ''))
            user_id = current_user.data.id

        likes_dict = {
            'count': 0,
            'has_liked_model': False
        }

        likes_dict['count'] = ModelLikeService.get_model_likes(model_name=registered_model.name,
                                                               count_only=True).data
        likes_dict['has_liked_model'] = False

        # Check if user liked model
        if user_id:
            user_like = ModelLikeService.get_like(model_name=registered_model.name, user_id=user_id)

            if user_like.is_success() and user_like.data is not None:
                likes_dict['has_liked_model'] = True

        likes = ml_model_schema.Likes(**likes_dict)

        # Get comment count
        comment_count = ModelCommentService.get_model_comments(model_name=registered_model.name, count_only=True)
        comment_count = comment_count.data if comment_count.is_success() else 0

        # Get latest model version
        version = 0 if len(registered_model.latest_versions) == 0 else int(
            registered_model.latest_versions[0].version)

        ml_user = ml_model_schema.User(name=user_query.data.name, username=user_query.data.username)

        try:
            ml_user.photo = UserPhotoService.get_user_photo(user_query.data.username)
        except:
            ml_user.photo = None

        registered_model_dict = ml_model_schema.MlModelListing(name=registered_model.name,
                                                               version=version,
                                                               likes=likes,
                                                               comment_count=comment_count,
                                                               hashtags=hashtags,
                                                               tags=registered_model.tags,
                                                               api_calls=api_calls,
                                                               creation_time=registered_model.creation_timestamp,
                                                               last_update_time=registered_model.last_updated_timestamp,
                                                               user=ml_user,
                                                               description=registered_model.description).dict()
        result['models'].append(registered_model_dict)

    return Result(
        Result.SUCCESS,
        'Collected models successfully',
        result
    ).to_dict()


# Get list of users
@router.get('/users')
def get_users(response: Response, search_query: str = '', page_number: int = 1, results_per_page: int = 10):
    users_query = UserService.get_users(search_query=search_query, page_number=page_number,
                                        results_per_page=results_per_page)
    results = []

    if users_query.is_fail():
        response.status_code = users_query.get_status_code()
        return users_query.to_dict()

    for raw_user in users_query.data:
        user_id = raw_user.id
        user = Format.format_user(raw_user)
        user_hashtags = HashtagService.get_user_hashtags(user_id)
        user_model_hashtags = HashtagService.get_hashtags_from_user_models(user['username'])

        if user_hashtags.is_success():
            user['hashtags'] = user_hashtags.data

        if user_model_hashtags.is_success():
            user['model_hashtags'] = user_model_hashtags.data

        try:
            user['photo'] = UserPhotoService.get_user_photo(user['username'])
        except:
            user['photo'] = None

        results.append(user)

    return Result(
        Result.SUCCESS,
        'Retrieved users successfully',
        results
    ).to_dict()


# Update user
@router.put('/users/{username}', status_code=200)
def update_user(username: str, user: UserSchema.UserUpdate, response: Response,
                current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    # Check if user who's editing is the one that will be edited
    if current_user.data.username != username:
        result = Result(
            Result.FAIL,
            "You don't have permission to edit this user",
            Result.FORBIDDEN
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Check if user exists
    user_exists = UserService.get_user_by_username(username=username)

    if user_exists.is_fail():
        response.status_code = user_exists.get_status_code()
        return user_exists.to_dict()

    result = UserService.update_user(user)

    # Check if user was updated
    if result.is_fail():
        response.status_code = result.get_status_code()
        return result.to_dict()

    result.data = Format.format_user(result.data['updated_user'])

    return result.to_dict()


# Update password
@router.put('/users/{username}/password', status_code=200)
def update_password(username: str, user: UserSchema.UserUpdatePassword, response: Response,
                    current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    # Check if user who's editing is the one that will be edited
    if current_user.data.username != username:
        result = Result(
            Result.FAIL,
            "You don't have permission to edit this user",
            Result.FORBIDDEN
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Check if user exists
    user_exists = UserService.get_user_by_username(username=username)

    if user_exists.is_fail():
        response.status_code = user_exists.get_status_code()
        return user_exists.to_dict()

    # Check if new passwords exist
    if user.new_password is None or user.new_password_confirm is None:
        result = Result(
            Result.FAIL,
            'Missing new password or new password confirmation',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Check if new password and its confirmation match
    if user.new_password != user.new_password_confirm:
        result = Result(
            Result.FAIL,
            'Passwords do not match',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Validate password length
    if len(user.new_password) < 6 or len(user.new_password_confirm) < 6:
        result = Result(
            Result.FAIL,
            'Password length must be at least 6 characters long',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Update password
    updated_password = UserService.update_password(user_id=user_exists.data.id, new_password=user.new_password)

    if updated_password.is_fail():
        response.status_code = updated_password.get_status_code()

    return updated_password.to_dict()


# Delete user
@router.delete('/users/{username}', status_code=200)
def delete_user(username: str, response: Response,
                current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    # Check if user who's deleting is the one that will be deleted
    if current_user.username != username:
        result = Result(
            Result.FAIL,
            "You don't have permission to delete this user",
            Result.FORBIDDEN
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    user = UserService.get_user_by_username(username=username)

    if user.is_fail():
        response.status_code = user.get_status_code()
        return user.to_dict()

    result = UserService.delete_user(username)

    if result.is_fail():
        response.status_code = result.get_status_code()

    return result.to_dict()


# Add user hashtag
@router.post('/users/{username}/hashtags', status_code=200)
def add_user_hashtag(username: str,
                     hashtag: HashtagSchema.HashtagUpdateBase,
                     response: Response,
                     current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    '''
    Adds user hashtag
    '''

    result = HashtagService.add_user_hashtag(user_id=current_user.data.id, value=hashtag.value, key=hashtag.key)

    if result.is_fail():
        response.status_code = result.get_status_code()

    return result.to_dict()


# Delete user hashtag
@router.delete('/users/{username}/hashtags/{hashtag_id}', status_code=200)
def delete_user_hashtag(username: str,
                        hashtag_id: int,
                        response: Response,
                        current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    '''
    Deletes user hashtag
    '''

    result = HashtagService.delete_user_hashtag(user_id=current_user.data.id, hashtag_id=hashtag_id)

    if result.is_fail():
        response.status_code = result.get_status_code()

    return result.to_dict()


# Get user's social networks
@router.get('/users/{user_id}/social-networks', status_code=200)
def get_hashtags(user_id: int, response: Response):
    result = SocialNetworkService.get_social_networks_by_user_id(user_id)

    if result.is_fail():
        response.status_code = result.get_status_code()

    return result.to_dict()


# Get number of registered users
@router.get('/count/users', status_code=200)
def get_user_count(response: Response):
    results = UserService.get_nr_of_registered_users()

    if results.is_fail():
        response.status_code = results.get_status_code()

    return results.to_dict()


# Get current user's model usage
@router.get('/users/me/model-usage', status_code=200)
def get_model_usage_by_user(response: Response,
                            current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    '''
    Gets model usage by user
    '''
    results = ApiCallService.get_recently_used_models(user_id=current_user.data.id)

    if results.is_fail():
        response.status_code = results.get_status_code()

    return results.to_dict()


# Get current user's api calls
@router.get('/users/me/api-calls', status_code=200)
def get_api_calls_by_user(response: Response,
                          current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    '''
    Gets user's API calls
    '''
    query_results = ApiCallService.get_user_calls(user_id=current_user.data.id)

    if query_results.is_fail():
        response.status_code = query_results.get_status_code()

    return query_results.to_dict()

# Upload photo
@router.post('/users/{username}/photo', status_code=200)
def upload_photo(username: str, response: Response, photo: UploadFile = File(...)):
    # Get photo's path
    full_photo_path = UserPhotoService.get_user_photo_path(username)

    # Check if file extension is valid
    if not ImageUploadService.is_valid_extension(content_type=photo.content_type):
        result = Result(
            Result.FAIL,
            'Invalid file extension',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Check if user exists
    user = UserService.get_user_by_username(username=username)

    if user.is_fail():
        response.status_code = user.get_status_code()
        return user.to_dict()

    # Save photo
    try:
        utilities.clear_dir(full_photo_path)
        utilities.create_dir(full_photo_path)
        utilities.save_uploaded_file(full_photo_path, photo)
    except Exception:
        result = Result(
            Result.FAIL,
            'An error occurred while saving photo',
            Result.EXCEPTION
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    return Result(
        Result.SUCCESS,
        'Successfully saved photo'
    ).to_dict()
