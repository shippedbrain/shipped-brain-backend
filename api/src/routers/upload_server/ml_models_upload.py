'''
File upload server

This server implements the model deployment and project upload feature. This prevents the main API from blocking.  
'''
import os
import tempfile
from datetime import datetime
from typing import Optional, Tuple

import libs.utilities as Utilities
import middleware.auth as AuthMiddleware
from config.config import MODEL_UPLOAD_SERVICE_CONFIG
from fastapi import APIRouter, File, UploadFile, Depends, Response, BackgroundTasks
from fastapi_utils.tasks import repeat_every
from libs.email_lib import Email
from models.model_upload import ModelUpload
from models.result import Result
from services.mlflow_service import MLflowService
from services.model_registry_service import ModelRegistryService
from services.model_upload_service import ModelUploadService
from services.user_service import UserService

router = APIRouter()


# @router.on_event("startup")
# @repeat_every(seconds=60)
# async def update_model_uploads() -> None:
#     print(f'[INFO] Trigger - Update model upload table')
#     now = datetime.now()
#     running_model_uploads_result = ModelUploadService.list(staus="running")
#     ttl = 60 * 5  # 5 minutes
#     if running_model_uploads_result.is_success():
#         running_model_uploads = running_model_uploads_result.data
#         for rmu in running_model_uploads:
#             time_delta = now - rmu.started_at
#             if time_delta.seconds >= ttl:
#                 ModelUploadService.update(user_id=rmu.id, status="failed")
#                 user_result = UserService.get_user_by_id(rmu.id)
#                 if user_result.is_success():
#                     username = user_result.data.username
#                     access_token, _ = AuthMiddleware.create_access_token(data={'sub': username},
#                                                                          expires_delta=int(
#                                                                              os.getenv('ACCESS_TOKEN_EXPIRATION')))
#                     send_email(access_token=access_token, success=False, deployment_id=rmu.id)


def send_email(access_token: Result,
               model_name_version: Optional[Tuple[str, int]] = None,
               success: bool = True,
               deployment_id: Optional[int] = None,
               message: Optional[str] = None) -> Result:
    try:
        if success:
            print('[INFO] Sending model deployment SUCCESS e-mail.')
            Email().send_deployed_model_email(user_name=access_token.data.name,
                                              user_email=access_token.data.email,
                                              model_name=model_name_version[0],
                                              model_version=model_name_version[1])
        else:
            print('[INFO] Sending model deployment FAIL e-mail.')
            Email().send_failed_deployed_model_email(user_name=access_token.data.name,
                                                     user_email=access_token.data.email,
                                                     deployment_id=deployment_id)
    except Exception as e:
        print(f'[EXCEPTION] An error occurred while sending an email confirming model deployment status. Exception {e}')
        return Result(
            Result.FAIL,
            'An error occurred while sending an email confirming model deployment status',
            Result.EXCEPTION
        )

    return Result(Result.SUCCESS,
                  'Successfully submitted model deployment job.',
                  Result.SUCCESS)


# Background task
def upload_file_and_register_model(access_token: Result,
                                   file: UploadFile,
                                   user_model_upload_result: Result,
                                   response) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:

        # Save file
        try:
            uploaded_model = Utilities.save_uploaded_file(dir=tmpdir, file=file)

        except Exception as e:
            print(f'[EXCEPTION] An error occurred while saving file. Exception: {e}')
            # ModelUpdate - update completion
            _ = ModelUploadService.update(user_model_upload_result.data.id,
                                          status=ModelUpload.FAILED,
                                          finished_at=datetime.now())

            _ = send_email(access_token, success=False, deployment_id=user_model_upload_result.data.id)

        # Register model
        try:
            uploaded_model_zip = os.path.join(tmpdir, file.filename)

            print("[INFO] Registrying model...")
            register_model_result = ModelRegistryService.register_model(uploaded_model_zip, access_token.data.username)

            print(f"[DEBUG] Register model result.is_success(): {register_model_result.is_success()}")
            print(f"[DEBUG] Register model result: {register_model_result.data}")

            if register_model_result.is_success():
                model_version = register_model_result.data
                ModelRegistryService.update_model_owner(access_token.data.username, run_id=model_version.run_id)
                #ModelRegistryService.inherit_model_hashtags(model_version.name, int(model_version.version))

                # Update upload state
                # ModelUpdate - update completion
                print(f"[INFO] Model uploaded successfully.")

                _ = ModelUploadService.update(user_model_upload_result.data.id,
                                              model_name=model_version.name,
                                              model_version=int(model_version.version),
                                              status=ModelUpload.FINISHED,
                                              finished_at=datetime.now())

                _ = send_email(access_token, model_name_version=(model_version.name, int(model_version.version)),
                               success=True)

            else:
                print(f"[INFO] Failed to register model! {register_model_result.message}")
                # Update upload state
                # ModelUpdate - update completion
                _ = ModelUploadService.update(user_model_upload_result.data.id,
                                              status=ModelUpload.FAILED,
                                              finished_at=datetime.now())

                _ = send_email(access_token, success=False, deployment_id=user_model_upload_result.data.id)

        except Exception as e:
            print(f"[INFO] Failed to register model! ERROR: {e}")
            # Update upload state
            # ModelUpdate - update completion
            _ = ModelUploadService.update(user_model_upload_result.data.id,
                                          status=ModelUpload.FAILED,
                                          finished_at=datetime.now())

            _ = send_email(access_token, success=False, deployment_id=user_model_upload_result.data.id)


# Upload model zip file and deploy
@router.post('/uploads/deploy', status_code=200)
async def upload_model_file_and_deploy(response: Response,
                                       background_task: BackgroundTasks,
                                       file: UploadFile = File(...),
                                       access_token=Depends(AuthMiddleware.get_current_user)):
    ''' Upload zip file and deploy project. Requires API access token

    Request example:
        curl -X POST "http://localhost:8001/uploads/deploy" -H 'Authorization: Bearer <access_token>' -F "file=@/path/to/zip_file"  -F 'description="Some model Description"'
    
        curl -X POST "http://localhost:8001/uploads/deploy" -H "Content-Type: multipart/form-data"  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJibGMiLCJleHAiOjE2MTY0MDYwNzN9.L2cErdoh3HQlMgO1_u4yhP2FKzYMC51coo9J-Y8nsz8' -F "file=@/home/blc/ShippedBrain/shipped-brain-ui/api/src/examples/libs/mlflow_wrapper/sklearn_elasticnet_wine.zip"
    '''
    accepted_extensions = [
        'application/zip',
        'application/x-zip-compressed',
        'application/octet-stream',
        'multipart/form-data'
    ]

    # TODO ModelUpload.QUEUED
    all_model_uploads_result = ModelUploadService.list(status=ModelUpload.RUNNING)

    ##### Server is running max number of uploads #####
    if all_model_uploads_result.is_success() and len(all_model_uploads_result.data) >= MODEL_UPLOAD_SERVICE_CONFIG[
        'max_concurrent_uploads_all']:
        print('[INFO] Cannot register any models. Too many uploads are running or queued.')
        result = Result(
            Result.FAIL,
            'We are sorry. We are experiencing a lot of traffic. You cannot register any models at the moment. Please try again later.',
            Result.FORBIDDEN
        )
        response.status_code = result.get_status_code()

        return result.to_dict()

    ##### User is already uploading a model #####
    user_model_uploads_result = ModelUploadService.list(user_id=access_token.data.id, status=ModelUpload.RUNNING)
    if user_model_uploads_result.is_success() and len(user_model_uploads_result.data) >= MODEL_UPLOAD_SERVICE_CONFIG[
        'max_concurrent_uploads_user']:
        print('[INFO] Cannot register any models. Upload is running or queued.')
        result = Result(
            Result.FAIL,
            'You cannot register any models at the moment. Model is being uploaded. Please upgrade your user limits or try again later.',
            Result.FORBIDDEN
        )
        response.status_code = result.get_status_code()

        return result.to_dict()

    # Create model_upload record
    user_model_upload_result = ModelUploadService.create(access_token.data.id)
    # TODO check integrity

    #### Bad file foramt - Update ModelUpload status to ####
    if file.content_type not in accepted_extensions:
        print(f"[WARN] BAD file content type: {file.content_type}")
        # ModelUpdate - update completion
        _ = ModelUploadService.update(user_model_upload_result.data.id,
                                      status=ModelUpload.FAILED,
                                      finished_at=datetime.now())

        result = Result(
            Result.FAIL,
            'Invalid extension for file upload',
            Result.NOT_ACCEPTABLE
        )

        response.status_code = result.get_status_code()

        return result.to_dict()

    try:
        print("[INFO] Registering model as bg task")
        #### Upload model as background task ####
        background_task.add_task(upload_file_and_register_model,
                                 access_token,
                                 file,
                                 user_model_upload_result,
                                 response)

        return Result(
            Result.SUCCESS,
            'Successfully submitted model deployment job.',
            Result.SUCCESS).to_dict()
    except Exception as e:
        result = Result(
            Result.FAIL,
            e,
            Result.EXCEPTION
        )
        response.status_code = result.get_status_code()
        return result.to_dict()
