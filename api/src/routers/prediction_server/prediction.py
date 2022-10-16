'''
File upload server

This server implements models prediction feature. This prevents the main API from blocking.
'''

import json
from time import sleep

import aiohttp
import middleware.auth as AuthMiddleware
from fastapi import APIRouter, Depends, Response
from fastapi_utils.tasks import repeat_every
from models.prediction_request import PredictionRequest
from models.result import Result
from services.model_serving_service import ModelServingService

aiohttp_session = aiohttp.ClientSession()

model_serving = ModelServingService()

router = APIRouter()


@router.on_event("startup")
@repeat_every(seconds=60)
async def kill_serving_model() -> None:
    print(f'[INFO] Trigger - Kill live models')
    await model_serving.kill()


@router.post('/serving/predict/{model_name}/{model_version}')
async def predict(model_name: str,
                  model_version: int,
                  prediction_req: PredictionRequest,
                  response: Response,
                  current_user=Depends(AuthMiddleware.get_current_user)):
    print(f'[INFO] Model Server - Running prediction for ({model_name}, {model_version})')

    serve_result = await model_serving.serve(model_name, int(model_version))

    # Live model
    if serve_result.is_success():
        port = serve_result.data['port']
        print(f'[INFO] Model Server - Serving SUCCESS')

        retries: int = 0
        while retries < model_serving.MAX_RETRIES:
            retries += 1
            try:
                async with aiohttp_session.post(f'http://127.0.0.1:{port}/invocations',
                                                headers={'Content-Type': 'application/json'},
                                                json=json.loads(prediction_req.json())) as resp:
                    result = await resp.text()

                # Handle error: model crash
                if result is None:
                    result = Result(Result.FAIL,
                                    f'Failed to perform predictions using model ({model_name}, {model_version})',
                                    Result.NOT_ACCEPTABLE)
                    response.status_code = result.get_status_code()
                    return result.to_dict()
                else:
                    # Handle error: mlflow exception
                    # error_code=BAD_REQUEST, error_message=
                    # remove stack_trace from response
                    # https://github.com/mlflow/mlflow/blob/9d9d4b1f1f62de82637e24c1eb1daeec405e6c30/mlflow/pyfunc/scoring_server/__init__.py#L261
                    result_eval = eval(result)
                    if type(result_eval) is dict and (
                            result_eval.get('error_code') or result_eval.get('error_message')):
                        result = Result(Result.FAIL,
                                        f'Failed to perform predictions using model ({model_name}, {model_version})',
                                        Result.NOT_ACCEPTABLE)
                        response.status_code = result.get_status_code()
                        return result.to_dict()
                    # SUCCESS
                    else:
                        return Result(Result.SUCCESS,
                                      f'Successfully performed predictions using model ({model_name}, {model_version})',
                                      result).to_dict()
            except Exception as e:
                print(f'[DEBUG] Retrying model prediction: {retries}.')
                sleep(2 ** retries)

        # failed to predict
        result_fail = Result(Result.FAIL,
                             f'Failed to perform prediction for model ({model_name}, {model_version})',
                             Result.FAIL)
        response.status_code = result_fail.get_status_code()
        return result_fail.to_dict()

    # failed to serve
    else:
        response.status_code = serve_result.get_status_code()
        return serve_result.to_dict()


@router.post('/serving/serve/{model_name}/{version}', status_code=200)
async def serve_model(model_name: str, version: int, response: Response,
                      current_user=Depends(AuthMiddleware.get_current_user)):
    result = await model_serving.serve(model_name, int(version))

    if not result.is_success():
        response.status_code = result.get_status_code()

    return result.to_dict()


@router.post('/serving/kill/{model_name}/{version}', status_code=200)
async def kill_model(model_name: str, version: int, response: Response,
                     current_user=Depends(AuthMiddleware.get_current_user)):
    result = await model_serving.kill_model(model_name, int(version))

    response.status_code = result.get_status_code()
    return result.to_dict()


@router.get('/serving/endpoints', status_code=200)
async def list_models_rest_endpoints(response: Response, current_user=Depends(AuthMiddleware.get_current_user)):
    result = await model_serving.list_endpoints()

    response.status_code = result.get_status_code()
    return result.to_dict()
