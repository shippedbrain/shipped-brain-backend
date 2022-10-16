from services.user_photo_service import UserPhotoService
from fastapi import APIRouter, Depends, Response
from models.result import Result
from services.password_reset_service import PasswordResetService
from services.user_service import UserService
from libs.email_lib import Email
from dotenv import load_dotenv
import schemas.user as UserSchema
import schemas.password_reset as PasswordResetSchema
import middleware.auth as AuthMiddleware
import util.validation as Validation
import libs.format as Format
import os

load_dotenv()

router = APIRouter()

# Login
@router.post('/login', status_code = 200)
def login(response: Response, form_data: UserSchema.Login):
    user = UserService.check_login(user = form_data)

    # Validate login
    if user.is_fail():
        result = Result(
            Result.FAIL,
            'Incorrect email or password',
            Result.UNAUTHORIZED
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Create auth token
    access_token, expiration = AuthMiddleware.create_access_token(data = { 'sub': user.data.username }, expires_delta = int(os.getenv('ACCESS_TOKEN_EXPIRATION')))

    return Result(
        Result.SUCCESS,
        'Logged in successfully',
        {
            'access_token': access_token,
            'token_type': 'bearer',
            'expires': expiration
        }
    ).to_dict()

# Get current user
@router.get('/users/me')
async def get_user(current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    user = Format.format_user(current_user.data)

    try:
        user['photo'] = UserPhotoService.get_user_photo(user['username'])
    except:
        user['photo'] = None

    return Result(
        Result.SUCCESS,
        'Retrieved user successfully',
        user
    ).to_dict()

# Create password reset request
@router.post('/reset-password', status_code = 200)
def create_reset_password_request(password_reset: PasswordResetSchema.PasswordResetCreate, response: Response):
    result = Result(
        Result.FAIL,
        ''
    )

    # Email validation
    if password_reset.user_email is None:
        result.message = 'Please enter an email address'
        result.data = Result.NOT_ACCEPTABLE
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Email whitespaces validation
    if Validation.has_whitespaces(password_reset.user_email):
        result.message = 'Email cannot contain whitespaces'
        result.data = Result.NOT_ACCEPTABLE
        response.status_code = result.get_status_code()
        return result.to_dict()

    user = UserService.get_user_by_email(password_reset.user_email)

    # Check if user email was found
    if user.is_fail():
        result.data = Result.NOT_FOUND
        result.message = 'Email address was not found'
        response.status_code = result.get_status_code()
        return result.to_dict()

    password_reset_data = PasswordResetService.generate_password_reset_token(user_id = user.data.id, email_address = password_reset.user_email)

    # Check if password reset token generation failed
    if password_reset_data.is_fail():
        result.data = Result.EXCEPTION
        result.message = 'We were unable to reset your password at this moment. Please try again later!'
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Send email with password reset info
    try:
        Email().send_password_reset_email(user_name = user.data.name, user_email = password_reset_data.data.data.user_email, reset_token = password_reset_data.data.data.reset_token)
    except Exception as e:
        print('[EMAIL EXCEPTION]: ', str(e))
        result.data = Result.EXCEPTION
        result.message = 'An error occurred while sending password reset instructions to your email address. Please try again later!'
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Return successful response
    return Result(
        Result.SUCCESS,
        'Please follow the instructions we sent to your email to reset your password',
        {
            'sent_to': password_reset_data.data.data.user_email,
            'reset_token': password_reset_data.data.data.reset_token
        }
    ).to_dict()

# Validate reset token
@router.get('/reset-password/{reset_token}', status_code = 200)
def validate_reset_token(reset_token: str, response: Response):
    result = Result(
        Result.FAIL,
        ''
    )

    # Check if reset token is present
    if reset_token is None:
        result.message = 'Missing token'
        result.data = Result.NOT_ACCEPTABLE
        response.status_code = result.get_status_code()
        return result.to_dict()

    password_reset_data = PasswordResetService.get_password_reset_data_by_token(reset_token = reset_token)

    # Check if password reset data exists for provided token
    if password_reset_data.is_fail():
        result.message = 'Password reset request is not valid'
        result.data = Result.NOT_FOUND
        response.status_code = result.get_status_code()
        return result.to_dict()

    user_data = UserService.get_user_by_id(user_id = password_reset_data.data.user_id)

    # Check if user exists
    if user_data.is_fail():
        response.status_code = user_data.get_status_code()
        return user_data.to_dict()
    
    user = Format.format_user(user_data.data)

    return Result(
        Result.SUCCESS,
        'Retrieved password reset data successfully',
        {
            'password_reset_data': password_reset_data.data,
            'user': user
        }
    ).to_dict()

# Reset password
@router.post('/reset-password/{reset_token}', status_code = 200)
def reset_password(reset_token: str, user_password: UserSchema.PasswordResetSchema, response: Response):
    result = Result(
        Result.FAIL,
        ''
    )

    # Check if reset token is present
    if reset_token is None:
        result.message = 'Missing token'
        result.data = Result.NOT_ACCEPTABLE
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Check if new password was provided
    if user_password.password is None:
        result.message = 'New password was not provided'
        result.data = Result.NOT_ACCEPTABLE
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Check if password has whitespaces
    if Validation.has_whitespaces(text = user_password.password):
        result.message = 'Password cannot contain whitespaces'
        result.data = Result.NOT_ACCEPTABLE
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Validate password length
    if len(user_password.password) < 6:
        result.message = 'Password length must be at least 6 characters long'
        result.data = Result.NOT_ACCEPTABLE
        response.status_code = result.get_status_code()
        return result.to_dict()

    password_reset_data = PasswordResetService.get_password_reset_data_by_token(reset_token = reset_token)

    # Check if password reset data was found
    if password_reset_data.is_fail():
        response.status_code = password_reset_data.get_status_code()
        return password_reset_data.to_dict()

    # Get user
    user_data = UserService.get_user_by_id(user_id = password_reset_data.data.user_id)

    # Check if user associated with password reset was not found
    if user_data.is_fail():
        response.status_code = user_data.get_status_code()
        return user_data.to_dict()

    password_update_result = UserService.update_password(user_id = password_reset_data.data.user_id, new_password = user_password.password)

    if password_update_result.is_fail():
        response.status_code = password_update_result.get_status_code()
        return password_update_result.to_dict()

    # Delete reset token
    PasswordResetService.delete_password_reset_for_email(password_update_result.data['updated_user'].data.email)

    user = Format.format_user(password_update_result.data['updated_user'].data)

    return Result(
        Result.SUCCESS,
        'Password updated successfully',
        user
    ).to_dict()