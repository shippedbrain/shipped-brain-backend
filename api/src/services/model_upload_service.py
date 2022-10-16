from db.db_config import session
from models.result import Result
from models.model_upload import ModelUpload
from typing import Optional
from datetime import datetime

class ModelUploadService:

    @staticmethod
    def create(user_id: int, model_name: Optional[str]=None, model_version: Optional[int]=None) -> Result:
        try:
            model_upload = ModelUpload(user_id=user_id, model_name=model_name, model_version=model_version)
            session.add(model_upload)
            session.commit()

            return Result(Result.SUCCESS,
                          'Created user model upload record.',
                          model_upload
                          )

        except Exception as e:
            print(f'[EXCEPTION] Could not create model_upload for user with id {user_id}. Exception {e}')
            return Result(Result.FAIL,
                          'Failed to create model_upload record.',
                          Result.EXCEPTION
                          )

    @staticmethod
    def get_by_id(id: int) -> Result:
        ''' Get model upload by id

        :param id: record id

        :return: Result objet with ModelUpload data
        '''
        try:
            model_upload = session.query(ModelUpload).filter(ModelUpload.id == id).first()

            if model_upload is None:
                return Result(
                    Result.FAIL,
                    f'Model upload with id {id} was not found',
                    Result.NOT_FOUND
                )

            return Result(Result.SUCCESS,
                          f'Successfully fetch model upload with id {id}',
                          model_upload
                          )
        except Exception as e:
            print(f'[EXCEPTION] Failed to fetch model_upload with id {id}. Exception {e}')
            return Result(Result.FAIL,
                          f'Failed to fetch model_upload with id {id}',
                          Result.EXCEPTION
                          )

    @staticmethod
    def list(user_id: Optional[int]=None, status: Optional[str]=None) -> Result:
        ''' List model uploads. If both args. are None, list all

        :param user_id: the user's id
        :param status: upload status

        :return: Result objet with ModelUpload data
        '''
        try:
            assert status is None or ModelUpload.is_valid_status(status), f"Bad status value '{status}'"

            model_uploads = None
            if user_id is not None and status is not None:
                model_uploads = session.query(ModelUpload).filter(ModelUpload.user_id == user_id, ModelUpload.status == status).order_by(ModelUpload.id.desc()).all()
            elif user_id is not None:
                model_uploads = session.query(ModelUpload).filter(ModelUpload.user_id == user_id).order_by(ModelUpload.id.desc()).all()
            elif status is not None:
                model_uploads = session.query(ModelUpload).filter(ModelUpload.status == status).order_by(ModelUpload.id.desc()).all()
            else:
                model_uploads = session.query(ModelUpload).order_by(ModelUpload.id.desc()).all()

            return Result(Result.SUCCESS,
                          f'Successfully fetched model_uploads',
                          model_uploads
                          )
        except Exception as e:
            print(f'[EXCEPTION] Failed to list model uploads. Exception {e}')
            return Result(Result.FAIL,
                          f'Failed to list model uploads',
                          Result.EXCEPTION
                          )

    @staticmethod
    def update(id: int,
               model_name: Optional[str]=None,
               model_version: Optional[int]=None,
               status: Optional[str]=None,
               finished_at: Optional[datetime]=None) -> Result:
        ''' Update user model upload

        :param user_id: the user's id
        :param status: upload status
        :param finished_at: finished upload datetime

        :return: Result objet with ModelUpload data
        '''
        assert status is None or ModelUpload.is_valid_status(status), f"Bad status value '{status}'"

        try:
            model_upload = session.query(ModelUpload).filter(ModelUpload.id == id).first()

            if model_upload is None:
                print(f'[DEBUG] Failed to update model upload record. Could not find record with id {id}')
                return Result(Result.FAIL,
                              f'Failed to update model upload record. Could not find record with id {id}',
                              Result.NOT_ACCEPTABLE)

            if status is not None:
                model_upload.status = status
            if finished_at is not None:
                model_upload.finished_at = finished_at
            if model_name is not None:
                model_upload.model_name = model_name
            if model_version is not None:
                model_upload.model_version = model_version

            session.commit()

            return Result(Result.SUCCESS,
                          f'Successfully updated model upload with id {id} ',
                          model_upload)

        except Exception as e:
            print(f'[EXCEPTION] Failed to update model upload with id {id}. Exception {e}')
            return Result(Result.FAIL,
                          f'Failed to update model upload with id {id}',
                          Result.EXCEPTION)
