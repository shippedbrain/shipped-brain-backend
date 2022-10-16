import json
import os
from services.user_photo_service import UserPhotoService
import requests
import aiohttp
import libs.format as Format
import libs.utilities as utilities
import middleware.auth as AuthMiddleware
import schemas.api_call as ApiCallSchema
import schemas.hashtag as HashtagSchema
import schemas.ml_model as ml_model_schema
import schemas.user as UserSchema
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Response, Request
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from models.prediction_request import PredictionRequest
from models.result import Result
from services.api_call_service import ApiCallService
from services.hashtag_service import HashtagService
from services.image_upload_service import ImageUploadService
from services.model_cover_upload_service import ModelCoverUploadService
from services.mlflow_service import MLflowService
from services.model_like_service import ModelLikeService
from services.user_service import UserService
from services.model_comment_service import ModelCommentService
import util.validation as Validation

load_dotenv()
PREDICTION_SERVER = os.getenv('PREDICTION_SERVER')
PREDICTION_SERVER_PORT = os.getenv('PREDICTION_SERVER_PORT')

aiohttp_session = aiohttp.ClientSession()

router = APIRouter()


# Get models
@router.get('/models', status_code=200)
async def get_models(request: Request,
                     response: Response,
                     search_query: str = '',
                     order: str = 'recent',
                     page_number: int = 1, results_per_page: int = 10):
    accepted_orders = ['recent', 'popular', 'recently_used']
    results = []

    query_results_data = []

    # Check if order param exists and if it's accepted
    if order != '' and order not in accepted_orders:
        result = Result(
            Result.FAIL,
            'Order parameter is not valid',
            Result.BAD_REQUEST
        )

        response.status_code = result.get_status_code()
        return result.to_dict()

    # Get models by order param
    if order == 'recent':
        # Get most recent models
        query_results = MLflowService.search_models(model_name=search_query,
                                                    page_number=page_number,
                                                    results_per_page=results_per_page)
        query_results_data = query_results.data

    elif order == 'popular':
        # Get most popular models
        query_results = ApiCallService.get_most_popular_models(search_query=search_query,
                                                               page_number=page_number,
                                                               results_per_page=results_per_page)

        query_results_data = query_results.data['models']

    elif order == 'recently_used':
        user_id = None
        # Check if authorization header exists
        if 'Authorization' in request.headers:
            # Get current user
            current_user = await AuthMiddleware.get_current_user(
                str(request.headers['Authorization']).replace('Bearer ', ''))
            user_id = current_user.data.id

        # Get recently used models
        query_results = ApiCallService.get_recently_used_models(user_id=user_id,
                                                                search_query=search_query,
                                                                page_number=page_number,
                                                                results_per_page=results_per_page)
        query_results_data = query_results.data["models"]

    else:
        query_results = Result(
            Result.FAIL,
            'Order parameter is not valid',
            Result.NOT_ACCEPTABLE
        )

    # Return error
    if query_results.is_fail():
        response.status_code = query_results.get_status_code()
        return query_results.to_dict()

    for registered_model in query_results_data:

        # Validation is necessary because model_version from recently used is already formatted
        if order != 'recently_used':
            # Get user
            user = UserService.get_user_by_username(registered_model.tags['user_id'])
            if user.is_success():
                user = ml_model_schema.User(name=user.data.name, username=user.data.username)

                try:
                    user.photo = UserPhotoService.get_user_photo(user.username)
                except:
                    user.photo = None

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
            version = 0 if len(registered_model.latest_versions) == 0 else int(registered_model.latest_versions[0].version)

            # Get model's cover photo
            cover_photo = None
            try:
                cover_photo = ModelCoverUploadService.get_model_cover_photo(registered_model.name)
            except:
                cover_photo = None

            registered_model_dict = ml_model_schema.MlModelListing(name=registered_model.name,
                                                                   version=version,
                                                                   likes=likes,
                                                                   comment_count=comment_count,
                                                                   hashtags=hashtags,
                                                                   tags=registered_model.tags,
                                                                   api_calls=api_calls,
                                                                   creation_time=registered_model.creation_timestamp,
                                                                   last_update_time=registered_model.last_updated_timestamp,
                                                                   user=user,
                                                                   description=registered_model.description,
                                                                   cover_photo=cover_photo).dict()
            results.append(registered_model_dict)

        # Sorting here is necessary since it won't work when doing it with SQL, because SQL query is guaranteeing
        # that only the latest version of each model is being returned, by sorting by model name and version
        if order == 'recent':
            results = sorted(results, key=lambda x: x['creation_time'], reverse=True)

    return Result(
        Result.SUCCESS,
        'Collected models successfully',
        results
    ).to_dict()


# Get model
@router.get('/models/{model_name}')
def get_model(model_name: str, response: Response, type: str = 'full'):
    # Get model version

    result = MLflowService.get_model(model_name)

    if result.is_success():
        # Format model version
        # if model_version == 0 => no deployment
        model_version = 0 if len(result.data.latest_versions) == 0 else int(result.data.latest_versions[0].version)

        username = result.data.tags["user_id"]

        # Get user
        user = UserService.get_user_by_username(username)

        if user.is_success():
            user = ml_model_schema.User(name=user.data.name, username=user.data.username)

        # Get hashtags
        hashtags_result = HashtagService.get_model_hashtags(model_name=model_name)
        hashtags = hashtags_result.data if hashtags_result.is_success() else []
        print("[DEBUG] hashtags_result.is_success():", hashtags_result.is_success())

        # Get github repo
        github_repo = result.data.tags.get("github_repo")
        github_repo_files_url = Validation.get_github_raw_files_url(url = github_repo) if github_repo else None
        github_repo_readme_url = Validation.get_github_readme_url(url = github_repo) if github_repo else None

        # Get api calls
        api_calls_result = ApiCallService.get_model_count(model_name=model_name)
        api_calls = api_calls_result.data['count'] if api_calls_result.is_success() else 0
        print(f"[DEBUG] api_calls_result.is_success():", api_calls_result.is_success())

        # Get signature & input example
        if model_version == 0:
            signature = result.data.tags.get("signature")
            input_example = result.data.tags.get("input_example")
        else:
            signature_result = MLflowService.get_model_signature(model_name, model_version, result.data.latest_versions[0])
            signature = signature_result.data if signature_result.is_success() else None

            input_example_result = MLflowService.get_input_example(model_name, model_version, result.data.latest_versions[0])
            input_example = input_example_result.data if input_example_result.is_success() else None

            print(f"[DEBUG] signature_result.is_success():", signature_result.is_success())
            print(f"[DEBUG] input_example_result.is_success():", input_example_result.is_success())


        # TODO get metrics from model version
        metrics = json.loads(result.data.tags.get("metrics")) if result.data.tags.get("metrics") else None
        # TODO get parameters from model version
        parameters = json.loads(result.data.tags.get("params")) if result.data.tags.get("params") else None

        likes_dict = {
            'count': 0,
            'has_liked_model': False
        }

        model_likes_result = ModelLikeService.get_model_likes(model_name=model_name,
                                                              count_only=True)
        likes_dict['count'] = model_likes_result.data if model_likes_result.is_success() else 0
        likes_dict['has_liked_model'] = False

        # Check if user liked model
        # ...

        likes = ml_model_schema.Likes(**likes_dict)

        # Get comment count
        comment_count = ModelCommentService.get_model_comments(model_name=model_name, count_only=True)
        comment_count = comment_count.data if comment_count.is_success() else 0

        # Get GitHub repo's README.md
        raw_readme = None
        if github_repo_readme_url:
            try:
                raw_readme = requests.get(f'https://{github_repo_readme_url}').text
            except:
                raw_readme = None

        # Get model's cover photo
        cover_photo = None
        try:
            cover_photo = ModelCoverUploadService.get_model_cover_photo(model_name)
        except:
            cover_photo = None

        # Set Result's data property
        result.data = ml_model_schema.MlModelPage(name=model_name,
                                                  version=model_version,
                                                  metrics=metrics,
                                                  parameters=parameters,
                                                  tags=result.data.tags,
                                                  likes=likes,
                                                  comment_count=comment_count,
                                                  signature=signature,
                                                  input_example=input_example,
                                                  api_calls=api_calls,
                                                  creation_time=result.data.creation_timestamp,
                                                  last_update_time=result.data.last_updated_timestamp,
                                                  description=result.data.description,
                                                  user=user,
                                                  hashtags=hashtags,
                                                  github_repo=github_repo,
                                                  github_repo_files_url=github_repo_files_url,
                                                  github_repo_readme_url=github_repo_readme_url,
                                                  model_card=raw_readme,
                                                  cover_photo=cover_photo).dict()

    else:
        response.status_code = result.get_status_code()

    # Return response
    return result.to_dict()


# Update model version
@router.post('/models/create', status_code=200)
def create_model(response: Response,
                 model: ml_model_schema.MlModelCreate,
                 current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    result = MLflowService.create_registered_model(current_user.data.username, model.name, description=model.description)

    invalid_result = Result(
        Result.FAIL,
        '#key# invalid. Please enter a valid JSON object.',
        Result.NOT_ACCEPTABLE
    )
    has_error: bool = False

    if result.is_success():
        # Validate model's data
        if model.metrics is not None and not Validation.is_valid_json(model.metrics):
            # Metrics
            has_error = True
            invalid_result.message = invalid_result.message.replace('#key#', 'Metrics are')
        elif model.parameters is not None and not Validation.is_valid_json(model.parameters):
            # Parameters
            has_error = True
            invalid_result.message = invalid_result.message.replace('#key#', 'Parameters are')
        elif model.input_example is not None and not Validation.is_valid_json(model.input_example):
            # Input example
            has_error = True
            invalid_result.message = invalid_result.message.replace('#key#', 'Input example is')
        elif model.signature is not None and not Validation.is_valid_json(model.signature):
            # Signature
            has_error = True
            invalid_result.message = invalid_result.message.replace('#key#', 'Signature is')
        elif model.github_repo is not None and not Validation.is_github_repo_valid(model.github_repo):
            # GitHub repository
            has_error = True
            invalid_result.message = 'GitHub repository URL is invalid. URL should look something like: github.com/github_username/github_project'

        if has_error:
            response.status_code = invalid_result.get_status_code()
            return invalid_result.to_dict()
            
        if model.metrics:
            _ = MLflowService.set_metrics(current_user.data.username, model_name=model.name, metrics=model.metrics)
        if model.parameters:
            _ = MLflowService.set_params(current_user.data.username, model_name=model.name, params=model.parameters)
        if model.github_repo:
            _ = MLflowService.set_github_repo(current_user.data.username, model_name=model.name, url=model.github_repo)
        if model.input_example:
            _ = MLflowService.set_input_example(current_user.data.username, model_name=model.name, input_example=model.input_example)
        if model.signature:
            _ = MLflowService.set_signature(current_user.data.username, model_name=model.name, signature=model.signature)
    else:
        response.status_code = result.get_status_code()

    return result.to_dict()


@router.post('/models/metrics/{model_name}', status_code=200)
def set_model_metrics(model_name: str,
                      metrics: ml_model_schema.MlModelMetricsSet,
                      response: Response,
                      current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    """Set model metrics"""
    result = MLflowService.set_metrics(current_user.data.username, model_name, metrics=metrics.metrics)

    return result.to_dict()


@router.post('/models/github-repo/{model_name}', status_code=200)
def set_github_repo(model_name: str,
                    url: ml_model_schema.MlModelGitHubSet,
                    response: Response,
                    current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    """Set model github repo"""
    result = MLflowService.set_github_repo(current_user.data.username, model_name, url=url.url)

    return result.to_dict()


@router.post('/models/parameters/{model_name}', status_code=200)
def set_model_parameters(model_name: str,
                         parameters: ml_model_schema.MlModelParametersSet,
                         response: Response,
                         current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    """Set model parameters"""
    result = MLflowService.set_params(current_user.data.username, model_name, parameters=parameters.parameters)

    return result.to_dict()

@router.post('/models/input_example/{model_name}', status_code=200)
def set_model_input_example(model_name: str,
                         input_example: ml_model_schema.MlModelInputExampleSet,
                         response: Response,
                         current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    """Set model input example"""
    result = MLflowService.set_input_example(current_user.data.username, model_name, input_example=input_example.input_example)

    return result.to_dict()

@router.post('/models/signature/{model_name}', status_code=200)
def set_model_signature(model_name: str,
                         signature: ml_model_schema.MlModelSignatureSet,
                         response: Response,
                         current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    """Set model signature"""
    result = MLflowService.set_signature(current_user.data.username, model_name, signature=signature.signature)

    return result.to_dict()


# Update model version
@router.put('/models/{model_name}', status_code=200)
def update_model(model_name: str,
                 edit_values: ml_model_schema.MlModelEdit,
                 response: Response,
                 current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    """Update model

    Example cURL:
        curl -X PUT "http://localhost:8000/api/v0/models/ElasticNet" -H 'Authorization: Bearer <auth_token>' \
        -H  "accept: application/json" -H  "Content-Type: application/json" \
        -d "{\"name\":\"<model_name>\",\"description\":\"Some description\"}"
    """

    # Update model
    updated_model_result = MLflowService.update_model_description(model_name=model_name,
                                                                  username=current_user.data.username,
                                                                  description=edit_values.description)

    if updated_model_result.is_fail():
        response.status_code = updated_model_result.get_status_code()

    invalid_result = Result(
        Result.FAIL,
        '#key# invalid. Please enter a valid JSON object.',
        Result.NOT_ACCEPTABLE
    )
    has_error: bool = False

    # Validate model's data
    if edit_values.metrics is not None and not Validation.is_valid_json(edit_values.metrics):
        # Metrics
        has_error = True
        invalid_result.message = invalid_result.message.replace('#key#', 'Metrics are')
    elif edit_values.parameters is not None and not Validation.is_valid_json(edit_values.parameters):
        # Parameters
        has_error = True
        invalid_result.message = invalid_result.message.replace('#key#', 'Parameters are')
    elif edit_values.input_example is not None and not Validation.is_valid_json(edit_values.input_example):
        # Input example
        has_error = True
        invalid_result.message = invalid_result.message.replace('#key#', 'Input example is')
    elif edit_values.signature is not None and not Validation.is_valid_json(edit_values.signature):
        # Signature
        has_error = True
        invalid_result.message = invalid_result.message.replace('#key#', 'Signature is')
    elif edit_values.github_repo is not None and not Validation.is_github_repo_valid(edit_values.github_repo):
        # GitHub repository
        has_error = True
        invalid_result.message = 'GitHub repository URL is invalid. URL should look something like: github.com/github_username/github_project'

    if has_error:
        response.status_code = invalid_result.get_status_code()
        return invalid_result.to_dict()

    MLflowService.set_metrics(current_user.data.username, model_name=model_name, metrics=edit_values.metrics) if edit_values.metrics else MLflowService.delete_metrics(current_user.data.username, model_name)
    MLflowService.set_params(current_user.data.username, model_name=model_name, params=edit_values.parameters) if edit_values.parameters else MLflowService.delete_params(current_user.data.username, model_name)
    MLflowService.set_github_repo(current_user.data.username, model_name=model_name, url=edit_values.github_repo) if edit_values.github_repo else MLflowService.delete_github_repo(current_user.data.username, model_name)
    MLflowService.set_input_example(current_user.data.username, model_name=model_name, input_example=edit_values.input_example) if edit_values.input_example else MLflowService.delete_input_example(current_user.data.username, model_name)
    MLflowService.set_signature(current_user.data.username, model_name=model_name, signature=edit_values.signature) if edit_values.signature else MLflowService.delete_signature(current_user.data.username, model_name)

    return updated_model_result.to_dict()


# Delete model version
@router.delete('/models/{model_name}', status_code=200)
def delete_model_version(model_name: str, model_version: int, response: Response,
                         current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    """Delete model version
    """
    result = MLflowService.delete_model_version(username=current_user.data.username,
                                                model_name=model_name,
                                                model_version=model_version)

    if result.is_fail():
        response.status_code = result.get_status_code()

    return result.to_dict()


@router.post('/models/{model_name}/hashtags', status_code=200)
def add_model_hashtag(model_name: str,
                      hashtag: HashtagSchema.HashtagUpdateBase,
                      response: Response,
                      current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    '''
    Create model hashtag
    '''

    result = HashtagService.add_model_hashtag(model_name=model_name, value=hashtag.value, key=hashtag.key)

    if result.is_fail():
        response.status_code = result.get_status_code()

    return result.to_dict()


@router.delete('/models/{model_name}/hashtags/{hashtag_id}', status_code=200)
def delete_model_hashtag(model_name: str,
                         hashtag_id: int,
                         response: Response,
                         current_user: UserSchema.UserBase = Depends(AuthMiddleware.get_current_user)):
    '''
    Deletes model hashtag
    '''

    result = HashtagService.delete_model_hashtag(model_name=model_name, hashtag_id=hashtag_id)

    if result.is_fail():
        response.status_code = result.get_status_code()

    return result.to_dict()


@router.post('/predict/{model_name}')
async def predict(model_name: str,
                  prediction_req: PredictionRequest,
                  response: Response,
                  current_user=Depends(AuthMiddleware.get_current_user)):
    '''Make prediction using model

    Request example: 
        curl -X POST "http://localhost:8000/api/v0/predict/ElasticNet"  \
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJibGMiLCJleHAiOjE2MjY4MTY0MTl9.5LhKKL2gyxrGgF2XHo2QjMcLCQ2ptwRtNOqcPp-qdLk' \
        -H 'accept: application/json' \
        -d '{"columns": ["fixed acidity","volatile acidity","citric acid","residual sugar","chlorides","free sulfur dioxide","total sulfur dioxide","density","pH","sulphates","alcohol"], "index": [0, 1], "data": [[7,0.27,0.36,20.7,0.045,45,170,1.001,3,0.45,8.8], [7,0.27,0.36,20.7,0.045,45,170,1.001,3,0.45,8.8]]}'
    '''
    prediction_json = json.loads(prediction_req.json())
    batch_size = len(prediction_json['data'])

    if batch_size > 10:
        result = Result(
            Result.FAIL,
            'Failed to perform prediction. Batch size is too big!',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Get model
    registered_model_result = MLflowService.get_model(model_name=model_name)
    if registered_model_result.is_fail() or len(registered_model_result.data.latest_versions) == 0:
        return Result(Result.SUCCESS,
                      f"Failed to get deployment endpoint for model with name '{model_name}'. {registered_model_result}",
                      Result.NOT_FOUND)
    model_version = registered_model_result.data.latest_versions[0].version

    # Predict
    # NOTE this is horrible; reuse token (don't know how...)
    access_token, _ = AuthMiddleware.create_access_token(data={'sub': current_user.data.username},
                                                         expires_delta=int(os.getenv('ACCESS_TOKEN_EXPIRATION')))
    try:
        async with aiohttp_session.post(
                f'http://{PREDICTION_SERVER}:{PREDICTION_SERVER_PORT}/api/v0/serving/predict/{model_name}/{model_version}',
                headers={'Authorization': f'Bearer {access_token}'},
                json=prediction_json) as resp:
            predict_result = await resp.text()
            print(f'[DEBUG] predict_result: {predict_result}')

        result = json.loads(predict_result)

        # Log api call
        if result['status'] == Result.SUCCESS:
            api_call_create = ApiCallSchema.ApiCallCreate(user_id=current_user.data.id, model_name=model_name,
                                                          model_version=model_version)
            api_calls = ApiCallService.create_batch(api_call_create, batch_size)

            if api_calls.is_fail():
                response.status_code = api_calls.get_status_code()
                return api_calls.to_dict()

            return result
        else:
            result_fail = Result(
                Result.FAIL,
                f'Could not perform prediction using model ({model_name}, {model_version}). An unexpected error occured.',
                Result.EXCEPTION
            )
            response.status_code = result_fail.get_status_code()
            return result_fail.to_dict()

    except Exception as e:
        print(f'[EXCEPTION] Could not perform prediction using model ({model_name}, {model_version}). Exception: {e}')
        result_fail = Result(Result.FAIL,
                             f'Could not perform prediction using model ({model_name}, {model_version}). An unexpected error occured.',
                             Result.EXCEPTION)
        response.status_code = result_fail.get_status_code()

        return result_fail.to_dict()


# Get model version usage
@router.get('/models/{model_name}/usage')
async def get_model_usage(model_name: str, response: Response, sample: str = 'D'):
    ''' Get total and sampled API calls for model version - sample is a query param
    
    :param model_name: the name of the model
    :param model_version: the version of the model
    :param sample: the  the sample to which to sample count

    :return: a json object with total and sampled api calls 
    Example:
        Get usage by 1 minute interval
        curl http:/localhost:8000/api/v0/model_usage/ElasticNet/1/?sample=1Min
    '''
    sampled_count = ApiCallService.count_by(model_name, sample=sample)

    if sampled_count.is_fail():
        response.status_code = sampled_count.get_status_code()
        return sampled_count.to_dict()

    total_count = 0
    sampled_count_json = json.loads(sampled_count.data['sampled_count'])
    for k in sampled_count_json:
        total_count += sampled_count_json[k]

    results = {'count': total_count,
               'sampled_count': sampled_count.data['sampled_count'],
               'distinct_users_count': sampled_count.data['distinct_users_count']}

    return Result(
        Result.SUCCESS,
        'Successfully fetched model usage',
        results
    ).to_dict()


# Get model versions
@router.get('/versions/{model_name}', status_code=200)
def get_model_versions(model_name: str, response: Response):
    result = MLflowService.list_model_versions(model_name=model_name)
    model_versions = []

    if result.is_fail():
        response.status_code = result.get_status_code()
        return result.to_dict()

    for model_version in result.data:
        model_versions.append(Format.format_model_version(model_version))

    result.data = model_versions

    return result.to_dict()

# Upload cover photo
@router.post('/models/{model_name}/cover', status_code=200)
def upload_cover_photo(model_name: str, response: Response, cover_photo: UploadFile = File(...)):
    # Get cover photo's path
    full_cover_photo_path = ModelCoverUploadService.get_model_cover_photo_path(model_name)

    # Check if file extension is valid
    if not ImageUploadService.is_valid_extension(content_type=cover_photo.content_type):
        result = Result(
            Result.FAIL,
            'Invalid file extension',
            Result.NOT_ACCEPTABLE
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    # Check if model exists
    model = MLflowService.get_model(model_name=model_name)

    if model.is_fail():
        response.status_code = model.get_status_code()
        return model.to_dict()

    # Save cover photo
    try:
        utilities.clear_dir(full_cover_photo_path)
        utilities.create_dir(full_cover_photo_path)
        utilities.save_uploaded_file(full_cover_photo_path, cover_photo)
    except Exception:
        result = Result(
            Result.FAIL,
            'An error occurred while saving cover photo',
            Result.EXCEPTION
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

    return Result(
        Result.SUCCESS,
        'Successfully saved cover photo'
    ).to_dict()
