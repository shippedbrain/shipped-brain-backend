from dotenv import load_dotenv
from typing import Optional, Dict, Any, Union
import mlflow.pyfunc
from models.model_version import ModelVersion
from models.result import Result
from db.db_config import session
from sqlalchemy import desc
import yaml
import json
from models.registered_model_tag import RegisteredModelTag
import util.validation as Validation

# This is needed; set mlflow tracking uri to MLFLOW_TRACKING_URI
load_dotenv()


class MLflowService:
    """
    Exposes and extends MLflow functionalities
    """
    tracking_uri: str = mlflow.tracking.get_tracking_uri()

    client = mlflow.tracking.MlflowClient()

    STAGING: str = 'Staging'
    PRODUCTION: str = 'Productions'
    ARCHIVED: str = 'Archived'
    ASC: str = 'ASC'
    DESC: str = 'DESC'
    DELETED_STAGE: str = 'Deleted_Internal'
    METRICS_TAG: str = 'metrics'
    PARAMS_TAG: str = 'params'
    GITHUB_REPO_TAG: str = 'github_repo'
    INPUT_EXAMPLE_TAG: str = 'input_example'
    SIGNATURE_TAG: str = 'signature'

    @staticmethod
    def _is_valid_stage(stage: str) -> bool:
        """Verifies that stage is valid

        :param stage: the specified stage

        :return: True if stage has valid name, otherwise False
        """

        return stage == MLflowService.STAGING or stage == MLflowService.PRODUCTION or stage == MLflowService.ARCHIVED

    @staticmethod
    def list_model_versions(model_name: str) -> Result:
        """List model versions

        :param model_name: the name of the model to search

        :return: a PagedList of mlflow.entities.model_registry.ModelVersion objects, None on exception.
        """
        try:
            results = session.query(ModelVersion) \
                .filter(ModelVersion.name == model_name, ModelVersion.current_stage != MLflowService.DELETED_STAGE) \
                .order_by(ModelVersion.version.desc()) \
                .all()

            return Result(
                Result.SUCCESS,
                f'Collected model versions of {model_name} successfully',
                results
            )
        except Exception as e:
            print(f'[EXCEPTION] Failed to collect model versions of {model_name}. Exception: {e}')

            return Result(
                Result.FAIL,
                f'Failed to collect model versions of {model_name}',
                Result.EXCEPTION
            )

    @staticmethod
    def get_model_version(model_name: str, version: Optional[int]) -> Result:
        ''' Get model version by name. Gets latest version unless otherwise specified

        :param model_name: Model name
        :param version: Model version

        :return A single ModelVersion
        '''
        try:
            model = MLflowService.client.get_model_version(name=model_name, version=version)

            if model is None:
                return Result(
                    Result.FAIL,
                    f'Version {version} of {model_name} was not found',
                    Result.NOT_FOUND
                )

            return Result(
                Result.SUCCESS,
                f'Collected version {version} of {model_name} successfully',
                model
            )

        except Exception as e:
            print(f'[EXCEPTION] Failed to collect version {version} of {model_name}. Exception: {e}')
            return Result(
                Result.FAIL,
                f'Failed to collect version {version} of {model_name}',
                Result.EXCEPTION
            )

    @staticmethod
    def get_model(model_name):
        try:
            return Result(Result.SUCCESS,
                          f"Successfully fetched model with name '{model_name}'",
                          MLflowService.client.get_registered_model(model_name))
        except:
            return Result(Result.FAIL,
                          f"Failed to get model with name '{model_name}'",
                          Result.EXCEPTION)

    @staticmethod
    def search_models(model_name: str = '',
                      page_number: int = 1,
                      results_per_page: int = 10) -> Result:
        ''' Search for model versions by name in backend that satisfy the filter criteria [name]

        :param model_name: the name to perform search on, if None returns all
        :param page_number: Page number to retrieve
        :param results_per_page: Maximum number of registered models desired

        :return: Result object containing list of models
        '''

        try:
            offset = results_per_page * page_number - results_per_page
            results = MLflowService.client.search_registered_models(f"name ilike '%{model_name}%'")

            return Result(
                Result.SUCCESS,
                'Searched models successfully',
                results
            )
        except Exception as e:
            print(f'[EXCEPTION] An error occurred while searching models with name like {model_name}. Error {e}')
            return Result(
                Result.FAIL,
                'An error occurred while searching models',
                Result.EXCEPTION
            )

    @staticmethod
    def get_latest_model_version(name: str) -> Result:
        ''' Get the latest model version

        :param name: name of the model

        :return: a ModelVersion object that is the latest version of a registered model
                 None if model with name is not found or on exception
        '''
        try:
            result = session.query(ModelVersion) \
                .filter(ModelVersion.name.like(name)) \
                .order_by(ModelVersion.version.desc()) \
                .limit(1) \
                .first()

            if result is None:
                return Result(
                    Result.FAIL,
                    f'No version was found for {name}',
                    Result.NOT_FOUND
                )

            return Result(
                Result.SUCCESS,
                f'Found version {result.version} of {name}',
                result
            )
        except Exception as e:
            print(f'[EXCEPTION] An error occurred while searching for model version of {name}. Exception: {e}')
            return Result(
                Result.FAIL,
                f'An error occurred while searching for model version of {name}',
                Result.EXCEPTION
            )

    @staticmethod
    def get_user_models(username: str) -> Result:
        ''' Get models by username

        :param username: username to find models of

        :return: List of ModelVersion objects of user
        '''
        try:
            user_models = []

            model_list = session.query(RegisteredModelTag) \
                .filter(RegisteredModelTag.key == "user_id", RegisteredModelTag.value == username) \
                .all()

            for model in model_list:
                user_models.append(MLflowService.client.get_registered_model(model.name))

            return Result(
                Result.SUCCESS,
                f'Collected models of {username}',
                user_models
            )
        except Exception as e:
            print(f'[EXCEPTION] An error occurred while collecting models of {username}. Exception {e}')
            return Result(
                Result.FAIL,
                f'An error occurred while collecting models of {username}',
                Result.EXCEPTION
            )

    @staticmethod
    def transition_model_version_stage(username: str, model_name: str, version: int, stage: str) -> Result:
        try:
            assert MLflowService._is_valid_stage(stage), 'Wrong model stage.'

            model = MLflowService.get_model_version(model_name=model_name, version=version)
            if model.data.user_id == username:
                MLflowService.client.transition_model_version_stage(name=model_name,
                                                                    version=str(version),
                                                                    stage=stage)
            return Result(Result.SUCCESS,
                          f"Successfully transitioned model with name '{model_name}' and version {version} to '{stage}",
                          None)

        except Exception as e:
            return Result(Result,
                          f"Failed to transition model with name '{model_name}' and version {version} to '{stage}",
                          Result.EXCEPTION)

    @staticmethod
    def delete_model_version(username: str, model_name: str, version: int) -> Result:
        ''' Delete a specific model version

        :param username: Username of user that's trying to delete model version
        :param model_name: the name of the model to delete
        :param version: the version to delete
        
        :return True e success, otherwise False
        '''
        try:

            # Get model version
            model = MLflowService.get_model_version(model_name=model_name, version=version)

            if model.is_fail():
                return model
            elif model.data.user_id != username:
                return Result(
                    Result.FAIL,
                    f"{username} doesn't have authorization to delete version {version} of {model_name}",
                    Result.UNAUTHORIZED
                )

            # Delete registered model. Backend raises exception if a registered model with given name does not exist
            MLflowService.client.delete_model_version(name=model_name, version=str(version))

            return Result(
                Result.SUCCESS,
                'Deleted model version successfully'
            )
        except Exception as e:
            print(f'[EXCEPTION]Failed to delete version {version} of {model_name}. Exception {e}.')
            return Result(
                Result.FAIL,
                f'Failed to delete version {version} of {model_name}',
                Result.EXCEPTION
            )

    @staticmethod
    def delete_model(username: str, model_name: str) -> Result:
        ''' Delete all model versions of specified model

        :param model_name: the name of the model to delete all versions
        
        :return True e success, otherwise False
        '''
        try:
            # Delete registered model. Backend raises exception if a registered model with given name does not exist
            registered_model = MLflowService.client.get_registered_model(model_name)
            # Verify model ownership
            if registered_model.tags["user_id"] == username:
                MLflowService.client.delete_registered_model(name=model_name)

            return Result(
                Result.SUCCESS,
                f'Deleted model {model_name}'
            )
        except Exception as e:
            return Result(
                Result.FAIL,
                f'An error occurred while deleting model {model_name}',
                Result.EXCEPTION
            )

    @staticmethod
    def update_model_description(username: str,
                                 model_name: str,
                                 description: str) -> Result:
        ''' Update registered model, or model version

        :param username: the user's username; refers to a model's user_id
        :param model_name: Model name to update
        :param description: Model description to update

        :return None if model was not found, else return updated model
        '''

        try:

            registered_model = MLflowService.client.get_registered_model(model_name)
            # Verify model ownership
            if registered_model.tags["user_id"] == username:
                MLflowService.client.update_registered_model(model_name, description)
            else:
                return Result(
                    Result.FAIL,
                    f"Failed to update model description. User '{username}' does not have authorization to edit model '{model_name}'",
                    Result.UNAUTHORIZED
                )

            return Result(
                Result.SUCCESS,
                'Updated model description successfully',
                None
            )

        except Exception as e:
            return Result(
                Result.FAIL,
                f"Error while trying to update description of model '{model_name}'",
                Result.NOT_FOUND
            )

    @staticmethod
    def get_model_signature(name: str, version: str, model_version_obj=None) -> Result:
        ''' Get model version signature

        :param name: model name
        :param version: the model version

        :return:  a Result object
                  on success  data is a python dict with format:
                    {
                     'inputs': <List[Dict[str, str]]>, # array json objects with columns input format
                     'outputs': <List[Dict[str, str]]> # array json objects with columns input format
                     }

        Example:
            {
             'inputs': 
                '[
                    {"name": "fixed acidity", "type": "long"},
                    {"name": "volatile acidity", "type": "double"},
                    {"name": "citric acid", "type": "double"},
                    {"name": "residual sugar", "type": "double"},
                    {"name": "chlorides", "type": "double"},
                    {"name": "free sulfur dioxide", "type": "long"},
                    {"name": "total sulfur dioxide", "type": "long"},
                    {"name": "density", "type": "double"},
                    {"name": "pH", "type": "long"},
                    {"name": "sulphates", "type": "double"},
                    {"name": "alcohol", "type": "double"}
                ]',
            outputs': 
                '[
                    {"type": "double"}
                ]'
            }
        '''
        try:
            if model_version_obj is None:
                model_version = MLflowService.get_model_version(name,int(version))
            else:
                model_version = Result(Result.SUCCESS,
                                       f"Using model version cached instance.",
                                       model_version_obj)

            # artifacts_ls = MLflowService.__client.list_artifacts(registered_model_version.run_id, name)

            if model_version.is_fail():
                return model_version

            shipped_brain_yaml_file = MLflowService.client.download_artifacts(model_version.data.run_id,
                                                                              "shipped-brain.yaml")
            with open(shipped_brain_yaml_file, "r") as yaml_file:
                shipped_brain_yaml = yaml.full_load(yaml_file)
                model_artifacts_path = shipped_brain_yaml["model_artifacts_path"]

            ml_model_path = MLflowService.client.download_artifacts(model_version.data.run_id,
                                                                    f"{model_artifacts_path}/MLmodel")
            cfg = None

            # TODO read from s3: implement store service
            with open(ml_model_path, 'r') as f:
                cfg = yaml.full_load(f)

            return Result(
                Result.SUCCESS,
                'Collected model signature successfully',
                cfg['signature']
            )
        except Exception as e:
            print(f'[EXCEPTION] Failed to collect model signature for model ({name}, {version}). Exception: {e}')
            return Result(
                Result.FAIL,
                'Failed to collect model signature',
                Result.EXCEPTION
            )

    @staticmethod
    def get_input_example(name: str, version: str, model_version_obj=None) -> Result:
        ''' Get model version input example

        :param name: model name
        :param version: the model version

        :return:  a Result object
                  on success Result.status is success data is a python dict with format json split=orient
                  otherwise Result.status is fail and Result.data is None
        '''
        try:
            if model_version_obj is None:
                model_version = MLflowService.get_model_version(name, int(version))
            else:
                model_version = Result(Result.SUCCESS,
                                       f"Using model version cached instance.",
                                       model_version_obj)

            print("MODEL VERSION.is_fail:", model_version.is_fail())

            if model_version.is_fail():
                return model_version

            print("MODEL VERSION DATA:", model_version.data.run_id)

            shipped_brain_yaml_file = MLflowService.client.download_artifacts(model_version.data.run_id,
                                                                              "shipped-brain.yaml")
            with open(shipped_brain_yaml_file, "r") as yaml_file:
                shipped_brain_yaml = yaml.full_load(yaml_file)
                model_artifacts_path = shipped_brain_yaml["model_artifacts_path"]

            input_example_path = MLflowService.client.download_artifacts(model_version.data.run_id,
                                                                         f"{model_artifacts_path}/input_example.json")

            with open(input_example_path, 'r') as f:
                input_example = json.load(f)

            return Result(
                Result.SUCCESS,
                'Collected model input example successfully',
                input_example
            )
        except Exception as e:
            print(f'[EXCEPTION] Failed to collect model input example for model ({name}, {version}). Exception: {e}')
            return Result(
                Result.FAIL,
                'Failed to collect model input example',
                Result.EXCEPTION
            )

    @staticmethod
    def get_conda_env_path(name: str, version: str) -> Result:
        ''' Get model version conda environment path

        :param name: model name
        :param version: the model version

        :return: Result object: data attr. is conda env. path on success; None otherwise
        '''
        try:
            model_version = MLflowService.get_model_version(name, int(version))

            if not model_version.is_success():
                return model_version

            # artifacts_ls = MLflowService.__client.list_artifacts(registered_model_version.run_id, name)
            shipped_brain_yaml_file = MLflowService.client.download_artifacts(model_version.data.run_id,
                                                                              "shipped-brain.yaml")
            with open(shipped_brain_yaml_file, "r") as yaml_file:
                shipped_brain_yaml = yaml.full_load(yaml_file)
                model_artifacts_path = shipped_brain_yaml["model_artifacts_path"]
                model_flavor = shipped_brain_yaml["flavor"]

            print("[DEBUG] Model artifacts path:", model_artifacts_path)

            ml_model_path = MLflowService.client.download_artifacts(model_version.data.run_id,
                                                                    f"{model_artifacts_path}/MLmodel")
            cfg = None

            print(f'[DEBUG] MLflowService.get_conda_env_path, {ml_model_path}')
            # TODO read from s3: implement store service
            with open(ml_model_path, 'r') as f:
                cfg = yaml.full_load(f)

            print(f"[DEBUG] MLflowService.get_conda_env_path :: cfg['flavors'] object in MLmodel: {cfg['flavors']}")

            remote_conda_env_path = model_artifacts_path + "/" + cfg['flavors']["python_function"]['env']
            print("[INFO] Downloading conda env from", remote_conda_env_path)
            conda_env_path = MLflowService.client.download_artifacts(model_version.data.run_id, remote_conda_env_path)

            return Result(
                Result.SUCCESS,
                'Collected model conda env. path successfully',
                conda_env_path
            )
        except Exception as e:
            print(f'[EXCEPTION] Failed to collect conda env. path for model ({name}, {version}). Exception: {e}')

            return Result(
                Result.FAIL,
                f'Failed to collect conda env. path for model ({name}, {version})',
                Result.EXCEPTION
            )

    @staticmethod
    def get_owner(model_name: str):
        try:
            registered_model = MLflowService.client.get_registered_model(model_name)

            return Result(Result.SUCCESS,
                          f"Collect owner for model '{model_name}' successfully.",
                          registered_model.tags["user_id"])
        except:
            return Result(Result.FAIL,
                          f"Failed get owner for model with name {model_name}.",
                          Result.EXCEPTION)

    @staticmethod
    def create_registered_model(user_id: str, model_name: str, description: Optional[str] = None):
        """ Create RegisteredModel - does not require logged model
        """
        from shippedbrain import shippedbrain

        if not shippedbrain._validate_model_name(model_name):
            return Result(
                Result.FAIL,
                f"Failed to create model with '{model_name}'. Name is not valid.",
                Result.EXCEPTION
            )

        try:
            registered_model = MLflowService.client.create_registered_model(name=model_name,
                                                                            description=description,
                                                                            tags={"user_id": user_id})
            return Result(
                Result.SUCCESS,
                f"Successfully created model '{model_name}' for user '{user_id}'.",
                registered_model
            )
        except Exception as e:
            print(f"[EXCEPTION] Failed to create model {model_name}. Error {e}")
            return Result(
                Result.FAIL,
                f"Failed to create model {model_name}.",
                Result.EXCEPTION
            )

    @staticmethod
    def get_or_create_registered_model(user_id: str, model_name: str):
        """ Get or create RegisteredModel - does not require logged model
        """
        from shippedbrain import shippedbrain

        if not shippedbrain._validate_model_name(model_name):
            return Result(
                Result.FAIL,
                f"Failed to create model with '{model_name}'. Name is not valid.",
                Result.EXCEPTION
            )

        try:
            registered_model = MLflowService.client.get_registered_model(model_name)
            return Result(
                Result.SUCCESS,
                f"Collected model '{model_name}' successfully.",
                registered_model
            )
        # RESOURCE_DOES_NOT_EXIST
        except:
            return MLflowService.create_registered_model(user_id, model_name)

    @staticmethod
    def set_tag(username: str, model_name: str, key: str, value: Union[Dict[str, Any], str]):
        failed_result = Result(Result.FAIL,
                               f"Failed to set {key} for model with name '{model_name}'.",
                               Result.EXCEPTION)
        try:
            owner_result = MLflowService.get_owner(model_name)

            value_str = json.dumps(value) if isinstance(value, dict) else value

            if owner_result.is_success() and username == owner_result.data:
                MLflowService.client.set_registered_model_tag(model_name, key, value_str)
            else:
                return failed_result

            return Result(Result.SUCCESS,
                          f"Successfully set {key} for model with name '{model_name}.")
        except Exception as e:
            print(f"[EXCEPTION] Failed to set tag '{key}' for model with name '{model_name}'. Error: {e}")
            return failed_result

    @staticmethod
    def delete_tag(username: str, model_name: str, key: str):
        failed_result = Result(Result.FAIL,
                               f"Failed to delete {key} for model with name '{model_name}'.",
                               Result.EXCEPTION)
        try:
            owner_result = MLflowService.get_owner(model_name)

            if owner_result.is_success() and username == owner_result.data:
                MLflowService.client.delete_registered_model_tag(model_name, key)
            else:
                return failed_result

            return Result(Result.SUCCESS,
                          f"Successfully deleted {key} for model with name '{model_name}.")
        except Exception as e:
            print(f"[EXCEPTION] Failed to delete tag '{key}' for model with name '{model_name}'. Error: {e}")
            return failed_result

    @staticmethod
    def set_metrics(username: str, model_name: str, metrics: Dict[str, Any]):
        metrics_str = json.dumps(metrics)
        return MLflowService.set_tag(username, model_name, MLflowService.METRICS_TAG, metrics_str)

    @staticmethod
    def set_params(username: str, model_name: str, params: Dict[str, Any]):
        params_str = json.dumps(params)
        return MLflowService.set_tag(username, model_name, MLflowService.PARAMS_TAG, params_str)

    @staticmethod
    def set_github_repo(username: str, model_name: str, url: str):
        if not Validation.is_github_repo_valid(url=url):
            return Result(
                Result.FAIL,
                'GitHub repository URL is invalid. URL should look something like: github.com/github_username/github_project',
                Result.NOT_ACCEPTABLE
            )

        return MLflowService.set_tag(username, model_name, MLflowService.GITHUB_REPO_TAG, url)

    @staticmethod
    def set_input_example(username: str, model_name: str, input_example: Dict[str, Any]):
        return MLflowService.set_tag(username, model_name, MLflowService.INPUT_EXAMPLE_TAG, input_example)

    @staticmethod
    def set_signature(username: str, model_name: str, signature: Dict[str, Any]):
        return MLflowService.set_tag(username, model_name, MLflowService.SIGNATURE_TAG, signature)

    @staticmethod
    def delete_metrics(username: str, model_name: str):
        return MLflowService.delete_tag(username, model_name, MLflowService.METRICS_TAG)

    @staticmethod
    def delete_params(username: str, model_name: str):
        return MLflowService.delete_tag(username, model_name, MLflowService.PARAMS_TAG)

    @staticmethod
    def delete_github_repo(username: str, model_name: str):
        return MLflowService.delete_tag(username, model_name, MLflowService.GITHUB_REPO_TAG)

    @staticmethod
    def delete_input_example(username: str, model_name: str):
        return MLflowService.delete_tag(username, model_name, MLflowService.INPUT_EXAMPLE_TAG)

    @staticmethod
    def delete_signature(username: str, model_name: str):
        return MLflowService.delete_tag(username, model_name, MLflowService.SIGNATURE_TAG)

    @staticmethod
    def get_model_version_from_registered_model_obj(model, version: int = 0):
        get_latest_version = True if version == 0 else False
        latest_model = None
        max_version = 0

        print("[DEBUG MODEL]:", model)
        for model_version in model.latest_versions:
            current_version = int(model_version.version)
            if get_latest_version and current_version > max_version:
                max_version = current_version
                latest_model = model_version
            elif not get_latest_version and current_version == version:
                return Result(Result.SUCCESS,
                              f"Successfully fetched model version {version}",
                              model_version)

        if max_version == 0:
            return Result(Result.FAIL,
                          f"Failed to fetch model version {version}",
                          Result.EXCEPTION)
        else:
            return Result(Result.SUCCESS,
                          f"Successfully fetched latest model version {max_version}",
                          latest_model)
