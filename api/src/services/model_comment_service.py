from db.db_config import session
from datetime import datetime
from models.result import Result
from models.model_comment import ModelComment

class ModelCommentService:
    
    @staticmethod
    def add_comment(model_name: str, user_id: int, comment: str) -> Result:
        '''Save comment to model

        :param model_name: Model to add comment to
        :param user_id: Commenter's ID
        :param comment: Comment's text content

        :return: Result object
        '''
        try:
            model_comment = ModelComment(model_name=model_name, user_id=user_id, comment=comment, created_at=datetime.now())
            session.add(model_comment)
            session.commit()

            return Result(
                Result.SUCCESS,
                'Successfully added comment',
                model_comment
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while adding comment',
                Result.EXCEPTION
            )

    @staticmethod
    def get_model_comments(model_name: str, count_only: bool = False, page_number: int = 1, results_per_page: int = 10) -> Result:
        '''Get model's comments

        :param model_name: Model to get comments from
        :param count_only: When True, method will only return number of comments, otherwise comments are returned
        :param page_number: Page number to retrieve
        :param results_per_page: Maximum number of comments to retrieve

        :return: Result object
        '''
        try:
            query = session.query(ModelComment)\
                .filter(ModelComment.model_name == model_name)\
                .order_by(ModelComment.created_at.desc())

            if not count_only:
                offset = results_per_page * page_number - results_per_page
                query = query.offset(offset).limit(results_per_page)

            results = query.count() if count_only else query.all()

            return Result(
                Result.SUCCESS,
                'Successfully retrieved comments',
                results
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving comments',
                Result.EXCEPTION
            )

    @staticmethod
    def get_comment(comment_id: int) -> Result:
        '''Get comment by ID

        :param comment_id: ID of comment to retrieve

        :return: Result object
        '''
        try:
            comment = session.query(ModelComment).filter(ModelComment.id == comment_id).first()

            if comment is None:
                return Result(
                    Result.FAIL,
                    'Comment not found',
                    Result.NOT_FOUND
                )

            return Result(
                Result.SUCCESS,
                'Successfully retrieved comment',
                comment
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving comment',
                Result.EXCEPTION
            )

    @staticmethod
    def delete_comment(comment_id: int) -> Result:
        '''Delete comment from model by ID

        :param comment_id: Comment to delete

        :return: Result object
        '''
        try:
            response = session.query(ModelComment).filter(ModelComment.id == comment_id).delete()
            session.commit()
            result = bool(response)

            if result:
                return Result(
                    Result.SUCCESS,
                    'Deleted comment successfully',
                    {
                        'was_deleted': result
                    }
                )
            else:
                return Result(
                    Result.FAIL,
                    'Unable to delete comment',
                    Result.EXCEPTION
                )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while deleting comment',
                Result.EXCEPTION
            )
