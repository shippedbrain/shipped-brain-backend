from db.db_config import session
from models.password_reset import PasswordReset
from models.result import Result

class PasswordResetService:

    @staticmethod
    def generate_password_reset_token(user_id: int, email_address: str) -> Result:
        # Delete previous reset tokens matching email address parameter
        PasswordResetService.delete_password_reset_for_email(email_address)

        password_reset_data = PasswordReset(user_id = user_id, user_email = email_address)
        password_reset_data.generate_token()

        session.add(password_reset_data)
        session.commit()

        if password_reset_data.id is None:
            return Result(
                Result.FAIL,
                'Unable to create password reset info',
                Result.EXCEPTION
            )

        try:
            results = PasswordResetService.get_password_reset_data(password_token_id = password_reset_data.id)

            return Result(
                Result.SUCCESS,
                'Successfully generated password reset info',
                results
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while generating password reset info',
                Result.EXCEPTION
            )

    @staticmethod
    def get_password_reset_data(password_token_id: int) -> Result:
        try:
            result = session.query(PasswordReset).filter(PasswordReset.id == password_token_id).first()

            if result is None:
                return Result(
                    Result.FAIL,
                    'Password reset request was not found',
                    Result.NOT_FOUND
                )

            return Result(
                Result.SUCCESS,
                'Successfully retrieved password reset data',
                result
            )
        except:
            return Result(
                Result.FAIL,
                'An error ocurred while retrieving password reset info',
                Result.EXCEPTION
            )

    @staticmethod
    def get_password_reset_data_by_token(reset_token: str) -> Result:
        result = session.query(PasswordReset).filter(PasswordReset.reset_token == reset_token).first()

        if result is None:
            return Result(
                Result.FAIL,
                'Password reset request was not found',
                Result.NOT_FOUND
            )

        return Result(
            Result.SUCCESS,
            'Successfully retrieved password reset data',
            result
        )

    @staticmethod
    def delete_password_reset_for_email(email_address: str) -> Result:
        try:
            response = session.query(PasswordReset).filter(PasswordReset.user_email == email_address).delete()
            session.commit()
            result = bool(response)

            return Result(
                Result.SUCCESS,
                'Deleted password reset info',
                {
                    'was_deleted': result
                }
            )
        except:
            return Result(
                Result.FAIL,
                'An error ocurred while deleting password reset data',
                Result.EXCEPTION
            )