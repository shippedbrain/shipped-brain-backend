import os
import tempfile

import mlflow
import yaml
from db.db_config import session
from models.model_version import ModelVersion
from models.result import Result
from services.hashtag_service import HashtagService
from services.mlflow_service import MLflowService
from shippedbrain import shippedbrain


class ModelRegistryService:

    @staticmethod
    def update_model_owner(user_id: str, model: ModelVersion = None, run_id: str = None) -> None:

        if not model:
            model = session.query(ModelVersion).filter_by(run_id=run_id).first()

        model.user_id = user_id
        session.commit()

    @staticmethod
    def inherit_model_hashtags(model_name: str) -> None:
        """Inherit model's previous version tags

        :param model_name: the model's name
        """
        previous_model_hashtags_data = HashtagService.get_model_hashtags(model_name=model_name)
        if previous_model_hashtags_data.is_success():
            for hashtag in previous_model_hashtags_data.data:
                key = hashtag['key']
                value = hashtag['value']
                print(f'[INFO] Inheriting hashtag ({key}, {value}')
                _ = HashtagService.add_model_hashtag(model_name=model_name,
                                                     value=value,
                                                     key=key)
        else:
            print(f'[INFO] Failed to inherit or create model hashtags for {model_name}')

    @staticmethod
    def register_model(zipfile: str, username: str) -> Result:
        """ Return Result object with data=ModelVersion on success, raise exception otherwise
        """
        # set on function's start
        mlflow.set_experiment(username)
        experiment = mlflow.get_experiment_by_name(username)
        print(f"[DEBUG] Experiment id: {experiment.experiment_id}")
        print(f"[DEBUG] Experiment lifecycle stage: {experiment.lifecycle_stage}")

        with tempfile.TemporaryDirectory() as tmpdir_target:
            shippedbrain._unzip_artifacts(zipfile, tmpdir_target)

            # read shipped-brain.yaml
            print("[INFO] Reading shipped-brain.yaml")
            with open(os.path.join(tmpdir_target, "shipped-brain.yaml"), "r") as yaml_file:
                shippedbrain_yaml = yaml.full_load(yaml_file)
                model_artifacts_path = shippedbrain_yaml["model_artifacts_path"]
                model_name = shippedbrain_yaml["model_name"]
                model_metrics = shippedbrain_yaml["metrics"]
                model_params = shippedbrain_yaml["params"]
                valid_model_name = shippedbrain._validate_model_name(model_name)

                print("[INFO] shippedbrain.yaml", shippedbrain_yaml)
                print("[INFO] shippedbrain.yaml-metrics", shippedbrain_yaml.get("metrics"))

                if not valid_model_name:
                    print(f"[WARN] Invalid model name '{model_name}")
                    return Result(Result.FAIL,
                                  f"Model name '{model_name}' is not valid!",
                                  Result.EXCEPTION)

                registered_model_result = MLflowService.get_or_create_registered_model(username, model_name)
                if registered_model_result.is_fail():
                    print(f"[FAIL] Failed to get or create model '{model_name}' for user {username}.")
                    return Result(Result.FAIL,
                                  f"An unexpected error occurred. Could not log model with name '{model_name}'.",
                                  Result.EXCEPTION)

                elif registered_model_result.data.tags["user_id"] != username:
                    print(f"[FAIL] Failed create model '{model_name}'. Permission denied.")
                    return Result(Result.FAIL,
                                  f"Failed create model '{model_name}'. Permission denied.",
                                  Result.EXCEPTION)

                print("[DEBUG]\tMODEL NAME:", model_name)
                print("[DEBUG]\tMODEL NAME IS VALID:", valid_model_name)
                print("[DEBUG]\tMODEL ARTIFACTS PATH:", model_artifacts_path)
                print("[DEBUG]\tMODEL FLAVOR:", shippedbrain_yaml["flavor"])

                # final_model_name = f"{username}/{model_name}"
                logged_model_run = shippedbrain._log_model(tmpdir_target, model_artifacts_path)

                model_version = mlflow.register_model(
                    f"runs:/{logged_model_run.info.run_id}/{model_artifacts_path}",
                    model_name)
                MLflowService.set_params(username=username, model_name=model_name, params=model_params)
                MLflowService.set_metrics(username=username, model_name=model_name, metrics=model_metrics)
                return Result(Result.SUCCESS,
                              f"Successfully registered model ({model_version.name, model_version.version}).",
                              model_version)
