from fastapi import APIRouter, Response
from models.result import Result
from services.hashtag_service import HashtagService
from services.api_call_service import ApiCallService
from services.user_service import UserService
import libs.format as Format

router = APIRouter()

# Get hashtags by key
@router.get('/hashtags', status_code = 200)
def get_hashtags(response: Response, key: str = ''):
    results = HashtagService.get_hashtags(key = key)

    if results.is_fail():
        response.status_code = results.get_status_code()
        return results.to_dict()

    results.data = Format.format_hashtag_list(results.data)

    return results.to_dict()

# Get models with hashtag
# @router.get('/model-hashtags', status_code = 200)
# def get_models_with_hashtag(response: Response, hashtag_id: int = 0):
#     if hashtag_id <= 0:
#         result = Result(
#             Result.FAIL,
#             'No hashtag ID provided',
#             Result.NOT_ACCEPTABLE
#         )
#         response.status_code = result.get_status_code()
#         return result.to_dict()
#
#     query_results = HashtagService.get_models_with_hashtag(hashtag_id = hashtag_id)
#     results = []
#
#     if query_results.is_fail():
#         response.status_code = query_results.get_status_code()
#         return query_results.to_dict()
#
#     if len(query_results.data) > 0:
#         for model in query_results.data:
#             model_version = Format.format_model_version(model)
#             model_version['api_calls'] = ApiCallService.get_model_version_count(model_name = model_version['name']).data['count']
#
#             user = UserService.get_user_by_username(model_version['user_id'])
#             if user.is_success():
#                 model_version['user'] = Format.format_user(user.data)
#
#             model_version['hashtags'] = HashtagService.get_model_hashtags(model_name=model_version['name'], model_version=model_version['version']).data
#
#             results.append(model_version)
#
#     query_results.data = results
#
#     return query_results.to_dict()
#
# # Search for models with given hashtag value
# @router.get('/model-hashtags/search', status_code = 200)
# def search_models_with_hashtag(response: Response, hashtag_value: str = ''):
#     # Validate search query
#     if len(hashtag_value) <= 0:
#         result = Result(
#             Result.FAIL,
#             'No search query provided',
#             Result.NOT_ACCEPTABLE
#         )
#         response.status_code = result.get_status_code()
#         return result.to_dict()
#
#     query_results = HashtagService.search_models_with_hashtag(hashtag_value)
#
#     if query_results.is_fail():
#         response.status_code = query_results.get_status_code()
#         return query_results.to_dict()
#
#     results = []
#
#     if len(query_results.data) > 0:
#         for hashtag in query_results.data:
#             hashtag.models = []
#
#             for model in hashtag.hashtag_models:
#                 model_version = Format.format_model_version(model)
#                 model_version['api_calls'] = ApiCallService.get_model_version_count(model_name = model_version['name'], model_version = model_version['version']).data['count']
#
#                 user = UserService.get_user_by_username(model_version['user_id'])
#                 if user.is_success():
#                     model_version['user'] = Format.format_user(user.data)
#
#                 model_version['hashtags'] = HashtagService.get_model_hashtags(model_name=model_version['name'], ).data
#
#                 hashtag.models.append(model_version)
#
#             del hashtag.hashtag_models
#             results.append(hashtag)
#
#     query_results.data = results
#
#     return query_results.to_dict()