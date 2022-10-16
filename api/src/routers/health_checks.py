from fastapi import APIRouter
from libs.email_lib import Email
from models.result import Result
from os import getenv

router = APIRouter()

# Test email
@router.get('/emails', status_code = 200)
def test_email() -> Result:
    try:
        Email().send_test_email()

        return Result(
            Result.SUCCESS,
            f"Email sent successfully to {getenv('EMAIL_TEST')}"
        ).to_dict()
    except Exception as e:
        return Result(
            Result.FAIL,
            f'[EMAIL EXCEPTION]: {e}',
            Result.EXCEPTION
        ).to_dict()