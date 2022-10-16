from datetime import datetime
from typing import Optional

import schemas.api_call as ApiCallSchema
from db.db_config import session
from models.api_call import ApiCall
from models.registered_model import RegisteredModel
from models.result import Result
from services.mlflow_service import MLflowService
from sqlalchemy import func
from sqlalchemy.sql import text


class ApiCallService:

    @staticmethod
    def create(api_call_create: ApiCallSchema.ApiCallCreate) -> Result:
        ''' Create an api call

        :param api_call_create: an ApiCallCreate object

        :return: and ApiCall object, None on exception
        '''
        try:
            api_call = ApiCall(user_id=api_call_create.user_id,
                               model_name=api_call_create.model_name,
                               call_time=datetime.now())
            session.add(api_call)
            session.commit()

            return Result(
                Result.SUCCESS,
                'Created API call',
                api_call
            )
        except Exception as e:
            print(f'[EXCEPTION] ApiCallService.create. Exception: {e}')
            return Result(
                Result.FAIL,
                'An error occurred while creating API call',
                Result.EXCEPTION
            )

    @staticmethod
    def create_batch(api_call_create: ApiCallSchema.ApiCallCreate, batch_size: int) -> Result:
        ''' Create an api call for each observation in batch

        :param api_call_create: an ApiCallCreate object
        :param batch_size: the size of the batch used in prediction

        :return: a list of ApiCall object, None on exception
        '''
        try:
            api_calls = []
            # A batch prediction is considered originates from a single call, 
            # thus th time of the API call is the same for every single inference
            call_time = datetime.now()
            for i in range(batch_size):
                api_call = ApiCall(user_id=api_call_create.user_id,
                                   model_name=api_call_create.model_name,
                                   call_time=call_time)
                session.add(api_call)
                api_calls.append(api_call)
            # Bulk insert
            session.commit()

            return Result(
                Result.SUCCESS,
                'Created API call batch',
                api_calls
            )
        except Exception as e:
            print(f'[EXCEPTION] ApiCallService.create_batch. Exception: {e}')
            return Result(
                Result.FAIL,
                'An error occurred while creating API call batch',
                Result.EXCEPTION
            )

    @staticmethod
    def get_model_count(model_name: str) -> Result:
        ''' Get total number of API call for a model version

        :param model_name: the model name

        :return: a Result object with the total count of API calls
        '''
        try:
            qr = session.query(func.count(ApiCall.model_name)).filter(ApiCall.model_name == model_name)

            count = qr.scalar()
            return Result(
                Result.SUCCESS,
                f"Successfully counted the number of api calls from model with name '{model_name}'.",
                {
                    'count': count
                }
            )
        except Exception as e:
            print(f'[EXCEPTION] ApiCallService.get_model_version_count. Exception: {e}')
            return Result(
                Result.FAIL,
                f"Failed to count the number of api calls from model with name '{model_name}'.",
                Result.EXCEPTION
            )

    @staticmethod
    def count_by(model_name: str, sample='D') -> Result:
        ''' Count number of api calls of model by day, week or month sample (or whatever)
        
        :param model_name: the model name
        :param sample: the sample to which to count the api call:
                        see: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.resample.html
                        day: 'D'
                        week: 'W'
                        month: 'M'
                        1 minute: '1Min'

        :return: If model has usage returns a json object with format: 
                    {"sampled_count": {"data_time_value_1": <count_1>, ..., "data_time_value_n": <count_n>}}
                 Otherwise returns empty dict: {"sampled_count": {}}
        '''
        try:
            import pandas as pd
            # TODO can count==0?
            qr = session.query(ApiCall).filter(ApiCall.model_name == model_name)

            table = pd.read_sql_query(qr.statement,
                                      session.bind,
                                      index_col='call_time',
                                      parse_dates=['call_time'])  # , chunksize=<n_rows>
            sampled_count = table['id'].resample(sample).count().to_json()
            distinct_users_count = table['user_id'].nunique()

            return Result(
                Result.SUCCESS,
                f'Successfully counted model usage with name \'{model_name}\' using sample \'{sample}\'',
                {
                    'sampled_count': sampled_count,
                    'distinct_users_count': distinct_users_count
                }
            )
        except Exception as e:
            print(f'[EXCEPTION] ApiCallService.count_by. Exception: {e}')
            return Result(
                Result.FAIL,
                f'Failed to count model usage with name \'{model_name}\'  using sample \'{sample}\'.',
                Result.EXCEPTION
            )

    @staticmethod
    def get_recently_used_models(user_id: Optional[int] = None, page_number: int = 0,
                                 results_per_page: int = 10) -> Result:
        ''' Get recently used models by user, (optional) by user
        
        :page_number: Page number to retrieve
        :param results_per_page: Maximum number of registered models desired

        :return: a Result object with Result.data as a list of RegisteredModel dict objects format
        '''
        try:
            query = session.query(ApiCall.model_name, func.max(ApiCall.call_time).label("max_call_time"))

            if user_id is not None:
                query = query.filter(ApiCall.user_id == user_id)

            page_number += 1
            offset = results_per_page * page_number - results_per_page
            offset = 0

            # TODO This won't show models with count 0
            query_result = query.group_by(ApiCall.model_name) \
                .order_by(text('max_call_time DESC')) \
                .offset(offset) \
                .limit(results_per_page) \
                .all()

            recently_used_models = []
            # TODO fallback plan when query_result==0
            if len(query_result) > 0:
                for qr in query_result:
                    registered_model = MLflowService.get_model(model_name=qr.model_name)

                    # TODO check format
                    if registered_model.is_success():
                        recently_used_models.append(
                            {
                                'description': registered_model.data.description,
                                'name': registered_model.data.name,
                                'user_id': registered_model.data.tags["user_id"],
                                'version': 0,
                                "call_time": qr.max_call_time
                            }
                        )

            return Result(
                Result.SUCCESS,
                'Collected recently used models successfully',
                {
                    'models': recently_used_models,
                    'page_number': page_number,
                    'results_per_page': results_per_page
                }
            )
        except Exception as e:
            print(f'[EXCEPTION] ApiCallService.get_recently_used_models. Exception: {e}')
            return Result(
                Result.FAIL,
                'Failed to get recently used models',
                Result.EXCEPTION
            )

    @staticmethod
    def get_most_popular_models(search_query: str = '', page_number: int = 0, results_per_page: int = 10) -> Result:
        ''' Get most popular models by user
        
        :param search_query: the name to perform search on, if None returns all
        :page_number: Page number to retrieve
        :param results_per_page: Maximum number of registered models desired

        :return: a Result object with Result.data as a list of RegisteredModel dict objects format
        '''
        try:

            # TODO This won't show models with count 0
            page_number += 1
            offset = results_per_page * page_number - results_per_page

            query_result = session.query(ApiCall.model_name, func.count(ApiCall.model_name).label('model_name_count')) \
                .filter(ApiCall.model_name.ilike(f'%{search_query}%')) \
                .group_by(ApiCall.model_name) \
                .order_by(func.count(ApiCall.model_name).desc()) \
                .offset(offset) \
                .limit(results_per_page) \
                .all()

            most_popular_models = []
            for qr in query_result:
                registered_model = MLflowService.get_model(model_name=qr[0])  # , version = qr[1])

                if registered_model.is_success():
                    most_popular_models.append(registered_model.data)

            return Result(
                Result.SUCCESS,
                'Successfully collected most popular models.',
                {
                    'models': most_popular_models,
                    'page_number': page_number,
                    'results_per_page': results_per_page
                }
            )
        except Exception as e:
            print(f'[EXCEPTION] ApiCallService.get_most_popular_models. Exception: {e}')
            return Result(
                Result.FAIL,
                'Failed to get most popular models.',
                Result.EXCEPTION
            )

    @staticmethod
    def get_user_calls(user_id: int) -> Result:
        ''' Get API call for a user

        :param user_id: the user's id
        
        :return: a Result object with API calls for user
        '''
        try:
            results = session.query(ApiCall).filter(ApiCall.user_id == user_id) \
                .join(RegisteredModel, RegisteredModel.name == ApiCall.model_name) \
                .order_by(ApiCall.call_time.desc()) \
                .all()

            return Result(
                Result.SUCCESS,
                f"Successfully retrieved api calls",
                results
            )
        except Exception as e:
            print(f'[EXCEPTION] ApiCallService.get_user_calls. Exception: {e}')
            return Result(
                Result.FAIL,
                f"Failed to retrieve api calls",
                Result.EXCEPTION
            )

    @staticmethod
    def get_model_calls(model_name: str) -> Result:
        ''' Get API call for a model

        :param model_name: the model's name

        :return: a Result object with API calls for model
        '''
        try:
            results = session.query(ApiCall)\
                .filter(ApiCall.model_name == model_name)\
                .order_by(ApiCall.call_time.desc())\
                .all()

            return Result(
                Result.SUCCESS,
                f"Successfully retrieved api calls for model '{model_name}'",
                results
            )
        except Exception as e:
            print(f'[EXCEPTION] ApiCallService.get_user_calls. Exception: {e}')
            return Result(
                Result.FAIL,
                f"Failed to retrieve api calls",
                Result.EXCEPTION
            )

    @staticmethod
    def get_user_calls_count(user_id: int) -> Result:
        ''' Get total number of API call for a user

        :param user_id: the user's id
        
        :return: a Result object with the total count of API calls for user
        '''
        try:
            results = session.query(ApiCall).filter(ApiCall.user_id == user_id).count()

            return Result(
                Result.SUCCESS,
                f"Successfully counted the number of api calls",
                results
            )
        except Exception as e:
            print(f'[EXCEPTION] ApiCallService.get_user_calls_count. Exception: {e}')
            return Result(
                Result.FAIL,
                f"Failed to count the number of api calls",
                Result.EXCEPTION
            )
