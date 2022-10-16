from db.db_config import session
from models.model_version import ModelVersion
from models.result import Result

class ModelVersionService:

    @staticmethod
    def create_model_version(model_version: ModelVersion):
        ''' Create a model version

        :return: a Result object
        '''
        try:
            session.add(model_version)
            session.commit()

            return Result(
                Result.SUCCESS,
                f'Successfully created model version {model_version.version} of {model_version.name}',
                model_version
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to create model version {model_version.version} of {model_version.name}',
                Result.EXCEPTION
            )