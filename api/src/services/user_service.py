from services.mlflow_service import MLflowService
from models.model_version import ModelVersion
from db.db_config import session
from sqlalchemy import or_
from models.result import Result
from models.user import User
import schemas.user as UserSchema
import util.validation as Validation


class UserService:

    @staticmethod
    def check_login(user: UserSchema.Login) -> Result:
        try:
            # Get user by email
            user_data = session.query(User).filter_by(email=user.email).first()

            # Return if username was not found
            if user_data is None:
                return Result(
                    Result.FAIL,
                    'Email was not found',
                    Result.NOT_FOUND
                )

            user_data = User(id=user_data.id, email=user_data.email, description=user_data.description,
                             password=user_data.password, name=user_data.name, username=user_data.username,
                             created_at=user_data.created_at, updated_at=user_data.updated_at)

            # Checks password hash and returns false if it doesn't match
            if user_data.check_pw(user.password) is False:
                return Result(
                    Result.FAIL,
                    'Incorrect login credentials',
                    Result.UNAUTHORIZED
                )

            # Remove password property
            delattr(user_data, 'password')

            return Result(
                Result.SUCCESS,
                'Successfully validated login info',
                user_data
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while checking login info',
                Result.EXCEPTION
            )

    @staticmethod
    def create_user(user: UserSchema.UserCreate) -> Result:
        try:
            user_data = User(name=user.name, username=user.username, email=user.email, description=user.description,
                             password=user.password)

            # Trim data
            user_data.name = Validation.trim_whitespaces(user_data.name)
            user_data.username = Validation.trim_whitespaces(user_data.username)
            user_data.email = Validation.trim_whitespaces(user_data.email)

            # Hash password
            user_data.hash_pw(user_data.password)

            session.add(user_data)
            session.commit()

            if user_data.id is None:
                return Result(
                    Result.SUCCESS,
                    'Unable to create user',
                    Result.EXCEPTION
                )

            created_user = UserService.get_user_by_id(user_id=user_data.id)

            if created_user.is_fail():
                return Result(
                    Result.FAIL,
                    'An error occurred while retrieving created user',
                    Result.EXCEPTION
                )

            created_user = created_user.data

            return Result(
                Result.SUCCESS,
                'Successfully created user',
                {
                    'created_user': created_user
                }
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while creating user',
                Result.EXCEPTION
            )

    @staticmethod
    def check_if_user_exists(username: str, email: str) -> Result:
        try:
            result = session.query(User).filter(or_(User.username == username, User.email == email)).first()
            user_exists = result is not None

            return Result(
                Result.SUCCESS,
                'Successfully checked if user exists',
                {
                    'user_exists': user_exists
                }
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while checking if user exists',
                Result.EXCEPTION
            )

    @staticmethod
    def get_user_by_username(username: str) -> Result:
        try:
            result = session.query(User).filter(User.username == username).first()

            if result is None:
                return Result(
                    Result.FAIL,
                    'User was not found',
                    Result.NOT_FOUND
                )

            return Result(
                Result.SUCCESS,
                'Successfully retrieved user',
                result
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving user',
                Result.EXCEPTION
            )

    @staticmethod
    def get_user_by_email(email: str) -> Result:
        try:
            result = session.query(User).filter(User.email == email).first()

            if result is None:
                return Result(
                    Result.FAIL,
                    'Email address was not found',
                    Result.NOT_FOUND
                )

            return Result(
                Result.SUCCESS,
                'Successfully retrieved user',
                result
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving user',
                Result.EXCEPTION
            )

    @staticmethod
    def get_user_by_id(user_id: int) -> Result:
        try:
            result = session.query(User).filter(User.id == user_id).first()

            if result is None:
                return Result(
                    Result.FAIL,
                    'User was not found',
                    Result.NOT_FOUND
                )

            return Result(
                Result.SUCCESS,
                'Successfully retrieved user',
                result
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving user',
                Result.EXCEPTION
            )

    @staticmethod
    def get_users(search_query: str = '', page_number: int = 1, results_per_page: int = 10) -> Result:
        ''' Get users with pagination and filtering

        :param search_query: the name to perform search on, if None returns all
        :page_number: Page number to retrieve
        :param results_per_page: Maximum number of users to retrieve

        :return: Result object containing list of users
        '''

        try:
            offset = results_per_page * page_number - results_per_page
            results = session.query(User).filter(
                or_(User.name.ilike(f'%{search_query}%'), User.username.ilike(f'%{search_query}%'))).order_by(
                User.created_at.desc()).offset(offset).limit(results_per_page).all()

            return Result(
                Result.SUCCESS,
                'Successfully retrieved users',
                results
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving users',
                Result.EXCEPTION
            )

    @staticmethod
    def update_user(user: UserSchema.UserUpdate) -> Result:
        try:
            user_data = session.query(User).filter(User.username == user.username).first()

            user_data.name = user.name
            user_data.email = user.email
            user_data.description = user.description

            session.commit()

            updated_user = UserService.get_user_by_username(user_data.username)

            if updated_user.is_fail():
                return Result(
                    Result.FAIL,
                    'An error occurred while retrieving updated user',
                    Result.EXCEPTION
                )

            updated_user = updated_user.data

            return Result(
                Result.SUCCESS,
                'Successfully updated profile',
                {
                    'updated_user': updated_user
                }
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while updating user',
                Result.EXCEPTION
            )

    @staticmethod
    def update_password(user_id: int, new_password: str) -> Result:
        try:
            # Get user
            user_data = session.query(User).filter(User.id == user_id).first()
            # Hash password
            user_data.hash_pw(new_password)
            # Update user
            session.commit()

            return Result(
                Result.SUCCESS,
                'Successfully updated password',
                {
                    'updated_user': UserService.get_user_by_id(user_id=user_id)
                }
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while updating password',
                Result.EXCEPTION
            )

    @staticmethod
    def delete_user(username: str) -> Result:
        response = session.query(User).filter(User.username == username).delete()

        session.commit()

        result = bool(response)

        if result:
            return Result(
                Result.SUCCESS,
                'Deleted user successfully',
                {
                    'was_deleted': result
                }
            )
        else:
            return Result(
                Result.FAIL,
                'Unable to delete user',
                Result.EXCEPTION
            )

    @staticmethod
    def get_nr_of_registered_users() -> Result:
        try:
            results = session.query(User.id).count()

            return Result(
                Result.SUCCESS,
                'Successfully retrieved number of registered users',
                {
                    'count': results
                }
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving number of registered users',
                Result.EXCEPTION
            )

    @staticmethod
    def count_user_models(username: str) -> Result:
        try:
            models_result = MLflowService.get_user_models(username)

            # raises exception if models_result.is_fail()
            count = len(models_result.data)
            return Result(
                Result.SUCCESS,
                f'User has {count} models',
                count
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving count of models',
                Result.EXCEPTION
            )

    @staticmethod
    def count_user_model_versions(username: str) -> Result:
        try:
            count = session.query(ModelVersion).filter(ModelVersion.user_id == username).count()

            return Result(
                Result.SUCCESS,
                f'User has {count} model versions',
                count
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving count of model versions',
                Result.EXCEPTION
            )
