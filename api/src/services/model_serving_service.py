from typing import Optional, Tuple, List, Dict
import subprocess
import tempfile
import os
import pandas as pd
from dotenv import load_dotenv
from services.mlflow_service import MLflowService
from mlflow.utils import conda
from models.result import Result
from datetime import datetime
from config.config import MODEL_SERVING_SERVICE_CONFIG
import signal

# This is needed; set mlflow tracking uri to MLFLOW_TRACKING_URI
load_dotenv()

class ModelServingService:
    

    def __init__(self):
        self.MIN_PORT: int = MODEL_SERVING_SERVICE_CONFIG['min_port']
        self.MAX_PORT: int = MODEL_SERVING_SERVICE_CONFIG['max_port']
        self.TTL: int = MODEL_SERVING_SERVICE_CONFIG['ttl']
        self.MAX_MODELS: int = MODEL_SERVING_SERVICE_CONFIG['max_concurrent_models']
        self.OPEN_PORTS: List[int] = [x for x in range(MODEL_SERVING_SERVICE_CONFIG['min_port'], MODEL_SERVING_SERVICE_CONFIG['max_port'] + 1)]
        self.MODELS: Dict[Tuple[str, int], Tuple[int, subprocess.Popen, datetime]] = {}  # (model, version): [port, pid, datetime]
        self.MAX_RETRIES = MODEL_SERVING_SERVICE_CONFIG['max_retries']

    @staticmethod
    async def __has_conda_env(name: str, version: str) -> Tuple[bool, str]:
        ''' Check if model version has conda environment

        :param name: model name
        :param version: model version

        :return: True if env. exists; False otherwise
        '''
        result = MLflowService.get_conda_env_path(name, version)

        print(f"[DEBUG] PredictionService.__has_conda_env - MLflowService.get_conda_env_path: {result.to_dict()}")

        conda_env_path = result.to_dict()['data']['results']

        project_env_name = conda._get_conda_env_name(conda_env_path, None)

        print(f'[DEBUG] PredictionService.__has_conda_env - project_env_name={project_env_name}')

        conda_path = os.environ.get('MLFLOW_CONDA_HOME')
        conda_envs_path = os.path.join(conda_path, 'envs')
        conda_env_list = os.listdir(conda_envs_path)

        print(f"[DEBUG] PredictionService.__has_conda_env - conda envs list: {conda_env_list}")
        return project_env_name in conda_env_list, conda_env_path

    @staticmethod
    async def predict(name: str,
                      version: int,
                      input_features: str,
                      no_conda: bool=False,
                      base_uri: str='models') -> Result:
        ''' Make prediction from data using a queried model and version.

        :param name: name of the registered model
        :param version: version of the model
        :param input_features: json string data in 'split' format model compatible
        :param no_conda: (optional) [default False] use conda environment if False; otherwise True
        :param prepare_env: (optional) [default False] prepare conda environment if True; otherwise False. Should be True on for first prediction
        :param base_uri: (option) base model uri to use: 'runs' or 'models'. If 'runs' is used then [[name]] is the [run_id] and [[version]] the [model name]

        :return: prediction of type [numpy.ndarray | pandas.(Series | DataFrame)] on success; None otherwise 
        '''
        try:
            print("[INFO] PredictionService.predict - Offline Prediction Service")
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv') as f:
                file_abs = os.path.abspath(f.name)
                cmd = ['mlflow', 'models', 'predict', '-m', f'{base_uri}:/{name}/{version}', '-i', file_abs, '-t', 'csv'] # -o <output_file>
                prepare_env_cmd = ['mlflow', 'models', 'prepare-env', '--model-uri', f'{base_uri}:/{name}/{version}']
                
                # Check conda env
                has_conda_env, project_env_name = await ModelServingService.__has_conda_env(name, str(version))

                if no_conda:
                    cmd.append('--no-conda')
                
                df = pd.read_json(input_features, orient='split')
                df.to_csv(file_abs)

                # Install conda environment on first prediction.
                # If env. is not prepared, first prediction fails!
                conda.get_or_create_conda_env(project_env_name)

                '''if not has_conda_env:
                    print(f"\t[INFO] Preparing env. for '{name}' with version '{version}'...")
                    prepare_env_result = subprocess.run(prepare_env_cmd, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if prepare_env_result.returncode != 0:
                        print(f"\t[WARN] Failed to prepare env. for '{name}' with version '{version}'")
                        return Result(Result.FAIL,
                                      f"Failed to prepare env for model ({name}, {version})",
                                      Result.EXCEPTION)
                else:
                    print('\t PredictionService.predict env. exists')'''

                process = subprocess.run(cmd, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                f.close()

                print("\t[DEBUG] STDERR/INFO:", process.stderr)
                print("\t[DEBUG] STDOUT:", process.stdout)
                print("\t[DEBUG] RETURN CODE:", process.returncode)
                
                if process.returncode != 0:
                    print("[WARN] Process returned code != 0")
                    return Result(Result.FAIL,
                                  f"Failed to perform prediction using model ({name}, {version})",
                                  Result.FAIL)

                out = eval(process.stdout)

                print('[INFO] PredictionService.predict - success')
                return Result(Result.SUCCESS,
                              'Prediction success',
                              out)

        except Exception as e:
            print(f"\t[EXCEPTION] Could not make prediction using model with name '{name}' and version '{version}'. Error: '{e}'")
            return Result(Result.FAIL,
                          f"[EXCEPTION] Could not make prediction using model with name '{name}' and version '{version}'.",
                          Result.EXCEPTION)

    async def serve(self,
                    name: str,
                    version: int,
                    no_conda: bool=False,
                    base_uri: str='models') -> Result:
        ''' Serve model as REST endpoint

        :param name: name of the registered model
        :param version: version of the model
        :param no_conda: (optional) [default False] use conda environment if False; otherwise True
        :param prepare_env: (optional) [default False] prepare conda environment if True; otherwise False. Should be True on for first prediction
        :param base_uri: (option) base model uri to use: 'runs' or 'models'. If 'runs' is used then [[name]] is the [run_id] and [[version]] the [model name]

        :return: REST endpoint port on success; None otherwise 
        '''
        # TODO verify serving limits; e.g. self.MAX_MODELS
        try:
            print('[INFO] Serve model')
            # Check if model is being served
            if self.MODELS.get((name, version)) is not None:
                print(f'[INFO] Already serving model ({name}, {version})')

                port = self.MODELS.get((name, version))[0]
                process = self.MODELS.get((name, version))[1]
                model_serving_timestamp = datetime.now()
                # Update TTL
                self.MODELS[(name, version)] = (port, process, model_serving_timestamp)
                return Result(Result.SUCCESS,
                              f"Serving {(name, version)}: ({port}, {process.pid}, {model_serving_timestamp})",
                              {'port': port})
            
            port = self.OPEN_PORTS[0]
            
            cmd = ['mlflow', 'models', 'serve', '-m', f'{base_uri}:/{name}/{version}', '-p', str(port)]
            prepare_env_cmd = ['mlflow', 'models', 'prepare-env', '--model-uri', f'{base_uri}:/{name}/{version}']
                
            # Check conda env
            has_conda_env, project_env_name = await ModelServingService.__has_conda_env(name, str(version))

            if no_conda:
                cmd.append('--no-conda')
                
            # Install conda environment on first prediction.
            # If env. is not prepared, first prediction fails!
            conda.get_or_create_conda_env(project_env_name)

            process = subprocess.Popen(cmd, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # subprocess is dead
            if process.returncode is not None:
                print("\t[WARN] Process returned code != 0")
                return Result(Result.FAIL,
                              f"Process returned code != 0")

            # update
            model_serving_timestamp = datetime.now()
            self.MODELS[(name, version)] = (port, process, model_serving_timestamp)
            self.OPEN_PORTS = self.OPEN_PORTS[1:]

            print(f"\t[INFO] Started serving {(name, version)}: ({port}, {process.pid}, {model_serving_timestamp})")

            return Result(Result.SUCCESS,
                          f"Serving {(name, version)}: ({port}, {process.pid}, {model_serving_timestamp})",
                          {'port': port})

        except Exception as e:
            print(f"\t[EXCEPTION] Could not start REST endpoint service for model with name '{name}' and version '{version}'. Error: '{e}'")
            return Result(Result.FAIL,
                          f"Could not start REST endpoint service for model with name '{name}' and version '{version}'",
                          Result.EXCEPTION)

    async def kill_model(self,
                         name: str,
                         version: int) -> Result:
        ''' Kill model's REST endpoint

        :param name: name of the registered model
        :param version: version of the model

        :return: True on success; False if not exists; None otherwise 
        '''
        try:
            print(f'[INFO] Kill live model ({name}, {version})')
            model_serving_data = self.MODELS.get((name, version))
            if model_serving_data is None:
                print('\t[WARN] Could not get live model port.')
                return Result(Result.FAIL,
                              'Could not get live model port.',
                              Result.NOT_FOUND)

            port = model_serving_data[0]
            pro = model_serving_data[1]
            model_serving_timestamp = model_serving_data[2]

            # TODO review and verify status code
            #pid.kill()
            # alternative SIGTERM
            os.killpg(os.getpgid(pro.pid), signal.SIGKILL)  # Send the signal to all the process groups

            self.MODELS.pop((name, version)) # delete pid
            self.OPEN_PORTS.append(port) # add port to open ports
            self.OPEN_PORTS = sorted(self.OPEN_PORTS)
            print(f"\t[INFO] Killed live model ({name}, {version}): ({port}, {pro.pid}, {model_serving_timestamp})")
            print("\t[DEBUG] Process status", pro.poll())

            return Result(Result.SUCCESS,
                          f"Killed live model ({name}, {version}): ({port}, {pro.pid})",
                          {'model_name': name,
                           'model_version': version,
                           'port': port,
                           'pid': pro.pid,
                           'timestamp': model_serving_timestamp
                           }
                          )
        except Exception as e:
            print(f"\t[EXCEPTION] Could not kill REST endpoint service for model with name '{name}' and version '{version}'. Error: '{e}'")
            return Result(Result.FAIL,
                          f"Could not kill REST endpoint service for model with name '{name}' and version '{version}'",
                          Result.EXCEPTION)

    def get_port(self,
                 name: str,
                version: int) -> Optional[int]:
        model_serving_data = self.MODELS.get((name, version))

        if model_serving_data is None:
            return False
        
        return model_serving_data[0]

    async def kill(self) -> None:
        ''' Kill live models using configs: max serving time, concurrency, etc
        '''
        datetime_now = datetime.now()
        datetime_now_str = datetime_now.strftime('%Y-%m-%d %H:%M')
        print(f'[INFO] Kill model service. Time: {datetime_now_str}')
        for k in self.MODELS:
            time_delta = datetime_now - self.MODELS[k][2]
            print(f'[DEBUG] Kill or not {k}? Delta: {time_delta.seconds}; {time_delta.seconds >= self.TTL}')
            if time_delta.seconds >= self.TTL:
                kill_result = await self.kill_model(k[0], int(k[1]))
                print(f'[DEBUG] Kill Result ({k[0]}, {k[1]}): {kill_result.to_dict()}')

    def get_sorted_keys_by_datetime(self) -> List[Tuple[str, int]]:
        ''' Return sorted list of tuples by datetime
        '''
        return sorted(self.MODELS, key=lambda x: self.MODELS[x][2])

    def get_lru(self) -> Optional[Tuple[str, int]]:
        '''Get least recently used model by datetime
        '''
        sorted_keys = self.get_sorted_keys_by_datetime()

        return sorted_keys[-1] if len(sorted_keys) > 0 else None

    async def list_endpoints(self) -> Result:
        '''Used in endpoint
        '''
        try:
            active_endpoints = {}
            for k in self.MODELS:
                # cannot serialize tuple key object
                active_endpoints[k[0]+"_"+str(k[1])] = (self.MODELS[k][0],
                                                        self.MODELS[k][1].pid,
                                                        self.MODELS[k][2])
            return Result(Result.SUCCESS,
                          'Successfully fetched live models endpoints',
                          {'active_endpoints': active_endpoints})
        except Exception as e:
            print(f"[EXCEPTION] Failed to list REST endpoint. Error: '{e}'")
            return Result(Result.FAIL,
                          f"Failed to list REST endpoint.",
                          Result.EXCEPTION)
