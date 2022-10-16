from datetime import datetime
from os import stat
from db.db_config import session
from models.result import Result
from models.model_request import ModelRequest
import schemas.model_request as ModelRequestSchema

class ModelRequestService:

    @staticmethod
    def create_model_request(model_request: ModelRequestSchema.ModelRequestCreate) -> Result:
        ''' Creates a new model request

        :param model_request: Model request schema

        :return: Result object
        '''

        try:
            model_request_data = ModelRequest(
                requested_by = model_request.requested_by, 
                title = model_request.title, 
                description = model_request.description, 
                input_data = model_request.input_data, 
                output_data = model_request.output_data, 
                status = ModelRequest.OPEN,
                prize = model_request.prize, 
                created_at = datetime.now(), 
                updated_at = datetime.now())

            session.add(model_request_data)
            session.commit()

            if model_request_data.id is None:
                return Result(
                    Result.FAIL,
                    'Unable to create model request',
                    Result.EXCEPTION
                )

            return Result(
                Result.SUCCESS,
                'Successfully created model request',
                model_request_data
            )
        except Exception as e:
            return Result(
                Result.FAIL,
                'An error occurred while creating model request',
                Result.EXCEPTION
            )

    @staticmethod
    def get_model_requests(status: str = '', search_query: str = '') -> Result:
        ''' Gets list of model requests

        :param status: Optional parameter to filter model requests. If status is empty, all model requests will be retrieved
        :param search_query: Optional parameter to search model requests

        :return: Result object with list of model requests
        '''

        try:
            results = session.query(ModelRequest).filter(ModelRequest.status.ilike(f'%{status}%'), ModelRequest.title.ilike(f'%{search_query}%')).order_by(ModelRequest.created_at.desc()).all()

            return Result(
                Result.SUCCESS,
                'Successfully retrieved model requests',
                results
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving model requests',
                Result.EXCEPTION
            )

    @staticmethod
    def get_model_request(model_request_id: int) -> Result:
        ''' Gets model request by ID

        :param model_request_id: Model request ID

        :return: Result object with model request data
        '''

        try:
            result = session.query(ModelRequest).filter(ModelRequest.id == model_request_id).first()

            if result is None:
                return Result(
                    Result.FAIL,
                    'Model request was not found',
                    Result.NOT_FOUND
                )

            return Result(
                Result.SUCCESS,
                'Successfully retrieved model request',
                result
            )
        except:
            return Result(
                Result.FAIL,
                'An error occurred while retrieving model request',
                Result.EXCEPTION
            )