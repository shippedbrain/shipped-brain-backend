from db.db_config import session
from models.result import Result
from models.model_like import ModelLike
from datetime import datetime

class ModelLikeService:

    @staticmethod
    def get_like(model_name: str, user_id: int) -> Result:
        try:
            result = session.query(ModelLike)\
                .filter(ModelLike.model_name == model_name, ModelLike.user_id == user_id)\
                .first()
            
            return Result(
                Result.SUCCESS,
                'Successfully retrieved model like',
                result
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving model like',
                Result.EXCEPTION
            )

    @staticmethod
    def add_like(model_name: str, user_id: int) -> Result:
        try:
            model_like = ModelLike(model_name=model_name, user_id=user_id, created_at=datetime.now())
            session.add(model_like)
            session.commit()

            return Result(
                Result.SUCCESS,
                'Successfully liked model',
                model_like
            )

        except:
            return Result(
                Result.FAIL,
                'An error occurred while adding model like',
                Result.EXCEPTION
            )

    @staticmethod
    def remove_like(model_name: str, user_id: int) -> Result:
        try:
            session.query(ModelLike).filter(ModelLike.model_name == model_name, ModelLike.user_id == user_id).delete()
            session.commit()

            return Result(
                Result.SUCCESS,
                'Successfully removed like'
            )

        except:
            return Result(
                Result.FAIL,
                'An error occurred while removing model like',
                Result.EXCEPTION
            )

    @staticmethod
    def get_model_likes(model_name: str, count_only: bool = False) -> Result:
        try:
            query = session.query(ModelLike)\
                .filter(ModelLike.model_name == model_name)\
                .order_by(ModelLike.created_at.desc())
            results = query.count() if count_only else query.all()
            
            return Result(
                Result.SUCCESS,
                f"Successfully retrieved model {model_name} likes",
                results
            )
        except:
            return Result(
                Result.FAIL,
                f"An error occurred while retrieving model {model_name} likes",
                Result.EXCEPTION
            )

    @staticmethod
    def get_user_model_likes(user_id: int) -> Result:
        try:
            results = session.query(ModelLike).filter(ModelLike.user_id == user_id).order_by(ModelLike.created_at.desc()).all()

            return Result(
                Result.SUCCESS,
                "Successfully retrieved user's model likes",
                results
            )
        except:
            return Result(
                Result.FAIL,
                "An error occurred while retrieving user's model likes",
                Result.EXCEPTION
            )
